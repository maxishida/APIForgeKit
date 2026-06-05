from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Callable

from dotenv import load_dotenv

from core.config import ROOT_DIR
from core.observability import ObservabilityEventInput, ObservabilityRepository


DEFAULT_XAI_MODEL = "grok-4.3"


@dataclass(frozen=True)
class RunnerCase:
    module: str
    test_name: str
    callable_name: str


class XaiLiveRunner:
    def __init__(self, repository: ObservabilityRepository, model: str | None = None, load_env: bool = True):
        if load_env:
            load_dotenv(ROOT_DIR / ".env")
        self.repository = repository
        self.model = model or os.getenv("XAI_MODEL") or DEFAULT_XAI_MODEL

    def run_compact_sequence(self, stop_on_failure: bool = False) -> dict[str, object]:
        phases = ["connectivity", "chat", "structured_outputs", "streaming", "function_calling", "agents", "voice"]
        run = self.repository.start_run("xai", "live_observability_compact", phases)
        failed = False
        if not os.getenv("XAI_API_KEY"):
            self._event(
                run["id"],
                "connectivity",
                "readiness",
                "readiness_failed",
                "failed",
                "XAI_API_KEY ausente no .env local",
                request={"evidence_mode": "blocked"},
                error="Set XAI_API_KEY in .env before running real xAI tests.",
                recommendation="Configurar chave local e repetir a sequência.",
            )
            return self.repository.finish_run(run["id"], "failed", {"reason": "missing_xai_api_key"})

        cases = [
            RunnerCase("connectivity", "auth", "_run_auth"),
            RunnerCase("chat", "basic", "_run_basic"),
            RunnerCase("structured_outputs", "schema_parse", "_run_structured"),
            RunnerCase("streaming", "stream", "_run_stream"),
            RunnerCase("function_calling", "tools", "_run_tools"),
        ]
        for case in cases:
            try:
                getattr(self, case.callable_name)(run["id"])
            except Exception as exc:  # noqa: BLE001 - every runtime failure is evidence
                failed = True
                self._event(
                    run["id"],
                    case.module,
                    case.test_name,
                    "test_failed",
                    "failed",
                    f"{case.test_name} falhou",
                    error=str(exc),
                    recommendation="Registrar payload e comparar com docs xAI antes de corrigir.",
                )
                if stop_on_failure:
                    break
        self._record_blocked_future_phase(run["id"], "agents", "agent_task", "A fase Agents exige validação dedicada de endpoints/eventos antes de execução real.")
        self._record_blocked_future_phase(
            run["id"],
            "voice",
            "voice_realtime_agent",
            "A fase Voice Agent realtime exige fixture sintética, orçamento explícito e critérios próprios. Use /voice-lab para REST TTS/STT.",
        )
        status = "failed" if failed else "success"
        return self.repository.finish_run(run["id"], status, {"model": self.model, "compact_cases": len(cases)})

    def _get_client(self):
        from xai_sdk import Client
        from xai_sdk.chat import system, tool, tool_result, user

        return Client(api_key=os.getenv("XAI_API_KEY")), {
            "system": system,
            "tool": tool,
            "tool_result": tool_result,
            "user": user,
        }

    def _run_auth(self, run_id: str) -> None:
        client, chat_types = self._get_client()
        started = self._start(run_id, "connectivity", "auth", {"model": self.model})
        chat = client.chat.create(model=self.model)
        chat.append(chat_types["user"]("Reply with ok."))
        response = chat.sample()
        content = getattr(response, "content", "")
        self._finish(
            run_id,
            started,
            "connectivity",
            "auth",
            "Autenticação validada",
            {"content": content},
            recommendation="Chave e modelo acessíveis para testes compactos.",
        )

    def _run_basic(self, run_id: str) -> None:
        client, chat_types = self._get_client()
        started = self._start(run_id, "chat", "basic", {"model": self.model, "prompt": "api-lab-ok"})
        chat = client.chat.create(model=self.model)
        chat.append(chat_types["system"]("You are a concise API lab assistant."))
        chat.append(chat_types["user"]("Reply with exactly: api-lab-ok"))
        response = chat.sample()
        content = getattr(response, "content", "")
        self._finish(
            run_id,
            started,
            "chat",
            "basic",
            "Resposta de chat recebida",
            {"content": content},
            recommendation="Validar Responses API em seguida para integrações novas.",
        )

    def _run_stream(self, run_id: str) -> None:
        client, chat_types = self._get_client()
        started = self._start(run_id, "streaming", "stream", {"model": self.model, "stream": True})
        chunks: list[str] = []
        chunk_count = 0
        first_chunk_ms = None
        chat = client.chat.create(model=self.model)
        chat.append(chat_types["user"]("Count from one to three."))
        final_response = None
        for response, chunk in chat.stream():
            final_response = response
            chunk_text = getattr(chunk, "content", "")
            if chunk_text:
                chunk_count += 1
                if first_chunk_ms is None:
                    first_chunk_ms = round((time.perf_counter() - started) * 1000, 2)
                chunks.append(chunk_text)
                self._event(
                    run_id,
                    "streaming",
                    "stream",
                    "stream_chunk",
                    "running",
                    f"Chunk recebido #{chunk_count}",
                    latency_ms=first_chunk_ms or 0,
                    response={"chunk": chunk_text[:240], "chunk_count": chunk_count},
                )
        self._finish(
            run_id,
            started,
            "streaming",
            "stream",
            "Streaming finalizado",
            {"content": "".join(chunks), "chunk_count": chunk_count, "first_chunk_ms": first_chunk_ms, "raw": self._safe_response(final_response)},
            recommendation="Capturar first-token latency e chunk count em benchmarks.",
        )

    def _run_structured(self, run_id: str) -> None:
        from pydantic import BaseModel, Field

        class LabValidation(BaseModel):
            status: str = Field(description="Validation result: pass, warn, or fail")
            confidence: float = Field(description="Confidence from 0 to 1", ge=0, le=1)
            recommendation: str = Field(description="Short operational recommendation")

        client, chat_types = self._get_client()
        started = self._start(
            run_id,
            "structured_outputs",
            "schema_parse",
            {"model": self.model, "schema": LabValidation.model_json_schema()},
        )
        chat = client.chat.create(model=self.model)
        chat.append(chat_types["system"]("Return a structured API validation verdict."))
        chat.append(chat_types["user"]("The API returned HTTP 200, valid JSON, and 820ms latency. Classify the test."))
        response, parsed = chat.parse(LabValidation)
        self._event(
            run_id,
            "structured_outputs",
            "schema_parse",
            "structured_output_validated",
            "running",
            "Structured Output validado",
            response={"parsed": parsed.model_dump()},
        )
        self._finish(
            run_id,
            started,
            "structured_outputs",
            "schema_parse",
            "Structured output recebido e validado contra schema Pydantic",
            {"content": getattr(response, "content", ""), "parsed": parsed.model_dump(), "raw": self._safe_response(response)},
            recommendation="Usar schema versionado e validação local em todo teste com output estruturado.",
        )

    def _run_tools(self, run_id: str) -> None:
        client, chat_types = self._get_client()
        started = self._start(run_id, "function_calling", "tools", {"model": self.model, "tool": "get_lab_weather"})
        lab_tool = chat_types["tool"](
            name="get_lab_weather",
            description="Return deterministic lab weather for a city.",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name"}},
                "required": ["city"],
            },
        )
        chat = client.chat.create(model=self.model, tools=[lab_tool])
        chat.append(chat_types["user"]("Use the tool to get lab weather for Tokyo."))
        response = chat.sample()
        tool_calls = getattr(response, "tool_calls", None) or []
        if tool_calls:
            self._event(
                run_id,
                "function_calling",
                "tools",
                "tool_call_received",
                "running",
                "Tool call recebido",
                response={"tool_calls": self._safe_response(tool_calls)},
            )
            chat.append(response)
            for _ in tool_calls:
                chat.append(chat_types["tool_result"](json.dumps({"city": "Tokyo", "weather": "lab-clear"})))
            response = chat.sample()
        self._finish(
            run_id,
            started,
            "function_calling",
            "tools",
            "Function calling validado",
            {"tool_call_detected": bool(tool_calls), "content": getattr(response, "content", ""), "raw": self._safe_response(response)},
            recommendation="Registrar tool_call arguments e tool_result loop no adapter futuro.",
        )

    def _record_blocked_future_phase(self, run_id: str, module: str, test_name: str, message: str) -> None:
        self._event(
            run_id,
            module,
            test_name,
            "phase_blocked",
            "blocked",
            message,
            recommendation="Planejar teste real separado com orçamento, fixtures e critérios de aceite.",
        )

    def _start(self, run_id: str, module: str, test_name: str, request: dict[str, object]) -> float:
        started = time.perf_counter()
        event = self._event(
            run_id,
            module,
            test_name,
            "request_started",
            "running",
            "xAI Request Started",
            request=request,
        )
        self.repository.record_api_request(run_id, str(event["id"]), "xai", test_name, "xai_sdk.chat", request)
        return started

    def _finish(
        self,
        run_id: str,
        started: float,
        module: str,
        test_name: str,
        message: str,
        response: dict[str, object],
        recommendation: str,
    ) -> None:
        latency = round((time.perf_counter() - started) * 1000, 2)
        event = self._event(
            run_id,
            module,
            test_name,
            "response_received",
            "success",
            message,
            latency_ms=latency,
            response=response,
            recommendation=recommendation,
        )
        self.repository.record_api_response(run_id, str(event["id"]), 200, response, self._usage_from_response(response), 0)

    def _event(
        self,
        run_id: str,
        module: str,
        test_name: str,
        event_type: str,
        status: str,
        message: str,
        *,
        latency_ms: float = 0,
        tokens: dict[str, object] | None = None,
        cost: float = 0,
        request: dict[str, object] | None = None,
        response: dict[str, object] | None = None,
        error: str | None = None,
        recommendation: str = "",
    ) -> dict[str, object]:
        return self.repository.record_event(
            ObservabilityEventInput(
                run_id=run_id,
                provider="xai",
                module=module,
                test_name=test_name,
                event_type=event_type,
                status=status,
                message=message,
                latency_ms=latency_ms,
                tokens=tokens or {},
                cost=cost,
                request=request or {},
                response=response or {},
                error=error,
                recommendation=recommendation,
            )
        )

    def _safe_response(self, value: object) -> dict[str, object] | list[object] | str:
        if hasattr(value, "model_dump"):
            value = value.model_dump()
        try:
            return json.loads(json.dumps(value, default=str, ensure_ascii=False))
        except TypeError:
            return str(value)

    def _usage_from_response(self, response: dict[str, object]) -> dict[str, object]:
        raw = response.get("raw")
        if isinstance(raw, dict):
            usage = raw.get("usage")
            if isinstance(usage, dict):
                return usage
        return {}
