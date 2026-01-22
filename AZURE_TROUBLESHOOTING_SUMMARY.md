# Azure Troubleshooting Summary: "Invalid Host header" issue

This document summarizes the steps taken to troubleshoot the persistent `Invalid Host header` error encountered when deploying the Daily Checks Audit MCP server to Azure.

## 1. Problem Description
- **Symptoms**: 
    - Health check route (`/`) works perfectly (returns `200 OK`).
    - MCP endpoint (`/mcp`) consistently returns `Invalid Host header` (HTTP 400).
    - Failure persists across both **Azure Web Apps** and **Azure Container Apps**.
- **Root Cause (Initial Hypothesis)**: Starlette's `TrustedHostMiddleware` rejecting requests from the cloud proxy because the `Host` header doesn't match the internal expectations.

---

## 2. Infrastructure & Versions
Historically, 22 version increments were made across two infrastructure types.

### Phase 1: Azure Web App for Containers (v1 - v20)
- **Architecture**: Dockerized Python app running on Azure App Service.
- **Troubleshooting Steps**:
    - Added `ProxyHeadersMiddleware` to trust `X-Forwarded-*` headers.
    - Added `TrustedHostMiddleware(allowed_hosts=["*"])` to the wrapper.
    - Configured Azure App Settings: `WEBSITES_PORT=8000`, `WEBSITE_ADD_SITENAME_BINDINGS_IN_APPHOST_CONFIG=1`.
- **Finding**: **Local Docker Testing (v20)** passed. Pitting the localhost container directly returned a proper JSON-RPC error, proving the code logic is correct and the issue is Azure-specific.

### Phase 2: Azure Container Apps (v21 - v22)
- **Motivation**: To use a cleaner networking stack and bypass App Service's "magic" header rewriting.
- **Troubleshooting Steps**:
    - **v21 (Deep Patch)**: Manually iterated over the FastMCP sub-app's middleware stack and deleted any `TrustedHostMiddleware` before re-adding it with a wildcard.
    - **v22 (Bare Metal ASGI)**: Abandoned Starlette routing entirely for `/mcp`. Implemented a native ASGI `__call__` function to route paths manually.
- **Finding**: Even the "Bare Metal" implementation (no middleware stack) still returns "Invalid Host header" on Azure.

---

## 3. Current Situation & Status
- **Success Criteria**: The `/mcp` endpoint is technically "up" at the network level but its logic is unreachable due to header rejection.
- **Persistent Failure**: `Invalid Host header` is still being returned for any request to `/mcp`.
- **Top Suspects**:
    1. **Azure Ingress (Envoy)**: The Container App Ingress itself might be returning the 400 error before the request reaches the container.
    2. **Uvicorn Internal Rejection**: Uvicorn might have its own host validation layer (separate from Starlette) that is triggered during proxy header processing.


---
**Last Updated**: 2026-01-21
**Latest URL**: `https://daily-checks-audit.grayrock-262d9db9.uksouth.azurecontainerapps.io/mcp`
