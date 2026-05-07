import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


PROVIDER = "openai"
ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs"
load_dotenv(ROOT / ".env")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL") or "gpt-5-mini"


def redact_text(text):
    redacted = str(text)
    for name in ("OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY"):
        value = os.getenv(name)
        if value:
            redacted = redacted.replace(value, f"{name[:4]}...REDACTED")
    return redacted


def clean_raw(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    raw = json.dumps(value, default=str, ensure_ascii=True)
    return redact_text(raw)


def save_output(test_name, status, model, started, request_summary, response_summary="", error_message="", raw_response=None):
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "provider": PROVIDER,
        "test_name": test_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "model_used": model,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "request_summary": request_summary,
        "response_summary": response_summary,
        "error_message": redact_text(error_message),
        "raw_response_without_secrets": clean_raw(raw_response) if raw_response is not None else "",
    }
    path = OUTPUTS_DIR / f"{datetime.now(timezone.utc).date()}_{PROVIDER}_{test_name}_result.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"saved: {path}")


def require_key(test_name, started):
    load_dotenv(ROOT / ".env")
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return True
    save_output(
        test_name,
        "skipped_missing_env",
        DEFAULT_MODEL,
        started,
        "OPENAI_API_KEY missing",
        error_message="Set OPENAI_API_KEY in api-lab-kit/.env",
    )
    return False


def get_client(test_name, started):
    if not require_key(test_name, started):
        return None
    try:
        from openai import OpenAI
    except ImportError as exc:
        save_output(test_name, "missing_dependency", DEFAULT_MODEL, started, "import openai", error_message=str(exc))
        return None
    return OpenAI()


def run_auth():
    started = time.perf_counter()
    client = get_client("auth", started)
    if not client:
        return
    try:
        response = client.models.list()
        ids = [model.id for model in list(response.data)[:5]]
        save_output("auth", "ok", "models.list", started, "List first available models", ", ".join(ids), response)
    except Exception as exc:
        save_output("auth", "error", "models.list", started, "List first available models", error_message=str(exc))


def run_basic():
    started = time.perf_counter()
    client = get_client("basic", started)
    if not client:
        return
    try:
        response = client.responses.create(model=DEFAULT_MODEL, input="Reply with exactly: api-lab-ok")
        save_output("basic", "ok", DEFAULT_MODEL, started, "Responses API text call", response.output_text, response)
    except Exception as exc:
        save_output("basic", "error", DEFAULT_MODEL, started, "Responses API text call", error_message=str(exc))


def run_stream():
    started = time.perf_counter()
    client = get_client("stream", started)
    if not client:
        return
    chunks = []
    try:
        stream = client.responses.create(model=DEFAULT_MODEL, input="Count from one to three.", stream=True)
        for event in stream:
            if getattr(event, "type", "") == "response.output_text.delta":
                chunks.append(getattr(event, "delta", ""))
        save_output("stream", "ok", DEFAULT_MODEL, started, "Responses API stream=True", "".join(chunks), {"chunks": chunks})
    except Exception as exc:
        save_output("stream", "error", DEFAULT_MODEL, started, "Responses API stream=True", error_message=str(exc))


def run_tools():
    started = time.perf_counter()
    client = get_client("tools", started)
    if not client:
        return
    tools = [{
        "type": "function",
        "name": "get_lab_weather",
        "description": "Return fake lab weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    }]
    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input="Use the tool to get lab weather for Tokyo.",
            tools=tools,
        )
        summary = "tool_call_detected" if "function_call" in clean_raw(response) else "no_tool_call_detected"
        save_output("tools", "ok", DEFAULT_MODEL, started, "Responses API function tool", summary, response)
    except Exception as exc:
        save_output("tools", "error", DEFAULT_MODEL, started, "Responses API function tool", error_message=str(exc))


def run_structured():
    started = time.perf_counter()
    client = get_client("structured", started)
    if not client:
        return
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["ok"]},
            "provider": {"type": "string"},
        },
        "required": ["status", "provider"],
        "additionalProperties": False,
    }
    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input="Return JSON for an OpenAI lab success.",
            text={"format": {"type": "json_schema", "name": "lab_result", "schema": schema, "strict": True}},
        )
        parsed = json.loads(response.output_text)
        save_output("structured", "ok", DEFAULT_MODEL, started, "Responses API json_schema response", parsed, response)
    except Exception as exc:
        save_output("structured", "error", DEFAULT_MODEL, started, "Responses API json_schema response", error_message=str(exc))


def main():
    parser = argparse.ArgumentParser(description="OpenAI API lab")
    parser.add_argument("--case", choices=["auth", "basic", "stream", "tools", "structured"], required=True)
    args = parser.parse_args()
    {
        "auth": run_auth,
        "basic": run_basic,
        "stream": run_stream,
        "tools": run_tools,
        "structured": run_structured,
    }[args.case]()


if __name__ == "__main__":
    main()
