# --- Configuration ---
$ChromePath = "$env:LOCALAPPDATA\Google\Chrome\User Data"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$FileName = "ChromeProfiles-$Timestamp.zip"
$DefaultTarget = "D:\Temp"
$ExcludedFolders = @("Cache", "Code Cache", "GPUCache", "Service Worker\CacheStorage", "OptimizationGuidePredictionModels", "OptGuideOnDeviceModel", "GrShaderCache", "DawnWebGPUCache", "component_crx_cache")

Write-Host "--- Chrome Profile Backup Tool (Accurate Progress) ---" -ForegroundColor Cyan
$InputPath = Read-Host "Target folder (Enter for D:\Temp)"
$TargetLocation = if ([string]::IsNullOrWhiteSpace($InputPath)) { $DefaultTarget } else { $InputPath.Replace('"', '') }
if (-not (Test-Path -Path $TargetLocation)) { New-Item -ItemType Directory -Path $TargetLocation -Force | Out-Null }
$FullOutputPath = Join-Path -ChildPath $FileName -Path $TargetLocation

try {
    Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
    $zipFile = [System.IO.Compression.ZipFile]::Open($FullOutputPath, [System.IO.Compression.ZipArchiveMode]::Create)
    
    # 1. Correct Filtering to find exactly 17 profiles
    $validProfiles = Get-ChildItem -Path $ChromePath -Directory | Where-Object { $_.Name -eq "Default" -or $_.Name -like "Profile *" }
    $totalProfiles = $validProfiles.Count
    $currentIndex = 0

    foreach ($profile in $validProfiles) {
        $currentIndex++
        Write-Progress -Id 0 -Activity "Overall Backup Progress" -Status "Profile $currentIndex of $totalProfiles" -PercentComplete (($currentIndex / $totalProfiles) * 100)

        $profileFiles = Get-ChildItem -Path $profile.FullName -Recurse -File | Where-Object {
            $filePath = $_.FullName; $isEx = $false; foreach ($f in $ExcludedFolders) { if ($filePath -like "*\$f\*") { $isEx = $true; break } }; -not $isEx
        }

        $itemIdx = 0; $itemCount = $profileFiles.Count
        foreach ($file in $profileFiles) {
            $itemIdx++
            Write-Progress -Id 1 -ParentId 0 -Activity "Processing: $($profile.Name)" -Status "Item $itemIdx of $itemCount ($($file.Name))" -PercentComplete (($itemIdx / $itemCount) * 100)
            try { [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zipFile, $file.FullName, $file.FullName.Substring($ChromePath.Length + 1), [System.IO.Compression.CompressionLevel]::Fastest) | Out-Null } catch { continue }
        }
    }
    $zipFile.Dispose(); Write-Host "`n[SUCCESS] Backup complete!" -ForegroundColor Green; exit 0
} catch { if ($zipFile) { $zipFile.Dispose() }; Write-Host "`n[ERROR] Backup failed: $($_.Exception.Message)"; exit 1 }