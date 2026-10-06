$pptFile = "C:\STAR WARS\complybot\ComplyBot_Infothon_7.0_Final.pptx"
$pdfFile = "C:\STAR WARS\complybot\ComplyBot_Infothon_7.0_Final.pdf"
$dlPdfFile = "$HOME\Downloads\ComplyBot_Infothon_7.0_Final.pdf"

try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open($pptFile, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    # ppSaveAsPDF = 32
    $pres.SaveAs($pdfFile, 32)
    $pres.SaveAs($dlPdfFile, 32)
    $pres.Close()
    $ppt.Quit()
    Write-Host "Successfully exported PDF to: $pdfFile and $dlPdfFile"
} catch {
    Write-Host "Error converting to PDF: $_"
}
