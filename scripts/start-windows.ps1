$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'

if (-not (Test-Path (Join-Path $backendDir '.venv\Scripts\python.exe'))) {
    python -m venv (Join-Path $backendDir '.venv')
    & (Join-Path $backendDir '.venv\Scripts\python.exe') -m pip install -r (Join-Path $backendDir 'requirements-dev.txt')
}
if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    npm install --prefix $frontendDir
}

# 每次启动先执行增量迁移；Alembic 只升级未执行的版本，不覆盖既有健康资料。
Push-Location $backendDir
try {
    & '.\.venv\Scripts\python.exe' -m alembic upgrade head
}
finally {
    Pop-Location
}

Start-Process powershell -WindowStyle Hidden -WorkingDirectory $backendDir -ArgumentList '-NoProfile', '-Command', '.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000'
Start-Process powershell -WindowStyle Hidden -WorkingDirectory $frontendDir -ArgumentList '-NoProfile', '-Command', 'npm run dev'

Write-Host '家医已启动：'
Write-Host '网页：http://127.0.0.1:5173'
Write-Host '接口文档：http://127.0.0.1:8000/docs'
