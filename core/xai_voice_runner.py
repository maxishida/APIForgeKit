from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

from core.config import ROOT_DIR
from core.observability import ObservabilityEventInput, ObservabilityRepository


XAI_TTS_URL = "https://api.x.ai/v1/tts"
XAI_STT_URL = "https://api.x.ai/v1/stt"
DEFAULT_VOICE_ID = "eve"
DEFAULT_TTS_LANGUAGE = "en"
DEFAULT_STT_LANGUAGE = "en"
DEFAULT_VOICE_MODEL = "grok-4.3"

VOICE_LOG_EVENT_TYPES = (
    "lead_received",
    "user_message_received",
    "tts_request_started",
    "tts_audio_received",
    "stt_request_started",
    "transcript_received",
    "agent_response_request_started",
    "agent_response_received",
    "voice_call_completed",
    "api_error",
)


@dataclass(frozen=True)
class VoiceLeadInput:
    lead_name: str
    user_message: str
    origin: str
    previous_page: str = ""
    voice_id: str = DEFAULT_VOICE_ID
    tts_language: str = DEFAULT_TTS_LANGUAGE
    stt_language: str = DEFAULT_STT_LANGUAGE

    def to_log_payload(self, *, evidence_mode: str = "real_http") -> dict[str, object]:
        return {
            "lead_name": self.lead_name,
            "user_message": self.user_message,
            "origin": self.origin,
            "previous_page": self.previous_page,
            "voice_id": self.voice_id,
            "tts_language": self.tts_language,
            "stt_language": self.stt_language,
            "evidence_mode": evidence_mode,
        }


class XaiVoiceApiError(RuntimeError):
    def __init__(self, endpoint: str, status_code: int, body: str):
        super().__init__(f"{endpoint} failed with HTTP {status_code}: {body[:500]}")
        self.endpoint = endpoint
        self.status_code = status_code
        self.body = body[:2000]


class XaiVoiceRunner:
    def __init__(
        self,
        repository: ObservabilityRepository,
        *,
        output_dir: str | Path,
        api_key: str | None = None,
        model: str | None = None,
        http_post: Callable[..., Any] | None = None,
        agent_responder: Callable[[str, VoiceLeadInput], str] | None = None,
        load_env: bool = True,
    ):
        if load_env:
            load_dotenv(ROOT_DIR / ".env")
        self.repository = repository
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key if api_key is not None else os.getenv("XAI_API_KEY") or ""
        self.model = model or os.getenv("XAI_MODEL") or DEFAULT_VOICE_MODEL
        self.http_post = http_post or _requests_post
        self.agent_responder = agent_responder

    def run_roundtrip(self, lead: VoiceLeadInput) -> dict[str, object]:
        run = self.repository.start_run(
            "xai",
            "voice_roundtrip",
            ["lead_input", "tts", "stt", "agent_response", "voice_status"],
        )
        run_id = str(run["id"])
        started = time.perf_counter()
        try:
            input_evidence_mode = "real_http" if self.api_key else "blocked"
            self._record_lead_input(run_id, lead, evidence_mode=input_evidence_mode)
            if not self.api_key:
                raise XaiVoiceApiError("readiness", 0, "XAI_API_KEY ausente no .env local")

            audio_path, audio_bytes, tts_latency = self._run_tts(run_id, lead)
            transcript_payload, stt_latency = self._run_stt(run_id, lead, audio_path)
            transcript = str(transcript_payload.get("text") or "").strip()
            classification = _classify_transcript(transcript, lead)
            agent_response, agent_latency = self._run_agent_response(run_id, lead, transcript)

            total_latency = round((time.perf_counter() - started) * 1000, 2)
            metrics = {
                "tts_latency_ms": tts_latency,
                "stt_latency_ms": stt_latency,
                "agent_latency_ms": agent_latency,
                "total_latency_ms": total_latency,
                "audio_bytes": len(audio_bytes),
                "duration_seconds": transcript_payload.get("duration", 0),
                "origin": lead.origin,
                "previous_page": lead.previous_page,
            }
            self.repository.record_voice_test(
                run_id,
                audio_artifact=str(audio_path),
                transcript=transcript,
                classification=classification,
                metrics=metrics,
                status="success",
            )
            self._event(
                run_id,
                "voice_call_completed",
                "success",
                "Status da chamada/voz: concluída",
                latency_ms=total_latency,
                request=lead.to_log_payload(),
                response={
                    "transcript": transcript,
                    "classification": classification,
                    "agent_response": agent_response,
                    "metrics": metrics,
                    "evidence_mode": "real_http",
                },
                recommendation="Usar estes logs para definir UX de voz, SLA, retries e handoff humano.",
            )
            return self.repository.finish_run(
                run_id,
                "success",
                {
                    "lead_name": lead.lead_name,
                    "origin": lead.origin,
                    "previous_page": lead.previous_page,
                    "classification": classification,
                    "transcript_chars": len(transcript),
                    "agent_response_chars": len(agent_response),
                    "voice_status": "success",
                },
            )
        except Exception as exc:  # noqa: BLE001 - every failure must become evidence
            safe_error = _redact(str(exc), self.api_key)
            is_readiness_block = isinstance(exc, XaiVoiceApiError) and exc.endpoint == "readiness"
            final_status = "blocked" if is_readiness_block else "failed"
            evidence_mode = "blocked" if is_readiness_block else "real_http"
            self.repository.record_voice_test(run_id, status=final_status, error=safe_error)
            self._event(
                run_id,
                "api_error",
                final_status,
                "Erro de API registrado no Voice Lab",
                request={**lead.to_log_payload(), "evidence_mode": evidence_mode},
                response={"evidence_mode": evidence_mode},
                error=safe_error,
                recommendation=(
                    "Configurar XAI_API_KEY no .env local antes de repetir o roundtrip."
                    if is_readiness_block
                    else "Corrigir credenciais/payload conforme docs xAI e repetir o roundtrip."
                ),
            )
            return self.repository.finish_run(
                run_id,
                final_status,
                {
                    "lead_name": lead.lead_name,
                    "origin": lead.origin,
                    "previous_page": lead.previous_page,
                    "voice_status": final_status,
                    "error": safe_error,
                },
            )

    def _record_lead_input(self, run_id: str, lead: VoiceLeadInput, *, evidence_mode: str) -> None:
        self._event(
            run_id,
            "lead_received",
            "success",
            "Lead recebido",
            request=lead.to_log_payload(evidence_mode=evidence_mode),
            response={"accepted": True, "evidence_mode": evidence_mode},
            recommendation="Persistir origem e página anterior para atribuição do funil.",
        )
        self._event(
            run_id,
            "user_message_received",
            "success",
            "Mensagem enviada pelo usuário",
            request=lead.to_log_payload(evidence_mode=evidence_mode),
            response={"message_chars": len(lead.user_message), "evidence_mode": evidence_mode},
            recommendation="Usar esta mensagem como entrada canônica do fluxo de voz.",
        )

    def _run_tts(self, run_id: str, lead: VoiceLeadInput) -> tuple[Path, bytes, float]:
        payload = {
            "text": lead.user_message,
            "voice_id": lead.voice_id,
            "language": lead.tts_language,
        }
        started = self._api_start(run_id, "tts", "tts_synthesis", XAI_TTS_URL, {**lead.to_log_payload(), **payload})
        response = self.http_post(
            XAI_TTS_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        if int(getattr(response, "status_code", 0)) >= 400:
            raise XaiVoiceApiError("tts", int(response.status_code), _response_text(response))
        audio_bytes = bytes(getattr(response, "content", b"") or b"")
        if not audio_bytes:
            raise XaiVoiceApiError("tts", int(getattr(response, "status_code", 0)), "Resposta TTS sem bytes de áudio")
        latency = round((time.perf_counter() - started) * 1000, 2)
        audio_path = self.output_dir / f"xai_voice_{run_id}.mp3"
        audio_path.write_bytes(audio_bytes)
        event = self._event(
            run_id,
            "tts_audio_received",
            "success",
            "Status da chamada/voz: áudio TTS recebido",
            latency_ms=latency,
            request={**lead.to_log_payload(), "endpoint": XAI_TTS_URL, "text_chars": len(lead.user_message)},
            response={"audio_artifact": str(audio_path), "audio_bytes": len(audio_bytes), "evidence_mode": "real_http"},
            recommendation="TTS validado; usar o artefato gerado como fixture local temporária para STT.",
        )
        self.repository.record_api_response(run_id, str(event["id"]), 200, {"audio_bytes": len(audio_bytes)}, {}, 0)
        return audio_path, audio_bytes, latency

    def _run_stt(self, run_id: str, lead: VoiceLeadInput, audio_path: Path) -> tuple[dict[str, object], float]:
        started = self._api_start(
            run_id,
            "stt",
            "stt_transcription",
            XAI_STT_URL,
            {**lead.to_log_payload(), "audio_artifact": str(audio_path), "format": True},
        )
        with audio_path.open("rb") as audio_file:
            response = self.http_post(
                XAI_STT_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data=[("format", "true"), ("language", lead.stt_language), ("keyterm", "APIForgeKit")],
                files={"file": (audio_path.name, audio_file, "audio/mpeg")},
                timeout=90,
            )
        if int(getattr(response, "status_code", 0)) >= 400:
            raise XaiVoiceApiError("stt", int(response.status_code), _response_text(response))
        payload = _response_json(response)
        transcript = str(payload.get("text") or "")
        latency = round((time.perf_counter() - started) * 1000, 2)
        event = self._event(
            run_id,
            "transcript_received",
            "success",
            "Status da chamada/voz: transcrição recebida",
            latency_ms=latency,
            request={**lead.to_log_payload(), "endpoint": XAI_STT_URL, "audio_artifact": str(audio_path)},
            response={
                "transcript": transcript,
                "language": payload.get("language", ""),
                "duration": payload.get("duration", 0),
                "words_count": len(payload.get("words") or []),
                "evidence_mode": "real_http",
            },
            recommendation="Validar intenção e classificar lead a partir da transcrição.",
        )
        self.repository.record_api_response(run_id, str(event["id"]), 200, _safe_json(payload), {}, 0)
        return payload, latency

    def _run_agent_response(self, run_id: str, lead: VoiceLeadInput, transcript: str) -> tuple[str, float]:
        request = {
            **lead.to_log_payload(),
            "model": self.model,
            "transcript": transcript,
            "instruction": "Responder como agente de atendimento de vendas em uma frase.",
        }
        started = self._api_start(run_id, "agent_response", "voice_agent_reply", "xai_sdk.chat", request)
        if self.agent_responder is not None:
            response_text = self.agent_responder(transcript, lead)
        else:
            response_text = self._call_xai_text_agent(transcript, lead)
        latency = round((time.perf_counter() - started) * 1000, 2)
        event = self._event(
            run_id,
            "agent_response_received",
            "success",
            "Resposta do agente recebida",
            latency_ms=latency,
            request=request,
            response={"agent_response": response_text, "evidence_mode": "real_http"},
            recommendation="Usar resposta do agente como baseline para handoff, follow-up e próxima ação.",
        )
        self.repository.record_api_response(run_id, str(event["id"]), 200, {"agent_response": response_text}, {}, 0)
        return response_text, latency

    def _call_xai_text_agent(self, transcript: str, lead: VoiceLeadInput) -> str:
        from xai_sdk import Client
        from xai_sdk.chat import system, user

        client = Client(api_key=self.api_key)
        chat = client.chat.create(model=self.model)
        chat.append(system("Você é um agente de vendas. Responda em português, em uma frase, com a próxima ação recomendada."))
        chat.append(
            user(
                "Lead: {lead}. Origem: {origin}. Página anterior: {page}. Transcrição: {transcript}".format(
                    lead=lead.lead_name,
                    origin=lead.origin,
                    page=lead.previous_page or "desconhecida",
                    transcript=transcript,
                )
            )
        )
        response = chat.sample()
        return str(getattr(response, "content", "") or "").strip()

    def _api_start(self, run_id: str, module: str, test_name: str, endpoint: str, payload: dict[str, object]) -> float:
        started = time.perf_counter()
        event = self._event(
            run_id,
            f"{module}_request_started",
            "running",
            "xAI Voice Request Started",
            request={**payload, "endpoint": endpoint},
            response={"evidence_mode": "real_http"},
        )
        self.repository.record_api_request(run_id, str(event["id"]), "xai", test_name, endpoint, payload)
        return started

    def _event(
        self,
        run_id: str,
        event_type: str,
        status: str,
        message: str,
        *,
        latency_ms: float = 0,
        request: dict[str, object] | None = None,
        response: dict[str, object] | None = None,
        error: str | None = None,
        recommendation: str = "",
    ) -> dict[str, object]:
        return self.repository.record_event(
            ObservabilityEventInput(
                run_id=run_id,
                provider="xai",
                module="voice",
                test_name="voice_roundtrip",
                event_type=event_type,
                status=status,
                message=message,
                latency_ms=latency_ms,
                request=request or {"evidence_mode": "real_http"},
                response=response or {"evidence_mode": "real_http"},
                error=error,
                recommendation=recommendation,
            )
        )


def _requests_post(url: str, **kwargs: object) -> object:
    import requests

    return requests.post(url, **kwargs)


def _response_text(response: object) -> str:
    text = str(getattr(response, "text", "") or "")
    if text:
        return text
    content = getattr(response, "content", b"") or b""
    if isinstance(content, bytes):
        return content[:1000].decode("utf-8", errors="replace")
    return str(content)


def _response_json(response: object) -> dict[str, object]:
    try:
        payload = response.json()
    except Exception as exc:  # noqa: BLE001 - response body becomes evidence
        raise XaiVoiceApiError("stt", int(getattr(response, "status_code", 0)), f"Resposta JSON inválida: {exc}") from exc
    return _safe_json(payload)


def _safe_json(value: object) -> dict[str, object]:
    try:
        parsed = json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except TypeError:
        return {"value": str(value)}
    return parsed if isinstance(parsed, dict) else {"value": parsed}


def _classify_transcript(transcript: str, lead: VoiceLeadInput) -> str:
    text = f"{transcript} {lead.user_message} {lead.origin}".lower()
    sales_terms = ("buy", "comprar", "orçamento", "budget", "price", "preço", "whatsapp", "today", "hoje", "urgent", "urgente")
    if any(term in text for term in sales_terms):
        return "sales_intent"
    if any(term in text for term in ("support", "suporte", "problem", "erro", "issue")):
        return "support_intent"
    return "general_intent"


def _redact(value: str, secret: str) -> str:
    redacted = value
    if secret:
        redacted = redacted.replace(secret, "[REDACTED_XAI_API_KEY]")
    return redacted.replace("Bearer ", "Bearer [REDACTED] ")
