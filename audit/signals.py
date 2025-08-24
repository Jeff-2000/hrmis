# # audit/signals.py (for example)
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from audit.models import AuditLog

# @receiver(post_save)
# def log_save(sender, instance, created, **kwargs):
#     # Avoid logging the AuditLog model itself to prevent recursion
#     if sender.__name__ == 'AuditLog':
#         return
#     action = "CREATE" if created else "UPDATE"
#     user = getattr(instance, '_logged_in_user', None)  # assume we attach user to instance in view
#     AuditLog.objects.create(
#         user=user, action=action,
#         object_type=sender.__name__,
#         object_id=str(instance.pk),
#         changes=str(instance.__dict__)
#     )

# @receiver(post_delete)
# def log_delete(sender, instance, **kwargs):
#     if sender.__name__ == 'AuditLog':
#         return
#     user = getattr(instance, '_logged_in_user', None)
#     AuditLog.objects.create(
#         user=user, action="DELETE",
#         object_type=sender.__name__,
#         object_id=str(instance.pk),
#         changes=""
#     )
