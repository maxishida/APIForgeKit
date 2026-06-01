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


AVAILABLE_COMMANDS: list[dict[str, str]] = [
    {
        "name": "/validate-api-suite",
        "description": "Valida uma suite de API em modo dry-run por padrão e exige permissão para HTTP real.",
    },
    {
        "name": "/validate-algorithm",
        "description": "Executa uma suite determinística do Algorithm Test Lab e salva evidências.",
    },
    {
        "name": "/token-cost",
        "description": "Calcula estimativa de uso/custo com fonte de pricing documentada.",
    },
    {"name": "/build-context", "description": "Gera contexto técnico a partir de logs e evidências."},
    {"name": "/export-evidence", "description": "Exporta um pacote de evidências para revisão."},
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
                return success_response(request_id, self.prompt(str(params.get("sessionId", "")), str(params.get("prompt", ""))))
            if method == "session/cancel":
                if not isinstance(params, dict):
                    return error_response(request_id, JsonRpcError.INVALID_PARAMS, "params must be an object")
                return success_response(request_id, self.cancel(str(params.get("sessionId", ""))))
            return error_response(request_id, JsonRpcError.METHOD_NOT_FOUND, f"Unknown method: {method}")
        except ValueError as exc:
            return error_response(request_id, JsonRpcError.INVALID_PARAMS, str(exc))
        except Exception as exc:  # noqa: BLE001 - JSON-RPC boundary
            return error_response(request_id, JsonRpcError.INTERNAL_ERROR, str(exc))

    def initialize(self) -> dict[str, object]:
        return {
            "protocolVersion": 1,
            "agent": {"name": "APIForgeKit ACP Skill Executor", "version": "0.1.0"},
            "agentCapabilities": {
                "loadSession": False,
                "promptCapabilities": {"image": False, "audio": False, "embeddedContext": True},
                "mcpCapabilities": {"stdio": True, "http": False, "sse": False},
            },
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

    def prompt(self, session_id: str, prompt: str) -> dict[str, object]:
        session = self._get_session(session_id)
        if session.cancelled:
            return {"stopReason": "cancelled", "message": "Session was cancelled.", "_meta": _session_meta(session_id)}
        self._notify(session_id, "plan", {"entries": _plan_for_prompt(prompt)})
        if _requires_network_permission(prompt):
            permission = {
                "kind": "network",
                "reason": "HTTP real ou provider pago exige permissão antes de executar.",
                "command": prompt,
            }
            self._request_permission(session_id, permission)
            return {"stopReason": "permission_required", "permission": permission, "_meta": _session_meta(session_id)}
        result = self._get_executor().execute(prompt)
        if result.get("status") == "permission_required":
            permission = result.get("permission", {})
            self._request_permission(session_id, permission if isinstance(permission, dict) else {})
            return {
                "stopReason": "permission_required",
                "permission": permission,
                "result": result,
                "_meta": _session_meta(session_id),
            }
        self._notify(
            session_id,
            "agent_message_chunk",
            {"content": _text_content(json.dumps(result, ensure_ascii=False))},
        )
        return {"stopReason": "end_turn", "result": result, "_meta": _session_meta(session_id)}

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
    command = prompt.strip().split(" ", 1)[0] if prompt.strip() else "unknown"
    if command == "/validate-algorithm":
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
            "status": "in_progress" if index == 0 else "pending",
        }
        for index, step in enumerate(steps)
    ]


def _requires_network_permission(prompt: str) -> bool:
    return prompt.strip().startswith("/validate-api-suite") and "--http-real" in prompt


def _session_meta(session_id: str) -> dict[str, str]:
    return {"apiforgekit.sessionId": session_id}


def _text_content(text: str) -> dict[str, str]:
    return {"type": "text", "text": text}


if __name__ == "__main__":
    run_stdio()
