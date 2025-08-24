# views_pages.py (or wherever you collect your page views)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def documents_page(request):
    is_elevated = (getattr(request.user, 'role', '') or '').upper() in ('HR', 'ADMIN')
    return render(request, 'documents/list.html', {
        'is_elevated': is_elevated,
    })

# (optional) employee-only page (if you want a separate URL)
@login_required
def documents_my_page(request):
    return render(request, 'documents/my_document.html', {
        'is_elevated': False,
    })
