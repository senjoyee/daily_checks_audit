
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path("src").resolve()))

def test_imports():
    print("Testing imports...")
    try:
        import server
        print("Successfully imported server module.")
    except Exception as e:
        print(f"FAILED to import server module: {e}")
        return

    # Check tools
    if hasattr(server, 'mcp'):
        print("MCP object found.")
        # FastMCP access to tools might be different, but we check if the functions exist in the module
        if hasattr(server, 'audit_daily_checks'):
             print("audit_daily_checks function found.")
        else:
             print("audit_daily_checks function NOT found.")
        
        if hasattr(server, 'validate_screenshots'):
             print("validate_screenshots function found.")
        else:
             print("validate_screenshots function NOT found.")
             
    else:
        print("MCP object NOT found in server module.")
        
    # Check if the inner logic modules were loaded
    if server.DailyChecksAuditor:
        print("DailyChecksAuditor loaded successfully.")
    else:
        print("DailyChecksAuditor FAILED to load (ImportError in server.py).")

if __name__ == "__main__":
    test_imports()
