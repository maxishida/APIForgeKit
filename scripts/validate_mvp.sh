#!/usr/bin/env bash
set -euo pipefail

run_provider_smoke=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider-smoke)
      run_provider_smoke=true
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
database_url="postgresql+psycopg://apiforgekit:apiforgekit@host.docker.internal:5432/apiforgekit"
image="python:3.13-slim"
docker_root="${root}"

if command -v cygpath >/dev/null 2>&1; then
  docker_root="$(cygpath -w "${root}")"
  export MSYS_NO_PATHCONV=1
fi

run_docker_python() {
  local command="$1"

  docker run --rm \
    --add-host=host.docker.internal:host-gateway \
    -v "${docker_root}:/app" \
    -w /app \
    -e "DATABASE_URL=${database_url}" \
    "${image}" \
    bash -lc "${command}"
}

assert_docker_ready() {
  if ! docker info >/dev/null 2>&1; then
    echo "Docker Desktop/Engine não está pronto. Inicie o Docker Desktop/Engine, aguarde o daemon e execute npm run validate:mvp novamente." >&2
    exit 1
  fi
}

cd "${root}"

assert_docker_ready
docker compose up -d
git diff --check

base_validation='python -m pip install --no-cache-dir -r requirements.txt >/tmp/pip-install.log &&
python -m pytest -q &&
python -m compileall app.py core ui agents scripts run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py &&
python run_algorithm_lab.py --suite lead_score --export &&
python run_acp_workflow.py &&
python scripts/ui_smoke_local.py &&
python scripts/clean_demo_artifacts.py'

run_docker_python "${base_validation}"

if [[ "${run_provider_smoke}" == "true" ]]; then
  provider_validation='python -m pip install --no-cache-dir -r requirements.txt >/tmp/pip-install.log &&
python run_xai_voice.py --export-report &&
python scripts/xai_responses_smoke.py'

  run_docker_python "${provider_validation}"
fi
