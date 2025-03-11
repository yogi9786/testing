from fastapi import Response, Request
from starlette.middleware.base import BaseHTTPMiddleware

class IgnoreFaviconMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/favicon.ico":
            return Response(status_code=204)  
        return await call_next(request)
