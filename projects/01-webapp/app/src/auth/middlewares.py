from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request
from src.auth import security

class UserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:

            user = await security.get_current_user_from_cookie(request)
            request.state.user = user
        except Exception:
            request.state.user = None

        response = await call_next(request)
        return response

def get_current_user_from_request(request: Request):
    """
    Función auxiliar para obtener el usuario del request.state
    Retorna el usuario si está autenticado, None en caso contrario.
    """
    return getattr(request.state, 'user', None)

def require_authenticated_user(request: Request):
    """
    Función auxiliar que requiere que el usuario esté autenticado.
    Lanza una excepción si el usuario no está autenticado.
    """
    user = get_current_user_from_request(request)
    if user is None:
        from src.auth.security import LoginRedirectException
        raise LoginRedirectException()
    return user

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que agrega headers de seguridad a todas las respuestas.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Headers de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Solo agregar HSTS en producción (HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware simple de rate limiting para prevenir ataques de fuerza bruta.
    """
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # En producción usar Redis o una base de datos

    async def dispatch(self, request: Request, call_next):
        import time

        # Obtener IP del cliente
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Limpiar requests antiguos
        self.requests = {
            ip: [(timestamp, path) for timestamp, path in requests
                 if current_time - timestamp < self.window_seconds]
            for ip, requests in self.requests.items()
        }

        # Verificar límite para esta IP
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.max_requests:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={"error": "Too Many Requests", "detail": "Rate limit exceeded"}
                )

        # Agregar esta request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append((current_time, str(request.url.path)))

        return await call_next(request)

class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging de auditoría de acciones importantes.
    """
    async def dispatch(self, request: Request, call_next):
        import time
        import logging

        start_time = time.time()

        # Obtener información del usuario si existe
        user = getattr(request.state, 'user', None)
        user_info = f"user:{user.username}" if user else "anonymous"

        # Identificar acciones sensibles
        sensitive_paths = ["/auth", "/login", "/logout", "/tasks/delete", "/profile"]
        is_sensitive = any(path in str(request.url.path) for path in sensitive_paths)

        response = await call_next(request)

        # Log de acciones sensibles o errores
        if is_sensitive or response.status_code >= 400:
            process_time = time.time() - start_time

            logging.info(
                f"AUDIT: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"User: {user_info} | "
                f"IP: {request.client.host if request.client else 'unknown'} | "
                f"Time: {process_time:.3f}s"
            )

        return response

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware básico de protección CSRF para formularios.
    """
    async def dispatch(self, request: Request, call_next):
        # Solo aplicar a métodos que modifican datos
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Verificar que el request venga del mismo origen
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            host = request.headers.get("host")

            # Permitir requests sin origen (API calls desde aplicaciones)
            if origin or referer:
                if origin and not origin.endswith(f"//{host}"):
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=403,
                        content={"error": "CSRF Protection", "detail": "Invalid origin"}
                    )

                if referer and not referer.startswith(f"http://{host}") and not referer.startswith(f"https://{host}"):
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=403,
                        content={"error": "CSRF Protection", "detail": "Invalid referer"}
                    )

        return await call_next(request)