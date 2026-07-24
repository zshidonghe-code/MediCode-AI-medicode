$ErrorActionPreference = 'Stop'

$harmonyRoot = Split-Path -Parent $PSScriptRoot
$medicodeSdkHome = 'C:\Program Files\Huawei\DevEco Studio\sdk'
$medicodeHvigorHome = 'C:\Users\Donghe\.hvigor-medicode'
$medicodeJavaHome = 'C:\Program Files\Huawei\DevEco Studio\jbr'
$hvigor = 'C:\Program Files\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.bat'

$env:DEVECO_SDK_HOME = $medicodeSdkHome
$env:HVIGOR_USER_HOME = $medicodeHvigorHome
$env:JAVA_HOME = $medicodeJavaHome
$env:Path = "$medicodeJavaHome\bin;$env:Path"

Push-Location $harmonyRoot
try {
  & $hvigor --mode module -p product=default assembleHap
  if ($LASTEXITCODE -ne 0) {
    throw "HarmonyOS build failed with exit code $LASTEXITCODE"
  }

  $hap = Join-Path $harmonyRoot 'entry\build\default\outputs\default\entry-default-unsigned.hap'
  if (-not (Test-Path -LiteralPath $hap)) {
    throw "HAP output was not generated: $hap"
  }
  if ((Get-Item -LiteralPath $hap).Length -le 0) {
    throw "HAP output is empty: $hap"
  }
  Write-Output "HAP verified: $hap"
}
finally {
  Pop-Location
}
