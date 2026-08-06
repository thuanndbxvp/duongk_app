"""
IP whitelist middleware — chỉ áp dụng cho /api/admin/**.
Config qua env ADMIN_ALLOWED_IPS (comma-separated CIDR).
Empty = allow all (dev mode).
"""
import ipaddress
import os
from typing import List
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


def _load_allowed_networks() -> List[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse env ADMIN_ALLOWED_IPS thành list network objects."""
    raw = os.environ.get('ADMIN_ALLOWED_IPS', '').strip()
    if not raw:
        return []  # Empty = allow all
    
    networks = []
    for cidr in raw.split(','):
        cidr = cidr.strip()
        if not cidr:
            continue
        try:
            networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            # Log warning nhưng không fail
            import logging
            logging.warning(f'[ip_whitelist] Invalid CIDR: {cidr}')
    
    return networks


def _ip_matches(client_ip: str, networks: List) -> bool:
    """Check client_ip có thuộc 1 trong networks không."""
    if not networks:
        return True  # Empty whitelist = allow all
    
    try:
        ip = ipaddress.ip_address(client_ip)
        return any(ip in net for net in networks)
    except ValueError:
        return False


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware block request từ IP không thuộc ADMIN_ALLOWED_IPS.
    CHỉ áp dụng cho paths bắt đầu /api/admin/.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Chỉ check admin routes
        if not request.url.path.startswith('/api/admin/'):
            return await call_next(request)
        
        # Lấy client IP (FastAPI default — không trust X-Forwarded-For)
        client_ip = request.client.host if request.client else 'unknown'
        
        # Parse whitelist (lazy — re-parse mỗi request hoặc cache 60s)
        networks = _load_allowed_networks()
        
        if not _ip_matches(client_ip, networks):
            return JSONResponse(
                status_code=403,
                content={'detail': f'IP {client_ip} not in admin whitelist'},
            )
        
        return await call_next(request)


def is_ip_allowed(client_ip: str) -> bool:
    """Helper test ngoài middleware."""
    return _ip_matches(client_ip, _load_allowed_networks())