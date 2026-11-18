param(
    [int]$Port = 8000
)

# 一键启动：后端同时提供 API 与前端页面（单端口）。
# 用法：双击项目根目录的 启动.bat，或执行
#   powershell -NoProfile -ExecutionPolicy Bypass -File start.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File start.ps1 -Port 8001
#
# 说明：脚本里的提示文字刻意用英文，因为 Windows PowerShell 5.1 会把
# 无 BOM 的 UTF-8 脚本按系统 ANSI 解码，中文会变成乱码。

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$index = Join-Path $root 'frontend\dist\index.html'
$url = "http://127.0.0.1:$Port"

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

# ---------------------------------------------------------------------------
# 1. 已经在跑？直接告诉用户打开地址，不要傻乎乎再起一个实例
#    （重复启动会因端口被占报 [Errno 10048]，看起来像启动失败）
# ---------------------------------------------------------------------------
$alreadyRunning = $false
try {
    $resp = Invoke-WebRequest -Uri "$url/health" -UseBasicParsing -TimeoutSec 2
    $alreadyRunning = ($resp.StatusCode -eq 200 -and $resp.Content -match 'ok')
} catch {
    $alreadyRunning = $false
}

if ($alreadyRunning) {
    Write-Host ''
    Write-Host '  WrongBook is already running.' -ForegroundColor Green
    Write-Host "  Open it in your browser:  $url" -ForegroundColor Green
    Write-Host ''
    Write-Host '  To restart it: close the OTHER console window first, then run this again.' -ForegroundColor DarkGray
    Write-Host "  If that window is already gone, check:  netstat -ano | findstr :$Port" -ForegroundColor DarkGray
    Write-Host ''
    exit 0
}

# ---------------------------------------------------------------------------
# 2. 端口被别的程序占着？说清楚是哪个 PID，而不是让 uvicorn 抛 WinError
# ---------------------------------------------------------------------------
$listeners = netstat -ano | Select-String ":$Port\s+.*LISTENING"
if ($listeners) {
    Write-Host ''
    Write-Host "  ERROR: port $Port is occupied by another program." -ForegroundColor Yellow
    foreach ($line in $listeners) { Write-Host "  $($line.Line.Trim())" -ForegroundColor DarkGray }
    Write-Host ''
    Write-Host '  Close that program, kill it in Task Manager, or use another port:' -ForegroundColor Yellow
    Write-Host "      powershell -ExecutionPolicy Bypass -File start.ps1 -Port 8001" -ForegroundColor Yellow
    Write-Host ''
    exit 1
}

# ---------------------------------------------------------------------------
# 3. 正常启动
# ---------------------------------------------------------------------------
# 取本机局域网 IPv4，排除回环、VirtualBox 虚拟网卡与 169.254 自动地址
$ips = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
    Where-Object { $_.AddressFamily -eq 'InterNetwork' -and -not $_.IsLoopback } |
    ForEach-Object { $_.IPAddressToString } |
    Where-Object { $_ -notlike '192.168.56.*' -and $_ -notlike '169.254.*' }

Write-Host ''
Write-Host '  WrongBook is starting ...' -ForegroundColor Cyan
Write-Host '  On this PC, open:' -ForegroundColor Cyan
Write-Host "      http://127.0.0.1:$Port" -ForegroundColor Green
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
    # 启动前先备份一次数据库，避免长期使用中意外丢数据（失败不影响启动）
    & $python scripts\backup_db.py
} catch {
    Write-Host 'WARN: backup failed, continue.' -ForegroundColor Yellow
}
Pop-Location

Push-Location $backend
try {
    & $python -m uvicorn app.main:app --host 0.0.0.0 --port $Port
}
finally {
    Pop-Location
}
