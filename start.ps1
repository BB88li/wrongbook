param(
    [int]$Port = 8000
)

# 一键启动：后端同时提供 API 与前端页面（单端口）。
# 用法：双击项目根目录的 启动.bat，或执行
#   powershell -NoProfile -ExecutionPolicy Bypass -File start.ps1
#
# 说明：脚本里的提示文字刻意用英文，因为 Windows PowerShell 5.1 会把
# 无 BOM 的 UTF-8 脚本按系统 ANSI 解码，中文会变成乱码。

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$index = Join-Path $root 'frontend\dist\index.html'

if (-not (Test-Path -LiteralPath $python)) {
    Write-Host 'ERROR: backend\.venv not found.' -ForegroundColor Yellow
    Write-Host 'Fix: cd backend; uv sync' -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path -LiteralPath $index)) {
    Write-Host 'ERROR: frontend has not been built.' -ForegroundColor Yellow
    Write-Host 'Fix: cd frontend; npm install; npm run build' -ForegroundColor Yellow
    exit 1
}

# 取本机局域网 IPv4，排除回环、VirtualBox 虚拟网卡与 169.254 自动地址
$ips = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
    Where-Object { $_.AddressFamily -eq 'InterNetwork' -and -not $_.IsLoopback } |
    ForEach-Object { $_.IPAddressToString } |
    Where-Object { $_ -notlike '192.168.56.*' -and $_ -notlike '169.254.*' }

Write-Host ''
Write-Host '  WrongBook is starting ...' -ForegroundColor Cyan
Write-Host '  On your phone (same Wi-Fi), open:' -ForegroundColor Cyan
foreach ($ip in $ips) {
    Write-Host ("      http://{0}:{1}" -f $ip, $Port) -ForegroundColor Green
}
Write-Host ''
Write-Host '  Phone cannot open it? Check Windows Firewall, see README.' -ForegroundColor DarkGray
Write-Host '  Press Ctrl+C to stop.' -ForegroundColor DarkGray
Write-Host ''

Push-Location $backend
try {
    & $python -m uvicorn app.main:app --host 0.0.0.0 --port $Port
}
finally {
    Pop-Location
}
