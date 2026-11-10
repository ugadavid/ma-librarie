param(
    [Parameter(Mandatory = $true)]
    [string] $InnoCompiler,
    [string] $PythonExe
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-BuildTool {
    param([string] $Executable, [string[]] $Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Executable exited with code $LASTEXITCODE."
    }
}

$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$InnoCompiler = (Resolve-Path -LiteralPath $InnoCompiler).Path
if (!$PythonExe) {
    $PythonExe = Invoke-BuildTool 'py.exe' @('-3.13', '-I', '-c', 'import sys; print(sys.executable)')
}
$Runtime = Invoke-BuildTool $PythonExe @('-I', '-c', "import platform, struct, sys; print(platform.system(), platform.machine(), struct.calcsize('P') * 8, sys.version.split()[0])")
if ($Runtime -ne 'Windows AMD64 64 3.13.5') {
    throw "Expected Windows x64 and CPython 3.13.5 x64. Found: $Runtime"
}
$CompilerVersion = Invoke-BuildTool $InnoCompiler @('--version')
if ($CompilerVersion -ne '7.1.1') {
    throw "Expected Inno Setup 7.1.1. Found: $CompilerVersion"
}

$Version, $WindowsVersion = Invoke-BuildTool $PythonExe @('-I', '-c',
    "import runpy,sys; values = runpy.run_path(sys.argv[1]); print(values['__version__']); print('.'.join(map(str, values['WINDOWS_VERSION'])))",
    (Join-Path $Root 'catalogue/__init__.py'))
if ($Version -notmatch '^(alpha-)?\d+\.\d+\.\d+$') {
    throw "Invalid product version: $Version"
}

$Work = Join-Path $Root ('.build/windows/' + [guid]::NewGuid().ToString('N'))
$Output = Join-Path $Root "dist/windows/$Version"
New-Item -ItemType Directory -Path $Work,$Output -Force | Out-Null
$Venv = Join-Path $Work 'venv'
Invoke-BuildTool $PythonExe @('-I', '-m', 'venv', $Venv)
$BuildPython = Join-Path $Venv 'Scripts/python.exe'
Invoke-BuildTool $BuildPython @('-I', '-m', 'pip', '--disable-pip-version-check', 'install',
    '--only-binary=:all:', '--no-deps', '-r', (Join-Path $PSScriptRoot 'requirements-build.txt'))
Invoke-BuildTool $BuildPython @('-I', '-m', 'pip', 'check')

$PreviousCache = $env:PYINSTALLER_CONFIG_DIR
try {
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $Work 'cache'
    Invoke-BuildTool $BuildPython @('-I', '-m', 'PyInstaller', '--noconfirm', '--distpath', $Output,
        '--workpath', (Join-Path $Work 'pyinstaller'), (Join-Path $PSScriptRoot 'Ma-Mediatheque.spec'))
}
finally {
    $env:PYINSTALLER_CONFIG_DIR = $PreviousCache
}

$Application = Join-Path $Output 'Ma-Mediatheque'
Invoke-BuildTool $InnoCompiler @("/DProductVersion=$Version", "/DWindowsVersion=$WindowsVersion", "/DSourceDir=$Application",
    "/DOutputDir=$Output", (Join-Path $PSScriptRoot 'setup.iss'))

$Zip = Join-Path $Output "Ma-Mediatheque-$Version-windows-x64.zip"
$Setup = Join-Path $Output "Ma-Mediatheque-$Version-windows-x64-setup.exe"
$TemporaryZip = Join-Path $Work 'package.zip'
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $Application, $TemporaryZip, [System.IO.Compression.CompressionLevel]::Optimal, $true)
Move-Item -LiteralPath $TemporaryZip -Destination $Zip -Force

$Checksums = foreach ($Asset in @($Zip, $Setup)) {
    $Hash = (Get-FileHash -LiteralPath $Asset -Algorithm SHA256).Hash.ToLowerInvariant()
    "$Hash  $([System.IO.Path]::GetFileName($Asset))"
}
Set-Content -LiteralPath (Join-Path $Output 'SHA256SUMS.txt') -Value $Checksums -Encoding ASCII
Get-Item -LiteralPath @((Join-Path $Application 'Ma-Mediatheque.exe'), $Zip, $Setup, (Join-Path $Output 'SHA256SUMS.txt'))
