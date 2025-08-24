
# analytics/services.py
from collections import defaultdict
from calendar import monthrange
from datetime import date, datetime, timedelta
from django.db.models import Sum, Count, Q, F
from django.utils import timezone

from employee.models import Employee
from leave.models import LeaveRequest
from payroll.models import Payslip, PayrollRun, PayslipItem, Contract
from notifications.models import Notification

# --- small helpers ---
def _month_key(dt): return f"{dt.year}-{dt.month:02d}"
def _add_month(d, k=1):
    y = d.year + (d.month + k - 1) // 12
    m = (d.month + k - 1) % 12 + 1
    from calendar import monthrange as mr
    return date(y, m, min(d.day, mr(y, m)[1]))

# --- computations used by API + Celery ---
def compute_kpis():
    today = timezone.localdate()
    active_headcount = Contract.objects.filter(
        start_date__lte=today
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))\
     .values("employee_id").distinct().count()
    if active_headcount == 0:
        active_headcount = Employee.objects.filter(status__iexact="actif").count()

    twelve_months_ago = today - timedelta(days=365)
    exits = Contract.objects.filter(
        end_date__gte=twelve_months_ago, end_date__lt=today
    ).values("employee_id").distinct().count()

    run = PayrollRun.objects.order_by("-year", "-month").first()
    payroll_net = 0
    if run:
        payroll_net = Payslip.objects.filter(run=run).aggregate(s=Sum("net_pay"))["s"] or 0

    since = timezone.now() - timedelta(days=30)
    notif_qs = Notification.objects.filter(timestamp__gte=since)
    sent = notif_qs.exclude(status__in=["failed"]).count()
    read = notif_qs.filter(is_read=True).count()
    read_rate = (read / sent * 100.0) if sent else 0.0

    return {
        "headcount": active_headcount,
        "turnover_12m": exits,
        "payroll_latest_total": float(payroll_net),
        "leave_pending": LeaveRequest.objects.filter(status="pending").count(),
        "read_rate_30d": round(read_rate, 1),
    }

def compute_headcount_series(months_back=18):
    today = timezone.localdate()
    start = _add_month(date(today.year, today.month, 1), -months_back)
    end = date(today.year, today.month, 1)
    series = []
    cur = start
    while cur <= end:
        month_end = date(cur.year, cur.month, monthrange(cur.year, cur.month)[1])
        c = Contract.objects.filter(start_date__lte=month_end)\
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=date(cur.year, cur.month, 1)))\
            .values("employee_id").distinct().count()
        if c == 0:
            c = Employee.objects.filter(date_joined__lte=month_end, status__iexact="actif").count()
        series.append({"month": _month_key(cur), "value": c})
        cur = _add_month(cur, 1)

    # naive forecast 6m
    values = [x["value"] for x in series]
    fc = []
    last = end
    for _ in range(6):
        f = sum(values[-3:])/3.0 if len(values) >= 3 else sum(values)/len(values)
        last = _add_month(last, 1)
        values.append(f)
        fc.append({"month": _month_key(last), "value": round(f, 2)})
    return {"history": series, "forecast": fc}

def compute_leave_series(months_back=18):
    today = timezone.localdate()
    start = _add_month(date(today.year, today.month, 1), -months_back)
    end = date(today.year, today.month, 1)
    counts = defaultdict(int)
    for lr in LeaveRequest.objects.filter(start_date__gte=start, start_date__lte=end)\
                                  .values("start_date"):
        k = f"{lr['start_date'].year}-{lr['start_date'].month:02d}"
        counts[k] += 1
    history = [{"month": k, "value": counts[k]} for k in sorted(counts.keys())]
    # naive forecast 6m
    vals = [x["value"] for x in history] or [0]
    fc = []
    last = end
    for _ in range(6):
        f = sum(vals[-3:])/3.0 if len(vals) >= 3 else sum(vals)/len(vals)
        last = _add_month(last, 1)
        vals.append(f)
        fc.append({"month": _month_key(last), "value": round(f, 2)})
    return {"history": history, "forecast": fc}

# def compute_leave_sla():
#     now = timezone.now()
#     pending = LeaveRequest.objects.filter(status="pending").values("requested_at")
#     aging = [(now - x["requested_at"]).days for x in pending]
#     buckets = {"0-2":0, "3-5":0, "6-10":0, "11-20":0, "21+":0}
#     for d in aging:
#         if d <= 2: buckets["0-2"] += 1
#         elif d <= 5: buckets["3-5"] += 1
#         elif d <= 10: buckets["6-10"] += 1
#         elif d <= 20: buckets["11-20"] += 1
#         else: buckets["21+"] += 1
#     status_counts = dict(LeaveRequest.objects.values_list("status").annotate(n=Count("id")))
#     med = sorted(aging)[len(aging)//2] if aging else 0
#     return {"pending_age_buckets": buckets, "status_counts": status_counts, "pending_median_age": med}

# analytics/services.py  (only diffs shown)

def compute_leave_sla():
    now = timezone.now()
    pending = LeaveRequest.objects.filter(status="pending").values("requested_at")
    aging = [(now - x["requested_at"]).days for x in pending]
    buckets = {"0-2":0, "3-5":0, "6-10":0, "11-20":0, "21+":0}
    for d in aging:
        if d <= 2: buckets["0-2"] += 1
        elif d <= 5: buckets["3-5"] += 1
        elif d <= 10: buckets["6-10"] += 1
        elif d <= 20: buckets["11-20"] += 1
        else: buckets["21+"] += 1

    # FIX: use values().annotate(...) then values_list with both fields
    qs = LeaveRequest.objects.values("status").annotate(n=Count("id"))
    status_counts = dict(qs.values_list("status", "n"))

    med = sorted(aging)[len(aging)//2] if aging else 0
    return {"pending_age_buckets": buckets, "status_counts": status_counts, "pending_median_age": med}

def compute_payroll_components():
    run = PayrollRun.objects.order_by("-status", "-year", "-month").first()
    if not run:
        return {"run": None, "components": []}
    items = (PayslipItem.objects
             .filter(payslip__run=run)
             .values(code=F("component__code"), name=F("component__name"), kind=F("component__kind"))
             .annotate(total=Sum("amount")).order_by("code"))
    return {
        "run": {"id": run.id, "year": run.year, "month": run.month, "status": run.status},
        "components": [{"code": i["code"], "name": i["name"], "kind": i["kind"], "total": float(i["total"] or 0)} for i in items],
    }

def compute_attrition_top():
    today = timezone.localdate()
    six_months_ago = today - timedelta(days=180)
    emps = Employee.objects.select_related("department", "grade")
    leave_counts = dict(
        LeaveRequest.objects.filter(start_date__gte=six_months_ago)
        .values("employee_id").annotate(n=Count("id")).values_list("employee_id", "n")
    )
    unread_counts = dict(
        Notification.objects.filter(is_read=False)
        .values("user_id").annotate(n=Count("id")).values_list("user_id", "n")
    )
    max_leave = max(leave_counts.values()) if leave_counts else 1
    max_unread = max(unread_counts.values()) if unread_counts else 1

    out = []
    for e in emps:
        dj = e.date_joined or (today - timedelta(days=365))
        tenure_m = max(1, (today.year - dj.year)*12 + today.month - dj.month)
        f_tenure = 1 - min(tenure_m / 120.0, 1.0)
        f_leave = (leave_counts.get(e.id, 0) / max_leave) if max_leave else 0.0
        ucount = unread_counts.get(getattr(e, "user_id", None), 0)
        f_unread = (ucount / max_unread) if max_unread else 0.0
        risk = 0.45*f_tenure + 0.35*f_leave + 0.20*f_unread
        out.append({
            "employee": {
                "id": str(e.id),
                "first_name": e.first_name, "last_name": e.last_name,
                "department": getattr(getattr(e, "department", None), "name", None),
                "grade": getattr(getattr(e, "grade", None), "code", None),
            },
            "score": round(float(risk), 3),
            "features": {"tenure_score": round(f_tenure,3), "leave6m": leave_counts.get(e.id, 0), "unread": ucount},
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return {"top": out[:20], "generated_at": timezone.now().isoformat()}

