import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


PROVIDER = "anthropic"
ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs"
load_dotenv(ROOT / ".env")
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL") or "claude-sonnet-4-20250514"


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


def get_client(test_name, started):
    load_dotenv(ROOT / ".env")
    if not os.getenv("ANTHROPIC_API_KEY"):
        save_output(
            test_name,
            "skipped_missing_env",
            DEFAULT_MODEL,
            started,
            "ANTHROPIC_API_KEY missing",
            error_message="Set ANTHROPIC_API_KEY in .env",
        )
        return None
    try:
        import anthropic
    except ImportError as exc:
        save_output(test_name, "missing_dependency", DEFAULT_MODEL, started, "import anthropic", error_message=str(exc))
        return None
    return anthropic.Anthropic()


def text_from_message(message):
    parts = []
    for block in getattr(message, "content", []) or []:
        if getattr(block, "type", "") == "text":
            parts.append(getattr(block, "text", ""))
    return "".join(parts)


def run_auth():
    started = time.perf_counter()
    client = get_client("auth", started)
    if not client:
        return
    try:
        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=8,
            messages=[{"role": "user", "content": "Reply with ok."}],
        )
        save_output("auth", "ok", DEFAULT_MODEL, started, "Minimal Messages API call", text_from_message(message), raw_response=message)
    except Exception as exc:
        save_output("auth", "error", DEFAULT_MODEL, started, "Minimal Messages API call", error_message=str(exc))


def run_basic():
    started = time.perf_counter()
    client = get_client("basic", started)
    if not client:
        return
    try:
        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=32,
            messages=[{"role": "user", "content": "Reply with exactly: api-lab-ok"}],
        )
        save_output("basic", "ok", DEFAULT_MODEL, started, "Messages API text call", text_from_message(message), raw_response=message)
    except Exception as exc:
        save_output("basic", "error", DEFAULT_MODEL, started, "Messages API text call", error_message=str(exc))


def run_stream():
    started = time.perf_counter()
    client = get_client("stream", started)
    if not client:
        return
    chunks = []
    try:
        with client.messages.stream(
            model=DEFAULT_MODEL,
            max_tokens=64,
            messages=[{"role": "user", "content": "Count from one to three."}],
        ) as stream:
            for text in stream.text_stream:
                chunks.append(text)
        save_output("stream", "ok", DEFAULT_MODEL, started, "Messages API stream", "".join(chunks), raw_response={"chunks": chunks})
    except Exception as exc:
        save_output("stream", "error", DEFAULT_MODEL, started, "Messages API stream", error_message=str(exc))


def run_tools():
    started = time.perf_counter()
    client = get_client("tools", started)
    if not client:
        return
    tools = [{
        "name": "get_lab_weather",
        "description": "Return fake lab weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
        },
    }]
    try:
        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=128,
            tools=tools,
            messages=[{"role": "user", "content": "Use the tool to get lab weather for Tokyo."}],
        )
        summary = "tool_use_detected" if "tool_use" in clean_raw(message) else "no_tool_use_detected"
        save_output("tools", "ok", DEFAULT_MODEL, started, "Messages API tool use", summary, raw_response=message)
    except Exception as exc:
        save_output("tools", "error", DEFAULT_MODEL, started, "Messages API tool use", error_message=str(exc))


def main():
    parser = argparse.ArgumentParser(description="Anthropic API lab")
    parser.add_argument("--case", choices=["auth", "basic", "stream", "tools"], required=True)
    args = parser.parse_args()
    {
        "auth": run_auth,
        "basic": run_basic,
        "stream": run_stream,
        "tools": run_tools,
    }[args.case]()


if __name__ == "__main__":
    main()
