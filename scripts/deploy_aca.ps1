param(
    [string]$ResourceGroup = "sap-services-uk",
    [string]$Location = "eastus",
    [string]$ContainerAppEnv = "daily-checks-env",
    [string]$ContainerAppName = "daily-checks-audit",
    [string]$AcrName = "sapservicesuk",
    [string]$ImageName = "daily-checks-audit",
    [string]$ImageTag = "latest",
    [string]$AllowHost = "",              # e.g., daily-checks-audit.grayrock-262d9db9.uksouth.azurecontainerapps.io
    [switch]$DisableDnsRebinding           # sets MCP_DISABLE_DNS_REBINDING=true when provided
)

$ErrorActionPreference = "Stop"
$PersonResponsibleTag = "joyee.sen@softwareone.com"

# Resolve registry login server
$Registry = "$AcrName.azurecr.io"
$ImageRef = "${Registry}/${ImageName}:${ImageTag}"

Write-Host "Using image: $ImageRef" -ForegroundColor Cyan

# Ensure ACR exists and fetch credentials
Write-Host "Fetching ACR credentials..." -ForegroundColor Yellow
$acrCred = az acr credential show --name $AcrName --query '{u:username,p:passwords[0].value}' -o json | ConvertFrom-Json
if (-not $acrCred) { throw "Could not fetch ACR credentials for $AcrName" }

# Build & push image
Write-Host "Building image..." -ForegroundColor Yellow
docker build -t $ImageRef .
Write-Host "Pushing image..." -ForegroundColor Yellow
docker push $ImageRef

# Create/update resource group with required tag
Write-Host "Ensuring resource group $ResourceGroup with PersonResponsible tag..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location --tags PersonResponsible=$PersonResponsibleTag | Out-Null
az group update --name $ResourceGroup --set tags.PersonResponsible=$PersonResponsibleTag | Out-Null

# Create Container Apps environment if needed
Write-Host "Ensuring Container Apps environment $ContainerAppEnv..." -ForegroundColor Yellow
az containerapp env create `
  --name $ContainerAppEnv `
  --resource-group $ResourceGroup `
  --location $Location `
  --only-show-errors | Out-Null

# Check if app exists
$appExists = $false
try {
    az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --only-show-errors | Out-Null
    $appExists = $true
} catch {
    $appExists = $false
}

# Base env vars
$envVars = @()
# Add allowlist if provided
if ($AllowHost -ne "") {
    $envVars += "MCP_ALLOWED_HOSTS=$AllowHost"
    $envVars += "MCP_ALLOWED_ORIGINS=https://$AllowHost"
}
# Optional disable flag
if ($DisableDnsRebinding) {
    $envVars += "MCP_DISABLE_DNS_REBINDING=true"
}

# Registry credentials
$regArgs = @(
    "--registry-server", $Registry,
    "--registry-username", $acrCred.u,
    "--registry-password", $acrCred.p
)

if (-not $appExists) {
    Write-Host "Creating Container App $ContainerAppName..." -ForegroundColor Yellow
    az containerapp create `
      --name $ContainerAppName `
      --resource-group $ResourceGroup `
      --environment $ContainerAppEnv `
      --image $ImageRef `
      --ingress external `
      --target-port 8000 `
      @regArgs `
      $(if ($envVars.Count -gt 0) {"--env-vars", ($envVars -join " ")}) `
      --only-show-errors | Out-Null
} else {
    Write-Host "Updating Container App $ContainerAppName..." -ForegroundColor Yellow
    az containerapp update `
      --name $ContainerAppName `
      --resource-group $ResourceGroup `
      --image $ImageRef `
      --ingress external `
      --target-port 8000 `
      @regArgs `
      $(if ($envVars.Count -gt 0) {"--set-env-vars", ($envVars -join " ")}) `
      --only-show-errors | Out-Null
}

# If allowlist was empty, derive FQDN and set env vars
if ($AllowHost -eq "") {
    Write-Host "Deriving app FQDN to set allowlist..." -ForegroundColor Yellow
    $fqdn = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
    if (-not $fqdn) { throw "Could not retrieve container app FQDN" }
    Write-Host "Setting MCP allowlist to $fqdn" -ForegroundColor Yellow
    az containerapp update `
      --name $ContainerAppName `
      --resource-group $ResourceGroup `
      --set-env-vars "MCP_ALLOWED_HOSTS=$fqdn" "MCP_ALLOWED_ORIGINS=https://$fqdn" `
      --only-show-errors | Out-Null
}

# Ensure ingress is configured (CLI compatibility)
Write-Host "Ensuring ingress is set to external:8000..." -ForegroundColor Yellow
az containerapp ingress set `
  --name $ContainerAppName `
  --resource-group $ResourceGroup `
  --type external `
  --target-port 8000 `
  --only-show-errors | Out-Null

Write-Host "Deployment complete." -ForegroundColor Green
Write-Host "Tip: test with   curl -i https://$(az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query 'properties.configuration.ingress.fqdn' -o tsv)/mcp" -ForegroundColor DarkCyan
