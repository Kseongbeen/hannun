# PPTX를 슬라이드별 PNG로 내보낸다(PowerPoint COM). 사용: powershell -File render_ppt.ps1 <pptx> <출력폴더>
param([string]$pptx, [string]$out)
New-Item -ItemType Directory -Force $out | Out-Null
Get-ChildItem $out -Filter *.png | Remove-Item
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open((Resolve-Path $pptx).Path, $true, $false, $false)
$i = 1
foreach ($s in $pres.Slides) {
    $s.Export((Join-Path (Resolve-Path $out).Path ("{0:D2}.png" -f $i)), "PNG", 1333, 750)
    $i++
}


$pres.Close()
if ($app.Presentations.Count -eq 0) { $app.Quit() }   # 사용자가 열어 둔 파워포인트는 닫지 않는다
Write-Output "rendered $($i-1)"
