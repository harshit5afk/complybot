$pptFile = "C:\STAR WARS\complybot\ComplyBot_Infothon_7.0_Final.pptx"
$imgDir = "C:\STAR WARS\complybot\slide_previews"

if (!(Test-Path $imgDir)) {
    New-Item -ItemType Directory -Path $imgDir | Out-Null
}

try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open($pptFile, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    
    for ($i = 1; $i -le $pres.Slides.Count; $i++) {
        $slide = $pres.Slides.Item($i)
        $outPath = Join-Path $imgDir "slide_$i.png"
        $slide.Export($outPath, "PNG", 1920, 1080)
        Write-Host "Exported Slide $i to $outPath"
    }
    
    $pres.Close()
    $ppt.Quit()
} catch {
    Write-Host "Error exporting slides to PNG: $_"
}
