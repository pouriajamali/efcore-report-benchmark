param([Parameter(Mandatory=$true)][string]$Dotnet,[string]$LocalDb='C:/Program Files/Microsoft SQL Server/150/Tools/Binn/SqlLocalDB.exe')
$ErrorActionPreference='Stop'
$labRoot=$PSScriptRoot
if (-not (Test-Path -LiteralPath $Dotnet)) { throw 'Pass a .NET 10 SDK host path.' }
if (-not (Test-Path -LiteralPath $LocalDb)) { throw 'SQL Server 2019 LocalDB is required.' }
$workPath=Join-Path $labRoot '.work'
$env:DOTNET_CLI_HOME=Join-Path $workPath 'dotnet-home'
$env:DOTNET_CLI_TELEMETRY_OPTOUT='1'
$env:DOTNET_GENERATE_ASPNET_CERTIFICATE='false'
$instanceName='JB_EF10Bench_20261109'
$instances=& $LocalDb info
if ($instances -notcontains $instanceName) {
    & $LocalDb create $instanceName
    if ($LASTEXITCODE) { throw 'Dedicated LocalDB creation failed.' }
}
& $LocalDb start $instanceName
if ($LASTEXITCODE) { throw 'Dedicated LocalDB start failed.' }
try {
    if (Test-Path -LiteralPath (Join-Path $labRoot 'results/samples.csv')) {
        $previous=Join-Path $labRoot ('runs/previous-'+(Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmssfff'))
        Copy-Item -LiteralPath (Join-Path $labRoot 'results') -Destination $previous -Recurse
    }
    & $Dotnet restore (Join-Path $labRoot 'Benchmark/Benchmark.csproj') --locked-mode --packages (Join-Path $workPath 'packages') --verbosity minimal
    if ($LASTEXITCODE) { throw 'Locked audited restore failed.' }
    & $Dotnet build (Join-Path $labRoot 'Benchmark/Benchmark.csproj') -c Release --no-restore --verbosity minimal
    if ($LASTEXITCODE) { throw 'Release build failed.' }
    & $Dotnet (Join-Path $labRoot 'Benchmark/bin/Release/net10.0/Benchmark.dll') $labRoot
    if ($LASTEXITCODE) { throw 'Primary experiment failed.' }
    & $Dotnet (Join-Path $labRoot 'Benchmark/bin/Release/net10.0/Benchmark.dll') $labRoot --verify-fix
    if ($LASTEXITCODE) { throw 'Scoped override verification failed.' }
} finally {
    & $LocalDb stop $instanceName
}
