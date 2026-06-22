# Renders social-preview.html to a crisp 1280x640 PNG for the GitHub repo
# "Social preview" (Settings -> General -> Social preview).
# Strategy: headless Edge/Chrome screenshot at 2x device scale, then downscale
# to 1280x640 with Pillow (LANCZOS) for supersampled, crisp text.
$ErrorActionPreference = 'Stop'
$here  = $PSScriptRoot
$html  = Join-Path $here 'social-preview.html'
$png2x = Join-Path $here 'social-preview@2x.png'
$out   = Join-Path $here 'social-preview.png'

$browser = @(
  "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
  "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
  "C:\Program Files\Google\Chrome\Application\chrome.exe",
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) { throw "No Edge/Chrome found for rendering." }

if (Test-Path $png2x) { Remove-Item $png2x -Force }
$uri = ([System.Uri]$html).AbsoluteUri

& $browser --headless=new --disable-gpu --hide-scrollbars `
  --force-device-scale-factor=2 --virtual-time-budget=8000 `
  --window-size=1280,640 "--screenshot=$png2x" $uri | Out-Null

if (-not (Test-Path $png2x)) { throw "Screenshot failed - no output produced." }

python -c "from PIL import Image; im=Image.open(r'$png2x').convert('RGB'); im=im.resize((1280,640), Image.LANCZOS); im.save(r'$out', optimize=True); print('saved', im.size)"
Remove-Item $png2x -Force -ErrorAction SilentlyContinue

$kb = [math]::Round((Get-Item $out).Length / 1KB, 1)
Write-Output "Done -> $out  (${kb} KB)"
