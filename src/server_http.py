"""
Streamable HTTP Server for MCP on Azure.
v22: Deep Bypass Strategy (ASGI Native)
Instead of Starlette routes, we handle the /mcp request directly at the ASGI level
to bypass any automatically added TrustedHostMiddleware.
"""

from src.server import mcp
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import PlainTextResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from contextlib import asynccontextmanager

# 1. Initialize FastMCP
_ = mcp.streamable_http_app()

# Health check logic
async def health_response(scope, receive, send):
    response = PlainTextResponse("OK")
    await response(scope, receive, send)

# 2. Manual Lifespan 
@asynccontextmanager
async def lifespan(app):
    print("Lifespan: Starting session manager...")
    async with mcp.session_manager.run():
        print("Lifespan: Session manager started.")
        yield
    print("Lifespan: Session manager stopped.")

# 3. Native ASGI Application to bypass ANY middleware
async def asgi_app(scope, receive, send):
    # Handle Lifespan
    if scope["type"] == "lifespan":
        async with lifespan(None):
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return

    # Routing logic at the base level
    path = scope.get("path", "")
    
    # CASE 1: The MCP endpoint (Bypass everything)
    if path.startswith("/mcp"):
        print(f"ASGI Native: Routing {path} to MCP Session Manager")
        await mcp.session_manager.handle_request(scope, receive, send)
        return

    # CASE 2: The Health check
    if path == "/" or path == "/health":
        await health_response(scope, receive, send)
        return

    # CASE 3: Fallback 404
    response = PlainTextResponse("Not Found", status_code=404)
    await response(scope, receive, send)

# Wrap with ProxyHeaders to ensure IP/Protocol is correct
app = ProxyHeadersMiddleware(asgi_app, trusted_hosts="*")

print("Startup: Native ASGI Application (v22). Middleware Bypassed.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
