import time
import json
import asyncio
import httpx
from typing import Optional, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings

SENSITIVE_KEYS = {
    "password", "hashed_password", "token", "secret", "secret_key",
    "access_key", "pin", "otp", "code", "turnstile_token", "jwt",
    "authorization", "cookie", "set-cookie", "x-api-key"
}

def sanitize_data(data: Any, depth: int = 0) -> Any:
    """Recursively sanitize sensitive fields in dict or list."""
    if depth > 5:
        return data
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if str(k).lower() in SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, (dict, list)):
                sanitized[k] = sanitize_data(v, depth + 1)
            elif isinstance(v, str) and len(v) > 3000:
                sanitized[k] = v[:3000] + "... [TRUNCATED]"
            else:
                sanitized[k] = v
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item, depth + 1) for item in data[:50]]
    elif isinstance(data, str) and len(data) > 3000:
        return data[:3000] + "... [TRUNCATED]"
    return data

async def send_agent_log_to_core(log_data: dict):
    """Kirim log request ke endpoint internal sellercek-core-api di background."""
    core_url = settings.SELLERCEK_CORE_API_URL.rstrip('/')
    target_url = f"{core_url}/api/v1/admin/internal/logs/agent"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.post(target_url, json=log_data)
    except Exception as e:
        print(f"[AgentLogMiddleware] Failed to send log to core API: {e}")

class AgentApiRequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware yang mencatat setiap request HTTP & SSE yang masuk ke sellercek-seller-api
    (https://agent.sellercek.com) dan mengirimkannya ke core backend untuk disimpan ke DB.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        path = request.url.path

        # Lewatkan health check agar tidak membanjiri log
        norm_path = path.lower().rstrip('/')
        if method == "OPTIONS" or norm_path in ("/health", "/api/v1/health"):
            return await call_next(request)

        start_time = time.time()
        client_ip = (
            request.headers.get("cf-connecting-ip")
            or request.headers.get("x-real-ip")
            or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        user_agent = request.headers.get("user-agent", "")[:500]

        # Ekstrak API Key prefix jika ada
        api_key_header = request.headers.get("x-seller-api-key") or ""
        api_key_prefix = None
        if api_key_header.startswith("sk_live_"):
            api_key_prefix = api_key_header[:12] + "..."

        # Tentukan tipe client
        client_type = "REST_API"
        if norm_path.startswith("/mcp"):
            client_type = "MCP_SSE"
        elif "claude" in user_agent.lower():
            client_type = "CLAUDE_AGENT"
        elif "hermes" in user_agent.lower():
            client_type = "HERMES_AGENT"
        elif "n8n" in user_agent.lower():
            client_type = "N8N_WORKFLOW"

        # Baca query params
        query_params = None
        if request.query_params:
            try:
                query_params = sanitize_data(dict(request.query_params))
            except Exception:
                pass

        # Baca request payload
        request_payload = None
        body_bytes = b""
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            content_type = request.headers.get("content-type", "").lower()
            if "multipart/form-data" in content_type:
                request_payload = {"[form_data]": "multipart file upload"}
            elif "application/json" in content_type:
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        raw_json = json.loads(body_bytes.decode("utf-8", errors="replace"))
                        request_payload = sanitize_data(raw_json)
                except Exception:
                    request_payload = {"[raw_data]": body_bytes[:1000].decode("utf-8", errors="replace")}

                async def receive():
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                request._receive = receive

        # Ekstrak safe request headers
        safe_headers = {}
        for h_k, h_v in request.headers.items():
            if h_k.lower() in ("host", "user-agent", "accept", "content-type", "x-seller-api-key"):
                if h_k.lower() == "x-seller-api-key" and h_v:
                    safe_headers[h_k] = h_v[:12] + "..."
                else:
                    safe_headers[h_k] = h_v[:500]

        response_status = "SUCCESS"
        status_code = 500
        error_message = None
        response_data = None
        response = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            if status_code >= 400:
                response_status = "FAILED"
                error_message = f"HTTP {status_code}"
            return response
        except Exception as exc:
            response_status = "ERROR"
            status_code = 500
            error_message = str(exc)
            raise exc
        finally:
            execution_time_ms = round((time.time() - start_time) * 1000, 2)

            log_data = {
                "method": method,
                "path": path,
                "full_url": str(request.url)[:500],
                "status_code": status_code,
                "response_status": response_status,
                "execution_time_ms": execution_time_ms,
                "ip_address": client_ip,
                "user_role": "SELLER_AGENT",
                "api_key_prefix": api_key_prefix,
                "client_type": client_type,
                "user_agent": user_agent,
                "query_params": query_params,
                "request_headers": safe_headers,
                "request_payload": request_payload,
                "response_data": response_data,
                "error_message": error_message
            }

            # Jalankan logging background tanpa memblokir response HTTP
            asyncio.create_task(send_agent_log_to_core(log_data))
