from .models import AdminAuditLog


def record_admin_action(request, *, action, target_type, target_id=None, details=None):
    return AdminAuditLog.objects.create(
        admin=request.user,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
        ip_address=request.META.get("REMOTE_ADDR"),
    )

