
import sys
from pathlib import Path
from starlette.testclient import TestClient

# Add src to sys.path
sys.path.append(str(Path("src").resolve()))

from src.server_http import app

client = TestClient(app)

print("Sending request with Azure Host header...")
response = client.get("/mcp", headers={"Host": "daily-checks-audit-app.azurewebsites.net"})

print(f"Status Code: {response.status_code}")
print(f"Content: {response.text}")
