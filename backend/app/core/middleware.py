import contextvars
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variables for correlation IDs and request IDs
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        corr_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        request_id_var.set(req_id)
        correlation_id_var.set(corr_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Correlation-ID"] = corr_id
        return response
