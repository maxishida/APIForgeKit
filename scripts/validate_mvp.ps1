param(
    [switch]$RunProviderSmoke
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$databaseUrl = "postgresql+psycopg://apiforgekit:apiforgekit@host.docker.internal:5432/apiforgekit"
$image = "python:3.13-slim"

function Assert-LastExitCode {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Step
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

function Invoke-DockerPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    docker run --rm `
        -v "${root}:/app" `
        -w /app `
        -e "DATABASE_URL=$databaseUrl" `
        $image `
        bash -lc $Command
    Assert-LastExitCode "docker python validation"
}

Push-Location $root
try {
    docker info *> $null
    Assert-LastExitCode "docker info"
    docker compose up -d
    Assert-LastExitCode "docker compose up"
    git diff --check
    Assert-LastExitCode "git diff --check"

    $baseValidation = @"
python -m pip install --no-cache-dir -r requirements.txt >/tmp/pip-install.log &&
python -m pytest -q &&
python -m compileall app.py core ui agents scripts run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py &&
python run_algorithm_lab.py --suite lead_score --export &&
python run_acp_workflow.py &&
python scripts/ui_smoke_local.py &&
python scripts/clean_demo_artifacts.py
"@

    Invoke-DockerPython -Command $baseValidation

    if ($RunProviderSmoke) {
        $providerValidation = @"
python -m pip install --no-cache-dir -r requirements.txt >/tmp/pip-install.log &&
python run_xai_voice.py --export-report &&
python scripts/xai_responses_smoke.py
"@

        Invoke-DockerPython -Command $providerValidation
    }
}
finally {
    Pop-Location
}
