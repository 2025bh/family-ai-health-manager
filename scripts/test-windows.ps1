$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'

Push-Location $backendDir
try {
    & '.\.venv\Scripts\python.exe' -m pytest tests -q
    if ($LASTEXITCODE -ne 0) { throw '后端自动测试失败' }
} finally {
    Pop-Location
}

Push-Location $frontendDir
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw '前端生产构建失败' }
} finally {
    Pop-Location
}
