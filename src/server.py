import sys
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# --- Setup Paths ---
# Add the existing skills/scripts directory to sys.path so we can import the modules
# Root of the project:
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / ".agent" / "skills" / "daily-checks-audit" / "scripts"

if SCRIPTS_DIR.exists():
    sys.path.append(str(SCRIPTS_DIR))
else:
    print(f"Warning: Scripts directory not found at {SCRIPTS_DIR}", file=sys.stderr)

# --- Import Skill Modules ---
try:
    from audit_checks import DailyChecksAuditor, load_customer_config, detect_customer
    from screenshot_validator import ScreenshotValidator
except ImportError as e:
    print(f"Error importing skill modules: {e}", file=sys.stderr)
    print(f"Current sys.path: {sys.path}", file=sys.stderr)
    # We don't exit here to allow server to start, but tools will fail
    DailyChecksAuditor = None
    ScreenshotValidator = None


# --- Transport Security (Host/Origin validation) ---
def _get_env_list(env_var: str) -> list[str]:
    raw = os.environ.get(env_var, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _build_transport_security() -> TransportSecuritySettings:
    disable = os.environ.get("MCP_DISABLE_DNS_REBINDING", "").lower() in {"1", "true", "yes"}
    allowed_hosts = _get_env_list("MCP_ALLOWED_HOSTS")
    allowed_origins = _get_env_list("MCP_ALLOWED_ORIGINS")

    if disable:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)

    if allowed_hosts or allowed_origins:
        return TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        )

    # Default to disabled to avoid rejecting cloud ingress hosts.
    return TransportSecuritySettings(enable_dns_rebinding_protection=False)


# --- Initialize Server ---
mcp = FastMCP("Daily Checks Audit", transport_security=_build_transport_security())

@mcp.tool()
def audit_daily_checks(excel_path: str) -> str:
    """
    Audit an SAP Daily Monitoring Excel file.
    
    Args:
        excel_path: Absolute path to the Excel file to audit.
        
    Returns:
        Markdown formatted audit report.
    """
    if not DailyChecksAuditor:
        return "Error: Audit modules could not be loaded."
        
    if not os.path.exists(excel_path):
        return f"Error: File found at {excel_path}"

    try:
        # Resolve config
        customer = detect_customer(excel_path)
        script_dir = SCRIPTS_DIR  # Use the resolved scripts dir
        config = None
        
        if customer:
            config = load_customer_config(customer, script_dir)
            
        auditor = DailyChecksAuditor(excel_path, config=config, customer=customer)
        
        if not auditor.load_workbook():
            return "Error: Failed to load Excel workbook. Please check the file format."
            
        auditor.audit_all_sheets()
        return auditor.generate_report()
        
    except Exception as e:
        return f"Error executing audit: {str(e)}"

@mcp.tool()
def validate_screenshots(excel_path: str) -> str:
    """
    Validate embedded screenshots in the Excel file using Vision AI.
    
    Args:
        excel_path: Absolute path to the Excel file.
        
    Returns:
        Text summary of validation issues and stats.
    """
    if not ScreenshotValidator:
        return "Error: Screenshot validator module could not be loaded."
        
    if not os.path.exists(excel_path):
        return f"Error: File not found at {excel_path}"
        
    try:
        validator = ScreenshotValidator(excel_path)
        analyses, issues = validator.run_validation()
        
        report = []
        report.append(f"# Screenshot Validation Report")
        report.append(f"analyzed {len(analyses)} screenshots.")
        
        if not issues:
            report.append("No validation issues found.")
        else:
            report.append(f"Found {len(issues)} issues:")
            for issue in issues:
                report.append(f"- [{issue.severity.upper()}] {issue.sheet}: {issue.message}")
                if issue.reported_value is not None:
                     report.append(f"  - Screenshot shows: {issue.screenshot_value}")
                     report.append(f"  - Reported value: {issue.reported_value}")
        
        return "\n".join(report)

    except Exception as e:
        return f"Error executing screenshot validation: {str(e)}"

if __name__ == "__main__":
    mcp.run()
