import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


PROVIDER = "xai"
ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs"
load_dotenv(ROOT / ".env")
DEFAULT_MODEL = os.getenv("XAI_MODEL") or "grok-4.20-reasoning"


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
    if not os.getenv("XAI_API_KEY"):
        save_output(
            test_name,
            "skipped_missing_env",
            DEFAULT_MODEL,
            started,
            "XAI_API_KEY missing",
            error_message="Set XAI_API_KEY in api-lab-kit/.env",
        )
        return None, None
    try:
        from xai_sdk import Client
        from xai_sdk.chat import system, tool, tool_result, user
    except ImportError as exc:
        save_output(test_name, "missing_dependency", DEFAULT_MODEL, started, "import xai-sdk", error_message=str(exc))
        return None, None
    return Client(api_key=os.getenv("XAI_API_KEY")), {"system": system, "tool": tool, "tool_result": tool_result, "user": user}


def run_auth():
    started = time.perf_counter()
    client, chat_types = get_client("auth", started)
    if not client:
        return
    try:
        chat = client.chat.create(model=DEFAULT_MODEL)
        chat.append(chat_types["user"]("Reply with ok."))
        response = chat.sample()
        save_output("auth", "ok", DEFAULT_MODEL, started, "Minimal xAI chat sample", getattr(response, "content", ""), raw_response=response)
    except Exception as exc:
        save_output("auth", "error", DEFAULT_MODEL, started, "Minimal xAI chat sample", error_message=str(exc))


def run_basic():
    started = time.perf_counter()
    client, chat_types = get_client("basic", started)
    if not client:
        return
    try:
        chat = client.chat.create(model=DEFAULT_MODEL)
        chat.append(chat_types["system"]("You are a concise API lab assistant."))
        chat.append(chat_types["user"]("Reply with exactly: api-lab-ok"))
        response = chat.sample()
        save_output("basic", "ok", DEFAULT_MODEL, started, "xAI chat sample text call", getattr(response, "content", ""), raw_response=response)
    except Exception as exc:
        save_output("basic", "error", DEFAULT_MODEL, started, "xAI chat sample text call", error_message=str(exc))


def run_stream():
    started = time.perf_counter()
    client, chat_types = get_client("stream", started)
    if not client:
        return
    chunks = []
    try:
        chat = client.chat.create(model=DEFAULT_MODEL)
        chat.append(chat_types["user"]("Count from one to three."))
        final_response = None
        for response, chunk in chat.stream():
            final_response = response
            if getattr(chunk, "content", ""):
                chunks.append(chunk.content)
        save_output("stream", "ok", DEFAULT_MODEL, started, "xAI chat stream", "".join(chunks), raw_response=final_response or {"chunks": chunks})
    except Exception as exc:
        save_output("stream", "error", DEFAULT_MODEL, started, "xAI chat stream", error_message=str(exc))


def run_tools():
    started = time.perf_counter()
    client, chat_types = get_client("tools", started)
    if not client:
        return
    try:
        lab_tool = chat_types["tool"](
            name="get_lab_weather",
            description="Return fake lab weather for a city.",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name"}},
                "required": ["city"],
            },
        )
        chat = client.chat.create(model=DEFAULT_MODEL, tools=[lab_tool])
        chat.append(chat_types["user"]("Use the tool to get lab weather for Tokyo."))
        response = chat.sample()
        if getattr(response, "tool_calls", None):
            chat.append(response)
            for call in response.tool_calls:
                result = {"city": "Tokyo", "weather": "lab-clear"}
                chat.append(chat_types["tool_result"](json.dumps(result)))
            response = chat.sample()
        summary = "tool_call_detected" if "tool_calls" in clean_raw(response) else "no_tool_call_detected"
        save_output("tools", "ok", DEFAULT_MODEL, started, "xAI function tool call", summary, raw_response=response)
    except Exception as exc:
        save_output("tools", "error", DEFAULT_MODEL, started, "xAI function tool call", error_message=str(exc))


def main():
    parser = argparse.ArgumentParser(description="xAI API lab")
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
