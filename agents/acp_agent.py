from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from core.algorithm_test_lab import AlgorithmTestRepository
from core.api_test_lab import ApiTestRepository
from core.config import get_settings
from core.database import build_engine, build_session_factory, init_db
from core.token_usage import TokenUsageRepository

from .acp_protocol import JsonRpcError, error_response, success_response
from .skill_executor import SkillExecutor, SkillExecutorServices


AVAILABLE_COMMANDS: list[dict[str, object]] = [
    {
        "name": "validate-api-suite",
        "description": "Valida uma suite de API em modo dry-run por padrão e exige permissão para HTTP real.",
        "input": {"hint": "whatsapp_validation_pack"},
    },
    {
        "name": "validate-algorithm",
        "description": "Executa uma suite determinística do Algorithm Test Lab e salva evidências.",
        "input": {"hint": "lead_score"},
    },
    {
        "name": "validate-lead-score",
        "description": "Executa a suite lead_score, verifica invariantes e exporta evidence pack.",
    },
    {
        "name": "token-cost",
        "description": "Calcula estimativa de uso/custo com fonte de pricing documentada.",
        "input": {"hint": "provider=xai model=grok-4.3 users=10 requests=20"},
    },
    {"name": "build-context", "description": "Gera contexto técnico a partir de logs e evidências."},
    {"name": "export-evidence", "description": "Exporta um pacote de evidências para revisão."},
]


@dataclass
class AcpSession:
    session_id: str
    cwd: str
    mcp_servers: list[dict[str, object]] = field(default_factory=list)
    cancelled: bool = False


class AcpAgent:
    def __init__(self, *, database_url: str | None = None, reports_dir: str | Path | None = None):
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.reports_dir = Path(reports_dir or settings.reports_dir)
        self.sessions: dict[str, AcpSession] = {}
        self.outbox: list[dict[str, object]] = []
        self._executor: SkillExecutor | None = None

    def handle_request(self, request: dict[str, object]) -> dict[str, object]:
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}
        try:
            if method == "initialize":
                return success_response(request_id, self.initialize())
            if method == "session/new":
                if not isinstance(params, dict):
                    return error_response(request_id, JsonRpcError.INVALID_PARAMS, "params must be an object")
                session = self.new_session(
                    cwd=str(params.get("cwd", "")),
                    mcp_servers=_normalize_mcp_servers(params.get("mcpServers", [])),
                )
                return success_response(
                    request_id,
                    {"sessionId": session.session_id, "_meta": _session_meta(session.session_id)},
                )
            if method == "session/prompt":
                if not isinstance(params, dict):
                    return error_response(request_id, JsonRpcError.INVALID_PARAMS, "params must be an object")
                return success_response(request_id, self.prompt(str(params.get("sessionId", "")), params.get("prompt", "")))
            if method == "session/cancel":
                if not isinstance(params, dict):
                    return error_response(request_id, JsonRpcError.INVALID_PARAMS, "params must be an object")
                result = self.cancel(str(params.get("sessionId", "")))
                if request_id is None:
                    return None
                return success_response(request_id, result)
            return error_response(request_id, JsonRpcError.METHOD_NOT_FOUND, f"Unknown method: {method}")
        except ValueError as exc:
            return error_response(request_id, JsonRpcError.INVALID_PARAMS, str(exc))
        except Exception as exc:  # noqa: BLE001 - JSON-RPC boundary
            return error_response(request_id, JsonRpcError.INTERNAL_ERROR, str(exc))

    def initialize(self) -> dict[str, object]:
        return {
            "protocolVersion": 1,
            "agentInfo": {"name": "apiforgekit-acp-skill-executor", "title": "APIForgeKit ACP Skill Executor", "version": "0.2.0"},
            "agentCapabilities": {
                "loadSession": False,
                "promptCapabilities": {"image": False, "audio": False, "embeddedContext": True},
                "mcpCapabilities": {"http": False, "sse": False},
            },
            "authMethods": [],
            "_meta": {"apiforgekit.supportsMcpStdio": True},
        }

    def new_session(self, *, cwd: str, mcp_servers: list[dict[str, object]]) -> AcpSession:
        if not cwd:
            raise ValueError("cwd is required")
        path = Path(cwd)
        if not path.is_absolute():
            raise ValueError("cwd must be absolute")
        session = AcpSession(session_id=str(uuid4()), cwd=str(path), mcp_servers=mcp_servers)
        self.sessions[session.session_id] = session
        self._notify(session.session_id, "available_commands_update", {"availableCommands": AVAILABLE_COMMANDS})
        return session

    def prompt(self, session_id: str, prompt: object) -> dict[str, object]:
        session = self._get_session(session_id)
        if session.cancelled:
            return {"stopReason": "cancelled", "message": "Session was cancelled.", "_meta": _session_meta(session_id)}
        try:
            prompt_text = _extract_prompt_text(prompt)
        except ValueError as exc:
            self._notify(
                session_id,
                "agent_message_chunk",
                {"content": _text_content(str(exc))},
            )
            return {"stopReason": "refusal", "_meta": _session_meta(session_id)}
        command = _command_name(prompt_text)
        plan_entries = _plan_for_prompt(prompt_text)
        self._notify(session_id, "plan", {"entries": plan_entries})
        self._notify(session_id, "plan", {"entries": _activate_plan_entry(plan_entries, 0)})
        if _requires_network_permission(prompt_text):
            permission = {
                "kind": "network",
                "reason": "HTTP real ou provider pago exige permissão antes de executar.",
                "command": prompt_text,
            }
            self._request_permission(session_id, permission)
            self._notify(
                session_id,
                "agent_message_chunk",
                {"content": _text_content("Permissão necessária antes de executar HTTP real ou provider pago.")},
            )
            return {"stopReason": "refusal", "_meta": _permission_meta(session_id, prompt_text, permission)}
        tool_call_id = str(uuid4())
        self._notify(
            session_id,
            "tool_call",
            {
                "toolCallId": tool_call_id,
                "title": f"APIForgeKit {command}",
                "kind": "execute",
                "status": "in_progress",
                "rawInput": {"command": prompt_text},
            },
        )
        result = self._get_executor().execute(prompt_text)
        if result.get("status") == "permission_required":
            permission = result.get("permission", {})
            permission_payload = permission if isinstance(permission, dict) else {}
            self._request_permission(session_id, permission_payload)
            self._notify(
                session_id,
                "tool_call_update",
                {
                    "toolCallId": tool_call_id,
                    "status": "failed",
                    "rawOutput": result,
                },
            )
            self._notify(
                session_id,
                "agent_message_chunk",
                {"content": _text_content("Permissão necessária antes de continuar a validação.")},
            )
            return {
                "stopReason": "refusal",
                "_meta": _permission_meta(session_id, prompt_text, permission_payload),
            }
        tool_status = "completed" if result.get("status") == "success" else "failed"
        self._notify(
            session_id,
            "tool_call_update",
            {
                "toolCallId": tool_call_id,
                "status": tool_status,
                "rawOutput": result,
            },
        )
        self._notify(
            session_id,
            "agent_message_chunk",
            {"content": _text_content(json.dumps(result, ensure_ascii=False))},
        )
        return {"stopReason": "end_turn", "_meta": _result_meta(session_id, command, result)}

    def cancel(self, session_id: str) -> dict[str, object]:
        session = self._get_session(session_id)
        session.cancelled = True
        self._notify(session_id, "agent_message_chunk", {"content": _text_content("Session cancelled.")})
        return {"cancelled": True, "_meta": _session_meta(session_id)}

    def _get_session(self, session_id: str) -> AcpSession:
        if session_id not in self.sessions:
            raise ValueError(f"Unknown sessionId: {session_id}")
        return self.sessions[session_id]

    def _get_executor(self) -> SkillExecutor:
        if self._executor is None:
            engine = build_engine(self.database_url)
            init_db(engine)
            session_factory = build_session_factory(engine)
            self._executor = SkillExecutor(
                SkillExecutorServices(
                    algorithm_repository=AlgorithmTestRepository(session_factory),
                    api_repository=ApiTestRepository(session_factory),
                    token_repository=TokenUsageRepository(session_factory),
                    reports_dir=self.reports_dir,
                    skill_path="SKILL.md",
                )
            )
        return self._executor

    def _notify(self, session_id: str, update_type: str, payload: dict[str, object]) -> None:
        self.outbox.append(
            {
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": session_id,
                    "update": {"sessionUpdate": update_type, **payload},
                    "_meta": _session_meta(session_id),
                },
            }
        )

    def _request_permission(self, session_id: str, permission: dict[str, object]) -> None:
        tool_call_id = str(uuid4())
        self.outbox.append(
            {
                "jsonrpc": "2.0",
                "id": f"permission-{uuid4()}",
                "method": "session/request_permission",
                "params": {
                    "sessionId": session_id,
                    "toolCall": {
                        "toolCallId": tool_call_id,
                        "title": "Executar validação externa",
                        "kind": "fetch",
                        "status": "pending",
                        "rawInput": permission,
                    },
                    "options": [
                        {"optionId": "allow_once", "kind": "allow_once", "name": "Permitir uma vez"},
                        {"optionId": "reject_once", "kind": "reject_once", "name": "Recusar"},
                    ],
                    "_meta": _session_meta(session_id),
                },
            }
        )


def run_stdio() -> None:
    agent = AcpAgent()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = agent.handle_request(request)
        except json.JSONDecodeError as exc:
            response = error_response(None, JsonRpcError.PARSE_ERROR, str(exc))
        for notification in agent.outbox:
            print(json.dumps(notification, ensure_ascii=False), flush=True)
        agent.outbox.clear()
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


def _normalize_mcp_servers(value: object) -> list[dict[str, object]]:
    if value is None:
        return []
    if isinstance(value, dict):
        iterable = value.values()
    elif isinstance(value, list):
        iterable = value
    else:
        raise ValueError("mcpServers must be an array or object")
    servers = []
    for item in iterable:
        if not isinstance(item, dict):
            raise ValueError("Each MCP server must be an object")
        if item.get("url") or item.get("transport") in {"http", "sse"}:
            raise ValueError("Only stdio MCP servers are supported in this version")
        servers.append(dict(item))
    return servers


def _plan_for_prompt(prompt: str) -> list[dict[str, str]]:
    command = _command_name(prompt)
    if command == "/validate-lead-score":
        steps = [
            "Classificar pedido como lead score",
            "Executar suite lead_score",
            "Verificar invariantes",
            "Exportar evidence pack",
        ]
    elif command == "/validate-algorithm":
        steps = ["Classificar pedido como algoritmo", "Executar suite", "Salvar evidência", "Exportar contexto"]
    elif command == "/validate-api-suite":
        steps = ["Classificar pedido como API", "Verificar permissão", "Executar dry-run", "Exportar contexto"]
    elif command == "/token-cost":
        steps = ["Classificar pedido como custo", "Calcular estimativa", "Registrar fonte de pricing"]
    else:
        steps = ["Aplicar gates do SKILL.md", "Retornar próximo passo seguro"]
    return [
        {
            "content": step,
            "priority": "high" if index == 0 else "medium",
            "status": "pending",
        }
        for index, step in enumerate(steps)
    ]


def _requires_network_permission(prompt: str) -> bool:
    return _command_name(prompt) == "/validate-api-suite" and "--http-real" in prompt


def _session_meta(session_id: str) -> dict[str, str]:
    return {"apiforgekit.sessionId": session_id}


def _result_meta(session_id: str, command: str, result: dict[str, object]) -> dict[str, object]:
    meta: dict[str, object] = {"apiforgekit.sessionId": session_id, "apiforgekit.command": command.lstrip("/")}
    run = result.get("run")
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    exports = result.get("exports") if isinstance(result.get("exports"), dict) else {}
    if isinstance(run, dict) and run.get("id"):
        meta["apiforgekit.runId"] = run["id"]
    if isinstance(evidence, dict):
        if evidence.get("run_id"):
            meta["apiforgekit.runId"] = evidence["run_id"]
        if evidence.get("algorithm"):
            meta["apiforgekit.algorithm"] = evidence["algorithm"]
    if isinstance(exports, dict):
        if exports.get("context"):
            meta["apiforgekit.contextPath"] = exports["context"]
        if exports.get("zip"):
            meta["apiforgekit.evidenceZip"] = exports["zip"]
    return meta


def _permission_meta(session_id: str, command_text: str, permission: dict[str, object]) -> dict[str, object]:
    command = _command_name(command_text).lstrip("/")
    return {
        "apiforgekit.sessionId": session_id,
        "apiforgekit.command": command,
        "apiforgekit.permissionRequired": True,
        "apiforgekit.blockedCommand": command_text,
        "apiforgekit.permissionKind": str(permission.get("kind", "unknown")),
        "apiforgekit.permissionReason": str(permission.get("reason", "")),
    }


def _text_content(text: str) -> dict[str, str]:
    return {"type": "text", "text": text}


def _extract_prompt_text(prompt: object) -> str:
    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, list):
        parts: list[str] = []
        unsupported: list[str] = []
        for block in prompt:
            if not isinstance(block, dict):
                unsupported.append(type(block).__name__)
                continue
            block_type = block.get("type")
            if block_type == "text":
                parts.append(str(block.get("text", "")))
            else:
                unsupported.append(str(block_type))
        if unsupported:
            raise ValueError("Apenas blocos de texto são suportados neste executor ACP local.")
        return "\n".join(part for part in parts if part.strip())
    raise ValueError("Prompt ACP inválido. Use string legada ou ContentBlock[] com type=text.")


def _command_name(prompt: str) -> str:
    raw = prompt.strip().split(" ", 1)[0] if prompt.strip() else "unknown"
    return raw if raw.startswith("/") else f"/{raw}"


def _activate_plan_entry(entries: list[dict[str, str]], active_index: int) -> list[dict[str, str]]:
    updated = []
    for index, entry in enumerate(entries):
        next_entry = dict(entry)
        next_entry["status"] = "in_progress" if index == active_index else "pending"
        updated.append(next_entry)
    return updated


if __name__ == "__main__":
    run_stdio()
