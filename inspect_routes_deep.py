
from mcp.server.fastmcp import FastMCP
from starlette.routing import Route, Mount
import uvicorn

mcp = FastMCP("demo")
# We call it to get the app
app = mcp.streamable_http_app

# If app is a function/method, call it (if it doesn't require args)
# Uvicorn calls it as a factory, so let's try calling it.
try:
    if callable(app):
        real_app = app()
        print(f"App returned: {type(real_app)}")
        if hasattr(real_app, 'routes'):
            for r in real_app.routes:
                print(f"Route: {r.path} [{type(r)}]")
    else:
        print("App is not callable??")

except Exception as e:
    print(f"Error calling app factory: {e}")
