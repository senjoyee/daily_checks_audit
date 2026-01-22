
import sys
import os
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path("src").resolve()))

from src.server_http import app
from starlette.middleware.trustedhost import TrustedHostMiddleware

print("Middleware Stack:")
for m in app.user_middleware:
    print(f"- {m.cls.__name__} {m.options}")

# Check if TrustedHostMiddleware is explicitly there
has_trusted = any(m.cls == TrustedHostMiddleware for m in app.user_middleware)
print(f"Has TrustedHostMiddleware: {has_trusted}")
