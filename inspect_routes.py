
from mcp.server.fastmcp import FastMCP
import uvicorn

mcp = FastMCP("demo")
app = mcp.streamable_http_app

print(f"Type of app: {type(app)}")
print(f"Dir of app: {dir(app)}")

# Try to run it briefly
try:
    print("Attempting dry run of startup...")
    # Just checking if we can import it successfully implies basic validity
    print("Import successful.")
except Exception as e:
    print(f"Error: {e}")
