param(
    [switch]$RunProviderSmoke
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$databaseUrl = "postgresql+psycopg://apiforgekit:apiforgekit@host.docker.internal:5432/apiforgekit"
$image = "python:3.13-slim"

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
}

Push-Location $root
try {
    docker info *> $null
    docker compose up -d
    git diff --check

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
python - <<'PY'
from dotenv import load_dotenv
load_dotenv(".env")
from core.config import get_settings
from core.database import build_engine, build_session_factory, init_db
from core.observability import ObservabilityRepository
from core.xai_live_runner import XaiLiveRunner

settings = get_settings()
engine = build_engine(settings.database_url)
session_factory = build_session_factory(engine)
init_db(engine)
repo = ObservabilityRepository(session_factory)
runner = XaiLiveRunner(repo)
run = repo.start_run("xai", "responses_api_smoke", ["responses_api"])
runner._run_responses_basic(run["id"])
events = repo.list_events(limit=5, run_id=run["id"])
started = [event for event in events if event["event_type"] == "request_started"][0]
success = [event for event in events if event["status"] == "success"][0]
repo.finish_run(run["id"], "success", {"module": success["module"], "test_name": success["test_name"]})
response = success.get("response") or {}
print({
    "run_id": run["id"],
    "status": success["status"],
    "module": success["module"],
    "test_name": success["test_name"],
    "endpoint": (started.get("request") or {}).get("endpoint"),
    "latency_ms": success.get("latency_ms"),
    "output_text_preview": response.get("output_text_preview"),
    "total_tokens": (success.get("tokens") or response.get("tokens") or {}).get("total_tokens"),
})
PY
"@

        Invoke-DockerPython -Command $providerValidation
    }
}
finally {
    Pop-Location
}
