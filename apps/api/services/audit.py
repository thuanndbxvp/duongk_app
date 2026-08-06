"""
Audit log service cho admin actions.
Tự động mask các field nhạy cảm (key/secret/token/password).
"""
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID
from apps.api.dependencies.supabase import get_supabase_admin


_SENSITIVE_KEYS = re.compile(r'(key|token|secret|password|api_key)', re.IGNORECASE)


def _mask_value(obj: Any) -> Any:
    """Deep-copy object, thay thế value của sensitive keys bằng '***'."""
    if isinstance(obj, dict):
        return {
            k: ('***' if _SENSITIVE_KEYS.search(str(k)) else _mask_value(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_mask_value(item) for item in obj]
    return obj


def log_admin_action(
    admin_id: UUID,
    admin_email: str,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """
    Ghi một admin action vào bảng admin_audit_logs.
    
    Args:
        admin_id: UUID của admin thực hiện.
        admin_email: Email admin (denormalized để hiển thị).
        action: Tên action, vd 'user.update', 'credit.adjust'.
        target_type: Loại target, vd 'user', 'credit', 'api_key'.
        target_id: UUID hoặc composite key của target.
        before: Snapshot trước khi thay đổi (sẽ tự mask).
        after: Snapshot sau khi thay đổi (sẽ tự mask).
        ip: IP address (ưu tiên X-Forwarded-For).
        user_agent: User agent string.
        reason: Lý do (bắt buộc cho sensitive actions).
    """
    admin = get_supabase_admin()
    admin.table('admin_audit_logs').insert({
        'admin_id': str(admin_id),
        'admin_email': admin_email,
        'action': action,
        'target_type': target_type,
        'target_id': target_id,
        'before': _mask_value(before) if before else None,
        'after': _mask_value(after) if after else None,
        'ip': ip,
        'user_agent': user_agent,
        'reason': reason,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }).execute()