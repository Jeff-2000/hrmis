# audit/models.py
from django.db import models
from django.contrib.contenttypes.models import ContentType
# To delete
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "CREATE"), ("UPDATE", "UPDATE"), ("DELETE", "DELETE"),
        ("LOGIN", "LOGIN"), ("LOGOUT", "LOGOUT"), ("PASSWORD_CHANGE", "PASSWORD_CHANGE"),
        ("RUN_GENERATE", "RUN_GENERATE"), ("RUN_CLOSE", "RUN_CLOSE"), ("RUN_REOPEN", "RUN_REOPEN"),
        ("DOC_DOWNLOAD", "DOC_DOWNLOAD"), ("DOC_STATUS_CHANGE", "DOC_STATUS_CHANGE"),
    ]
    SEVERITY_CHOICES = [("INFO", "INFO"), ("WARN", "WARN"), ("CRITICAL", "CRITICAL")]

    timestamp = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey("authentication.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    impersonator = models.ForeignKey("authentication.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_impersonations")

    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="INFO")

    object_ct = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_pk = models.CharField(max_length=128, null=True, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)

    # JSON payloads
    changes = models.JSONField(default=dict, blank=True)
    m2m_added = models.JSONField(default=list, blank=True)
    m2m_removed = models.JSONField(default=list, blank=True)

    # Request context
    request_id = models.CharField(max_length=64, blank=True)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=255, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.TextField(blank=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)

    # Classification / search helpers
    tags = models.JSONField(default=list, blank=True)
    message = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["action"]),
            models.Index(fields=["object_ct", "object_pk"]),
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["severity", "timestamp"]),
            models.Index(fields=["request_id"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} {self.user} {self.action} {self.object_ct_id}:{self.object_pk}"









