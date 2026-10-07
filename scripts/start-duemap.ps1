param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$frontendRoot = Join-Path $projectRoot 'frontend'
$logRoot = Join-Path $projectRoot '.local-data\logs'
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$vitePath = Join-Path $frontendRoot 'node_modules\vite\bin\vite.js'
$appUrl = 'http://127.0.0.1:5173'

function Test-Endpoint([string]$Url) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Wait-Endpoint([string]$Url, [System.Diagnostics.Process]$ServerProcess) {
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if (Test-Endpoint $Url) { return }
        if ($ServerProcess.HasExited) {
            throw "The server stopped during startup. Check logs in $logRoot"
        }
        Start-Sleep -Milliseconds 500
    }
    throw "The server did not become ready. Check logs in $logRoot"
}

try {
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

    if (-not (Test-Endpoint 'http://127.0.0.1:8000/openapi.json')) {
        if (-not (Test-Path -LiteralPath $pythonPath)) {
            throw "Python environment missing: $pythonPath"
        }
        Write-Host 'Starting DueMap API...'
        $apiProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m', 'uvicorn', 'bnpl_cashflow.api.app:app', '--reload', '--reload-dir', 'src', '--host', '127.0.0.1', '--port', '8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'api.stdout.log') -RedirectStandardError (Join-Path $logRoot 'api.stderr.log') -PassThru
        Wait-Endpoint 'http://127.0.0.1:8000/openapi.json' $apiProcess
    }

    $apiSchema = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/openapi.json' -TimeoutSec 5
    if (-not $apiSchema.paths.PSObject.Properties['/api/profiles/{profile_id}/projection']) {
        throw 'An older API is already running on port 8000 without the Projection endpoint. Stop that DueMap API process, then run Start-DueMap.bat again.'
    }

    if (-not (Test-Endpoint $appUrl)) {
        if (-not (Test-Path -LiteralPath $vitePath)) {
            throw 'Frontend dependencies are missing. Run npm ci in the frontend folder.'
        }
        $nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
        if ($nodeCommand) {
            $nodePath = $nodeCommand.Source
        } else {
            $runtimeRoot = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\runtimes\cua_node'
            $nodeRuntime = Get-ChildItem -Path (Join-Path $runtimeRoot '*\bin\node.exe') -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if (-not $nodeRuntime) { throw 'Node.js is missing. Install Node.js 22.12 or later.' }
            $nodePath = $nodeRuntime.FullName
        }
        Write-Host 'Starting DueMap frontend...'
        $frontendProcess = Start-Process -FilePath $nodePath -ArgumentList 'node_modules/vite/bin/vite.js', '--host', '127.0.0.1' -WorkingDirectory $frontendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'frontend.stdout.log') -RedirectStandardError (Join-Path $logRoot 'frontend.stderr.log') -PassThru
        Wait-Endpoint $appUrl $frontendProcess
    }

    if (-not (Test-Endpoint "$appUrl/api/profiles")) {
        throw 'The frontend cannot reach the DueMap API. Check the logs in .local-data\logs.'
    }
    Write-Host "DueMap is ready at $appUrl"
    if (-not $NoBrowser) { Start-Process $appUrl }
} catch {
    Write-Host "DueMap startup failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
