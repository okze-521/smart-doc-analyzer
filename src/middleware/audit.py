"""审计中间件 — 记录 API 访问日志"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models.audit import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """记录每个 HTTP 请求到 audit_logs 表"""

    SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed = int((time.time() - start) * 1000)

        path = request.url.path
        if path in self.SKIP_PATHS:
            return response

        try:
            db: Session = SessionLocal()
            log = AuditLog(
                action=request.method.lower(),
                resource_type=path.split("/")[2] if len(path.split("/")) > 2 else "root",
                detail=f"path={path} status={response.status_code} ms={elapsed}",
                ip_address=request.client.host if request.client else None,
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception:
            pass

        return response
