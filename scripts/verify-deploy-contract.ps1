# 部署契约演练脚本：验证"静态托管前端 + 跨源直连后端"的完整浏览器契约。
# 用法：
#   powershell -File scripts/verify-deploy-contract.ps1 -BackendOrigin https://xxx.onrender.com [-FrontendOrigin https://yyy.vercel.app]
# 不带 -FrontendOrigin 时本地演练：以 VITE_API_BASE_URL 构建 web-frontend 并用 vite preview 伺服。
# 校验点：静态页加载、OPTIONS 预检、匿名 POST、登录换 token、带 Authorization 的认证请求与暴露头。
param(
  [Parameter(Mandatory = $true)][string]$BackendOrigin,
  [string]$FrontendOrigin = ""
)

$ErrorActionPreference = "Stop"
$BackendOrigin = $BackendOrigin.TrimEnd("/")
$repoRoot = Split-Path -Parent $PSScriptRoot
$cleanup = @()

if (-not $FrontendOrigin) {
  Write-Host "== 本地演练：构建带 base URL 的产物并静态伺服 =="
  $env:VITE_API_BASE_URL = $BackendOrigin
  Push-Location (Join-Path $repoRoot "web-frontend")
  npm run build 2>&1 | Select-Object -Last 1 | Out-Host
  $npxCmd = (Get-Command npx.cmd -ErrorAction SilentlyContinue).Source
  if ($npxCmd) { $previewArgs = "vite", "preview", "--host", "127.0.0.1", "--port", "4173", "--strictPort" }
  else { $npxCmd = "cmd.exe"; $previewArgs = "/c", "npx", "vite", "preview", "--host", "127.0.0.1", "--port", "4173", "--strictPort" }
  $preview = Start-Process -FilePath $npxCmd -ArgumentList $previewArgs -PassThru -WindowStyle Hidden
  $cleanup += { Stop-Process -Id $preview.Id -Force -ErrorAction SilentlyContinue }
  Pop-Location
  $FrontendOrigin = "http://127.0.0.1:4173"
  Start-Sleep -Seconds 4
}

$failures = 0
function Check([string]$name, [scriptblock]$block) {
  try { & $block | Out-Host; Write-Host "PASS $name" -ForegroundColor Green }
  catch { $failures++; Write-Host "FAIL $name : $($_.Exception.Message)" -ForegroundColor Red }
}

Check "静态页加载" {
  $r = Invoke-WebRequest -Uri "$FrontendOrigin/" -TimeoutSec 15 -UseBasicParsing
  if ($r.StatusCode -ne 200 -or $r.Content -notmatch "<div id=") { throw "index.html 异常" }
  "status=$($r.StatusCode)"
}
Check "OPTIONS 预检" {
  $r = Invoke-WebRequest -Uri "$BackendOrigin/api/auth/send-code" -Method OPTIONS -Headers @{
    Origin = $FrontendOrigin; "Access-Control-Request-Method" = "POST"; "Access-Control-Request-Headers" = "content-type" } -TimeoutSec 15 -UseBasicParsing
  if ($r.Headers["Access-Control-Allow-Origin"] -ne $FrontendOrigin) { throw "allow-origin=$($r.Headers['Access-Control-Allow-Origin'])" }
  "allow-origin=$($r.Headers['Access-Control-Allow-Origin'])"
}
Check "匿名 POST send-code" {
  $r = Invoke-WebRequest -Uri "$BackendOrigin/api/auth/send-code" -Method POST -ContentType "application/json" -Headers @{ Origin = $FrontendOrigin } -Body '{"phone":"13800138000"}' -TimeoutSec 15 -UseBasicParsing
  if ($r.StatusCode -ne 200) { throw "status=$($r.StatusCode)" }
  "status=$($r.StatusCode)"
}
Check "登录换 token" {
  $script:token = (Invoke-RestMethod -Uri "$BackendOrigin/api/auth/login-phone" -Method POST -ContentType "application/json" -Headers @{ Origin = $FrontendOrigin } -Body '{"phone":"13800138000","code":"123456"}' -TimeoutSec 15).data.token
  if (-not $script:token) { throw "token 为空" }
  "token 长度=$($script:token.Length)"
}
Check "认证 GET draft/list" {
  $r = Invoke-WebRequest -Uri "$BackendOrigin/api/draft/list" -Headers @{ Origin = $FrontendOrigin; Authorization = "Bearer $($script:token)" } -TimeoutSec 15 -UseBasicParsing
  if ($r.Headers["Access-Control-Allow-Origin"] -ne $FrontendOrigin) { throw "allow-origin 缺失" }
  "status=$($r.StatusCode) expose=$($r.Headers['Access-Control-Expose-Headers'])"
}

foreach ($c in $cleanup) { & $c }
if ($failures -gt 0) { Write-Host "`n$failures 项失败——检查后端 CORS_ORIGINS 与前端 VITE_API_BASE_URL。" -ForegroundColor Red; exit 1 }
Write-Host "`n部署契约 5/5 通过。" -ForegroundColor Green
