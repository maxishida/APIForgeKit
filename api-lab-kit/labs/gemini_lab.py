import argparse
import base64
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


PROVIDER = "gemini"
ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs"
load_dotenv(ROOT / ".env")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"


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
    if not os.getenv("GEMINI_API_KEY"):
        save_output(
            test_name,
            "skipped_missing_env",
            DEFAULT_MODEL,
            started,
            "GEMINI_API_KEY missing",
            error_message="Set GEMINI_API_KEY in api-lab-kit/.env",
        )
        return None, None
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        save_output(test_name, "missing_dependency", DEFAULT_MODEL, started, "import google-genai", error_message=str(exc))
        return None, None
    return genai.Client(), types


def run_auth():
    started = time.perf_counter()
    client, _ = get_client("auth", started)
    if not client:
        return
    try:
        models = []
        for model in client.models.list():
            models.append(getattr(model, "name", str(model)))
            if len(models) >= 5:
                break
        save_output("auth", "ok", "models.list", started, "List first available models", ", ".join(models), raw_response=models)
    except Exception as exc:
        save_output("auth", "error", "models.list", started, "List first available models", error_message=str(exc))


def run_basic():
    started = time.perf_counter()
    client, _ = get_client("basic", started)
    if not client:
        return
    try:
        response = client.models.generate_content(model=DEFAULT_MODEL, contents="Reply with exactly: api-lab-ok")
        save_output("basic", "ok", DEFAULT_MODEL, started, "generate_content text call", response.text, raw_response=response)
    except Exception as exc:
        save_output("basic", "error", DEFAULT_MODEL, started, "generate_content text call", error_message=str(exc))


def run_stream():
    started = time.perf_counter()
    client, _ = get_client("stream", started)
    if not client:
        return
    chunks = []
    try:
        response = client.models.generate_content_stream(model=DEFAULT_MODEL, contents="Count from one to three.")
        for chunk in response:
            chunks.append(getattr(chunk, "text", ""))
        save_output("stream", "ok", DEFAULT_MODEL, started, "generate_content_stream text call", "".join(chunks), raw_response={"chunks": chunks})
    except Exception as exc:
        save_output("stream", "error", DEFAULT_MODEL, started, "generate_content_stream text call", error_message=str(exc))


def run_tools():
    started = time.perf_counter()
    client, _ = get_client("tools", started)
    if not client:
        return
    tool_config = {
        "tools": [{
            "function_declarations": [{
                "name": "get_lab_weather",
                "description": "Return fake lab weather for a city.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string", "description": "City name"}},
                    "required": ["city"],
                },
            }]
        }]
    }
    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents="Use the function to get lab weather for Tokyo.",
            config=tool_config,
        )
        summary = "function_call_detected" if "function_call" in clean_raw(response) else "no_function_call_detected"
        save_output("tools", "ok", DEFAULT_MODEL, started, "Gemini function declaration", summary, raw_response=response)
    except Exception as exc:
        save_output("tools", "error", DEFAULT_MODEL, started, "Gemini function declaration", error_message=str(exc))


def run_vision():
    started = time.perf_counter()
    client, types = get_client("vision", started)
    if not client:
        return
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNk+M8AAAQBAQDJ/pLvAAAAAElFTkSuQmCC"
    )
    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=[
                "What is the dominant color of this image? Answer briefly.",
                types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
            ],
        )
        save_output("vision", "ok", DEFAULT_MODEL, started, "Gemini inline PNG vision prompt", response.text, raw_response=response)
    except Exception as exc:
        save_output("vision", "error", DEFAULT_MODEL, started, "Gemini inline PNG vision prompt", error_message=str(exc))


def main():
    parser = argparse.ArgumentParser(description="Gemini API lab")
    parser.add_argument("--case", choices=["auth", "basic", "stream", "tools", "vision"], required=True)
    args = parser.parse_args()
    {
        "auth": run_auth,
        "basic": run_basic,
        "stream": run_stream,
        "tools": run_tools,
        "vision": run_vision,
    }[args.case]()


if __name__ == "__main__":
    main()
