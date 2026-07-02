$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
docker compose -f "$root/docker-compose.yml" up -d
docker run --rm -d `
  --name apiforgekit-studio `
  -v "${root}:/app" `
  -w /app `
  -p 8080:8080 `
  -e "DATABASE_URL=postgresql+psycopg://apiforgekit:apiforgekit@host.docker.internal:5432/apiforgekit" `
  -e "APP_HOST=0.0.0.0" `
  -e "PYTHONPATH=/app" `
  python:3.13-slim `
  bash -lc "pip install -q -r requirements.txt && python app.py"
Write-Host "Studio em http://127.0.0.1:8080/community-bot-lab"