from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


GENERATED_START = "<!-- @generated:start -->"
GENERATED_END = "<!-- @generated:end -->"
MANIFEST_NAME = ".apiforgekit-vault-manifest.json"
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


@dataclass(frozen=True)
class NoteSpec:
    relative_path: str
    title: str
    note_type: str
    area: str
    body: Callable[[dict[str, object]], str]
    user_section: str = ""


def build_repository_snapshot(repo_root: Path) -> dict[str, object]:
    root = repo_root.resolve()
    return {
        "branch": _git_value(root, "branch", "--show-current"),
        "commit": _git_value(root, "rev-parse", "--short", "HEAD"),
        "latest_subject": _git_value(root, "log", "-1", "--pretty=%s"),
        "documents": _document_catalog(root),
        "modules": _module_catalog(root),
        "validation_command": "npm test",
        "mvp_command": "npm run validate:mvp",
    }


def sync_vault(*, vault_path: Path, repo_root: Path) -> dict[str, object]:
    vault = vault_path.expanduser()
    if not vault.is_dir():
        return _error_result(f"Vault directory does not exist: {vault}")

    snapshot = build_repository_snapshot(repo_root)
    result: dict[str, object] = {
        "status": "ok",
        "created": [],
        "updated": [],
        "preserved": [],
        "skipped": [],
        "manifest_path": str(vault / MANIFEST_NAME),
    }
    _ensure_directories(vault)

    for spec in _note_specs():
        outcome = _upsert_note(vault / spec.relative_path, _render_note(spec, snapshot))
        result[outcome].append(spec.relative_path)

    manifest = _manifest(snapshot)
    _write_if_changed(vault / MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return result


def validate_vault(*, vault_path: Path) -> dict[str, object]:
    vault = vault_path.expanduser()
    if not vault.is_dir():
        return {"valid": False, "error": f"Vault directory does not exist: {vault}", "broken_links": []}

    notes = sorted(vault.rglob("*.md"))
    known_targets = _known_targets(vault, notes)
    broken_links: set[str] = set()

    for note in notes:
        for raw_target in WIKILINK_PATTERN.findall(note.read_text(encoding="utf-8")):
            target = raw_target.split("|", 1)[0].split("#", 1)[0].strip()
            if target and target not in known_targets:
                broken_links.add(target)

    return {
        "valid": not broken_links,
        "note_count": len(notes),
        "broken_links": sorted(broken_links),
        "canonical_missing": [
            spec.title
            for spec in _note_specs()
            if not (vault / spec.relative_path).exists()
        ],
    }


def _error_result(message: str) -> dict[str, object]:
    return {"status": "error", "error": message, "created": [], "updated": [], "preserved": [], "skipped": []}


def _ensure_directories(vault: Path) -> None:
    for relative in (
        "01 - Inbox",
        "02 - Projetos/ApiContextbuilder",
        "03 - Areas",
        "04 - Recursos",
        "05 - Arquivo",
        "06 - Engenharia/Gerado",
        "07 - Prompts",
        "08 - Logs",
        "09 - Tickets",
        "10 - Decisões",
        "99 - Templates",
    ):
        (vault / relative).mkdir(parents=True, exist_ok=True)


def _upsert_note(path: Path, rendered: str) -> str:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        return "created"

    existing = path.read_text(encoding="utf-8")
    if GENERATED_START not in existing or GENERATED_END not in existing:
        return "preserved"

    merged = _replace_generated(existing, _generated_block(_extract_generated_content(rendered)))
    if merged == existing:
        return "skipped"
    path.write_text(merged, encoding="utf-8")
    return "updated"


def _render_note(spec: NoteSpec, snapshot: dict[str, object]) -> str:
    frontmatter = "\n".join(
        (
            "---",
            f"tipo: {spec.note_type}",
            "status: ativo",
            f"area: {spec.area}",
            "projeto: ApiContextbuilder",
            "tags:",
            "  - api-contextbuilder",
            "  - second-brain",
            "source: APIForgeKit",
            "---",
            "",
            f"# {spec.title}",
            "",
        )
    )
    return f"{frontmatter}{_generated_block(spec.body(snapshot))}\n{spec.user_section}"


def _generated_block(content: str) -> str:
    return f"{GENERATED_START}\n{content.strip()}\n{GENERATED_END}\n"


def _extract_generated_content(rendered: str) -> str:
    start = rendered.index(GENERATED_START) + len(GENERATED_START)
    end = rendered.index(GENERATED_END, start)
    return rendered[start:end].strip()


def _replace_generated(existing: str, generated_block: str) -> str:
    start = existing.index(GENERATED_START)
    end = existing.index(GENERATED_END, start) + len(GENERATED_END)
    return f"{existing[:start]}{generated_block.rstrip()}{existing[end:]}"


def _write_if_changed(path: Path, content: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def _manifest(snapshot: dict[str, object]) -> dict[str, object]:
    source = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    return {
        "source_commit": snapshot["commit"],
        "fingerprint": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "source_documents": [item["path"] for item in snapshot["documents"]],
        "generated_notes": [spec.relative_path for spec in _note_specs()],
    }


def _document_catalog(repo_root: Path) -> list[dict[str, str]]:
    candidates = [repo_root / "README.md", repo_root / "SKILL.md", *sorted((repo_root / "docs").rglob("*.md"))]
    catalog: list[dict[str, str]] = []
    for path in candidates:
        if not path.is_file():
            continue
        relative = path.relative_to(repo_root).as_posix()
        if relative.startswith("docs/superpowers/"):
            continue
        content = path.read_text(encoding="utf-8")
        catalog.append(
            {
                "path": relative,
                "title": _first_heading(content) or path.stem,
                "digest": hashlib.sha256(content.encode("utf-8")).hexdigest()[:12],
            }
        )
    return catalog


def _module_catalog(repo_root: Path) -> dict[str, list[str]]:
    catalog: dict[str, list[str]] = {}
    for name in ("agents", "core", "ui", "scripts", "tests"):
        directory = repo_root / name
        if directory.is_dir():
            catalog[name] = sorted(
                path.name
                for path in directory.iterdir()
                if path.is_file() and path.suffix in {".py", ".js", ".ps1", ".sh"}
            )
    return catalog


def _first_heading(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _git_value(repo_root: Path, *args: str) -> str:
    override_name = {
        ("branch", "--show-current"): "APIFORGEKIT_GIT_BRANCH",
        ("rev-parse", "--short", "HEAD"): "APIFORGEKIT_GIT_COMMIT",
        ("log", "-1", "--pretty=%s"): "APIFORGEKIT_GIT_SUBJECT",
    }.get(args)
    if override_name and os.environ.get(override_name):
        return str(os.environ[override_name])

    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _known_targets(vault: Path, notes: list[Path]) -> set[str]:
    targets: set[str] = set()
    for note in notes:
        targets.add(note.stem)
        targets.add(note.relative_to(vault).with_suffix("").as_posix())
    return targets


def _note_specs() -> list[NoteSpec]:
    return [
        _spec("00 - Mapa do Projeto.md", "00 - Mapa do Projeto", "hub", "navegação", _project_map, "## Notas da sessão\n\n- [ ] Registre aqui a próxima conversa importante.\n"),
        _spec("00 - Retomar Agora.md", "00 - Retomar Agora", "status", "operação", _resume_note, "## Notas da sessão\n\n- [ ] Registre onde a conversa foi interrompida.\n"),
        _spec("AGENTS.md", "AGENTS.md", "guide", "agentes", _agents_note),
        _spec("02 - Projetos/ApiContextbuilder/Visão Geral do Projeto.md", "Visão Geral do Projeto", "project", "produto", _overview_note),
        _spec("02 - Projetos/ApiContextbuilder/MVP Inicial.md", "MVP Inicial", "scope", "produto", _mvp_note),
        _spec("03 - Areas/SDD - Spec Driven Development.md", "SDD - Spec Driven Development", "method", "engenharia", _sdd_note),
        _spec("03 - Areas/STB - Software Technical Blueprint.md", "STB - Software Technical Blueprint", "method", "engenharia", _stb_note),
        _spec("03 - Areas/ACP - AI Collaboration Protocol.md", "ACP - AI Collaboration Protocol", "protocol", "agentes", _acp_note),
        _spec("03 - Areas/PREVC.md", "PREVC", "workflow", "operação", _prevc_note),
        _spec("04 - Recursos/Memória Operacional.md", "Memória Operacional", "memory", "conhecimento", _memory_note),
        _spec("04 - Recursos/Referências Externas.md", "Referências Externas", "reference", "pesquisa", _references_note),
        _spec("04 - Recursos/Guia do Grafo.md", "Guia do Grafo", "guide", "navegação", _graph_note),
        _spec("06 - Engenharia/Arquitetura do Sistema.md", "Arquitetura do Sistema", "architecture", "engenharia", _architecture_note),
        _spec("06 - Engenharia/Algorithm Test Lab.md", "Algorithm Test Lab", "module", "engenharia", _algorithm_lab_note),
        _spec("06 - Engenharia/Generic API Lab.md", "Generic API Lab", "module", "engenharia", _api_lab_note),
        _spec("06 - Engenharia/Context Builder.md", "Context Builder", "module", "engenharia", _context_builder_note),
        _spec("06 - Engenharia/ACP Skill Executor.md", "ACP Skill Executor", "module", "agentes", _acp_executor_note),
        _spec("06 - Engenharia/Gerado/APIForgeKit - Snapshot de Arquitetura.md", "APIForgeKit - Snapshot de Arquitetura", "generated", "engenharia", _architecture_snapshot),
        _spec("06 - Engenharia/Gerado/Documentação Ativa.md", "Documentação Ativa", "generated", "documentação", _documentation_snapshot),
        _spec("07 - Prompts/Prompts Operacionais.md", "Prompts Operacionais", "prompt", "agentes", _prompts_note),
        _spec("08 - Logs/Logs de Evolução.md", "Logs de Evolução", "log", "operação", _logs_note),
        _spec("09 - Tickets/Backlog Geral.md", "Backlog Geral", "backlog", "planejamento", _backlog_note),
        _spec("09 - Tickets/Tickets Ativos.md", "Tickets Ativos", "ticket", "planejamento", _tickets_note),
        _spec("10 - Decisões/Decisões Técnicas.md", "Decisões Técnicas", "decision", "arquitetura", _decisions_note),
        _spec("99 - Templates/Template - Nota Operacional.md", "Template - Nota Operacional", "template", "navegação", _note_template),
        _spec("99 - Templates/Template - Decisão.md", "Template - Decisão", "template", "arquitetura", _decision_template),
    ]


def _spec(relative_path: str, title: str, note_type: str, area: str, body: Callable[[dict[str, object]], str], user_section: str = "") -> NoteSpec:
    return NoteSpec(relative_path, title, note_type, area, body, user_section)


def _sections(objective: str, context: str, content: list[str], actions: list[str]) -> str:
    return "\n".join(
        [
            "## Objetivo",
            objective,
            "",
            "## Contexto",
            context,
            "",
            "## Conteúdo principal",
            *content,
            "",
            "## Próximas ações",
            *[f"- [ ] {action}" for action in actions],
        ]
    )


def _project_map(_: dict[str, object]) -> str:
    links = [
        "Visão Geral do Projeto", "MVP Inicial", "SDD - Spec Driven Development", "STB - Software Technical Blueprint",
        "ACP - AI Collaboration Protocol", "PREVC", "Arquitetura do Sistema", "Algorithm Test Lab",
        "Generic API Lab", "Context Builder", "ACP Skill Executor", "Backlog Geral", "Tickets Ativos",
        "Decisões Técnicas", "Logs de Evolução", "Prompts Operacionais", "Memória Operacional",
        "Referências Externas", "Guia do Grafo",
    ]
    return _sections(
        "Centralizar a navegação do cérebro operacional.",
        "Abra esta nota para explorar o grafo. Para retomar uma sessão, abra primeiro [[00 - Retomar Agora]].",
        ["## Domínios principais", *[f"- [[{link}]]" for link in links]],
        ["Abra [[00 - Retomar Agora]] antes de iniciar uma sessão."],
    )


def _resume_note(snapshot: dict[str, object]) -> str:
    docs = [f"- [[Documentação Ativa]]: {item['path']}" for item in snapshot["documents"][:8]]
    return _sections(
        "Mostrar a referência confiável para retomar trabalho humano ou de IA.",
        "A parte gerada é atualizada pelo sync. A seção Notas da sessão pertence ao usuário.",
        [
            "## Estado do repositório",
            f"- Branch: {snapshot['branch']}",
            f"- Commit: {snapshot['commit']}",
            f"- Último commit: {snapshot['latest_subject']}",
            "",
            "## Validação recomendada",
            f"- {snapshot['validation_command']}",
            f"- {snapshot['mvp_command']}",
            "",
            "## Documentação para retomar",
            *docs,
            "",
            "## Próxima ação recomendada",
            "- Leia [[00 - Mapa do Projeto]], depois [[APIForgeKit - Snapshot de Arquitetura]] e [[Tickets Ativos]].",
            "",
            "## Links relacionados",
            "- [[00 - Mapa do Projeto]]",
            "- [[APIForgeKit - Snapshot de Arquitetura]]",
            "- [[Documentação Ativa]]",
            "- [[Logs de Evolução]]",
            "- [[Tickets Ativos]]",
        ],
        ["Registre decisão ou interrupção antes de fechar a sessão."],
    )


def _agents_note(_: dict[str, object]) -> str:
    return _sections(
        "Orientar agentes que usam este vault como memória operacional.",
        "O vault complementa o repositório; código, testes e evidência executável permanecem no APIForgeKit.",
        [
            "## Regras",
            "- Leia [[00 - Retomar Agora]] e [[00 - Mapa do Projeto]] antes de sugerir trabalho.",
            "- Use PREVC: planejamento, revisão, execução, validação e confirmação.",
            "- Conecte cada nota nova a um hub existente.",
            "- Registre decisões em [[Decisões Técnicas]] e sessões em [[Logs de Evolução]].",
            "- Não apague, mova ou renomeie notas sem plano explícito.",
            "- Não altere texto fora dos marcadores gerados.",
        ],
        ["Atualizar esta orientação quando o fluxo operacional mudar."],
    )


def _overview_note(_: dict[str, object]) -> str:
    return _sections(
        "Explicar o propósito do APIForgeKit Studio.",
        "O projeto é um laboratório local-first para validar APIs, algoritmos e custos antes de pedir implementação a IA.",
        [
            "## Fluxo canônico",
            "Teste -> Log estruturado -> PostgreSQL -> Dashboard -> Context Builder -> Evidence Pack -> IA implementa depois.",
            "## Links relacionados",
            "- [[MVP Inicial]]",
            "- [[Arquitetura do Sistema]]",
            "- [[PREVC]]",
        ],
        ["Manter alinhado ao README do repositório."],
    )


def _mvp_note(_: dict[str, object]) -> str:
    return _sections(
        "Delimitar o escopo funcional atual.",
        "O MVP prioriza validação, observabilidade e contexto técnico reutilizável.",
        [
            "## Módulos reais",
            "- [[Algorithm Test Lab]]",
            "- [[Generic API Lab]]",
            "- [[Context Builder]]",
            "- [[ACP Skill Executor]]",
            "## Links relacionados",
            "- [[Visão Geral do Projeto]]",
            "- [[Backlog Geral]]",
        ],
        ["Registrar novas promessas de produto em [[Decisões Técnicas]]."],
    )


def _sdd_note(_: dict[str, object]) -> str:
    return _sections(
        "Registrar o uso de Spec Driven Development.",
        "Mudanças relevantes começam por requisito, desenho, plano, teste e evidência.",
        ["## Prática", "- Especificar comportamento e critérios de aceitação.", "- Registrar evidência em [[Logs de Evolução]].", "## Links relacionados", "- [[STB - Software Technical Blueprint]]", "- [[PREVC]]", "- [[Tickets Ativos]]"],
        ["Criar especificação para mudança de arquitetura ou novo lab."],
    )


def _stb_note(_: dict[str, object]) -> str:
    return _sections(
        "Converter intenção em blueprint técnico verificável.",
        "O STB descreve módulos, entradas, saídas, limites, testes e evidências antes da implementação.",
        ["## Links relacionados", "- [[Arquitetura do Sistema]]", "- [[SDD - Spec Driven Development]]", "- [[Context Builder]]"],
        ["Anexar blueprints a tickets e decisões relacionadas."],
    )


def _acp_note(_: dict[str, object]) -> str:
    return _sections(
        "Descrever a colaboração via ACP.",
        "ACP executa validação e contexto; não gera código de produto sem evidência.",
        ["## Regras", "- Ler [[00 - Retomar Agora]] e [[PREVC]].", "- Caminhos pagos ou HTTP real exigem permissão.", "## Links relacionados", "- [[ACP Skill Executor]]", "- [[Prompts Operacionais]]", "- [[Context Builder]]"],
        ["Registrar alteração de protocolo em [[Decisões Técnicas]]."],
    )


def _prevc_note(_: dict[str, object]) -> str:
    return _sections(
        "Padronizar Planejamento, Revisão, Execução, Validação e Confirmação.",
        "PREVC reduz retrabalho e torna mudanças rastreáveis.",
        ["## Ciclo", "1. Planejamento", "2. Revisão", "3. Execução", "4. Validação", "5. Confirmação", "## Links relacionados", "- [[Tickets Ativos]]", "- [[Logs de Evolução]]", "- [[Decisões Técnicas]]"],
        ["Aplicar PREVC a tickets que alterem comportamento ou integrações."],
    )


def _memory_note(_: dict[str, object]) -> str:
    return _sections(
        "Guardar aprendizados que evitam repetição de trabalho.",
        "Memória operacional conecta decisões, incidentes, validações e padrões.",
        ["## Regra de ouro", "- Evidência antes de implementação.", "## Links relacionados", "- [[Decisões Técnicas]]", "- [[Logs de Evolução]]", "- [[Context Builder]]"],
        ["Promover aprendizados recorrentes para esta nota."],
    )


def _references_note(_: dict[str, object]) -> str:
    return _sections(
        "Centralizar fontes externas relevantes.",
        "Referências distinguem comportamento documentado de hipótese.",
        ["## Fonte inicial", "- https://github.com/eugeniughelbur/obsidian-second-brain", "## Links relacionados", "- [[Documentação Ativa]]", "- [[ACP - AI Collaboration Protocol]]"],
        ["Registrar URL, data de consulta e impacto técnico."],
    )


def _graph_note(_: dict[str, object]) -> str:
    return _sections(
        "Explicar como navegar o grafo sem links artificiais.",
        "Use Graph View global para clusters e grafo local para decisões, tickets ou módulos.",
        ["## Hubs", "- [[00 - Mapa do Projeto]] é o hub global.", "- [[00 - Retomar Agora]] conecta a sessão ao estado atual.", "- [[Arquitetura do Sistema]], [[PREVC]], [[Decisões Técnicas]] e [[Logs de Evolução]] formam o cluster operacional."],
        ["Abra o Graph View e selecione [[00 - Mapa do Projeto]]."],
    )


def _architecture_note(_: dict[str, object]) -> str:
    return _sections(
        "Registrar a arquitetura local-first.",
        "NiceGUI apresenta labs; SQLAlchemy persiste no PostgreSQL; ACP executa a skill; Context Builder gera evidência.",
        ["## Fluxo", "SKILL.md -> ACP -> Labs -> PostgreSQL -> Dashboard e Logs -> Context Builder -> Evidence Pack.", "## Links relacionados", "- [[APIForgeKit - Snapshot de Arquitetura]]", "- [[Algorithm Test Lab]]", "- [[Generic API Lab]]", "- [[Context Builder]]", "- [[ACP Skill Executor]]"],
        ["Sincronizar após mudanças nos módulos ou fluxo."],
    )


def _algorithm_lab_note(_: dict[str, object]) -> str:
    return _sections(
        "Validar regras determinísticas antes de implementação futura.",
        "O lead_score compara entrada, expected, actual, diff e invariantes.",
        ["## Evidência", "- Suite canônica com 17 casos.", "## Links relacionados", "- [[MVP Inicial]]", "- [[Context Builder]]", "- [[Backlog Geral]]"],
        ["Registrar novos algoritmos como tickets antes de adicionar suites."],
    )


def _api_lab_note(_: dict[str, object]) -> str:
    return _sections(
        "Validar contratos de API e webhook.",
        "Dry-run valida contrato local; HTTP real exige autorização explícita.",
        ["## Regras", "- Run Contract Dry-run não executa HTTP real.", "- HTTP real requer confirmação.", "## Links relacionados", "- [[Context Builder]]", "- [[Decisões Técnicas]]", "- [[Referências Externas]]"],
        ["Registrar payload validado e fonte do provider."],
    )


def _context_builder_note(_: dict[str, object]) -> str:
    return _sections(
        "Transformar logs, métricas e diffs em contexto técnico reutilizável.",
        "Readiness indica se há evidência suficiente para orientar outra IA.",
        ["## Saídas", "- Markdown, JSON, HTML e ZIP.", "- Prompt final baseado em evidência.", "## Links relacionados", "- [[MVP Inicial]]", "- [[Prompts Operacionais]]", "- [[Memória Operacional]]"],
        ["Gerar contexto depois das suites necessárias passarem."],
    )


def _acp_executor_note(_: dict[str, object]) -> str:
    return _sections(
        "Executar SKILL.md por IDE, CLI ou agente ACP.",
        "O executor produz atualizações estruturadas e trilha de auditoria.",
        ["## Segurança", "- ACP recusa execução paga ou HTTP real até ação explícita pela UI ou CLI.", "## Links relacionados", "- [[ACP - AI Collaboration Protocol]]", "- [[PREVC]]", "- [[00 - Retomar Agora]]"],
        ["Consultar o fingerprint da skill antes de interpretar trilha ACP."],
    )


def _architecture_snapshot(snapshot: dict[str, object]) -> str:
    modules = [f"- {name}: {', '.join(files) if files else 'sem arquivos diretos'}" for name, files in snapshot["modules"].items()]
    return _sections(
        "Fornecer uma fotografia gerada e segura da estrutura de código.",
        "O conteúdo vem de caminhos, Git e documentação pública do repositório.",
        ["## Git", f"- Branch: {snapshot['branch']}", f"- Commit: {snapshot['commit']}", f"- Último commit: {snapshot['latest_subject']}", "## Módulos", *modules, "## Fluxo", "- [[Arquitetura do Sistema]]", "- [[Algorithm Test Lab]] -> [[Context Builder]]", "- [[Generic API Lab]] -> [[Context Builder]]", "- [[ACP Skill Executor]] -> [[Context Builder]]"],
        ["Execute a sincronização após commit que altere módulos ou fluxo."],
    )


def _documentation_snapshot(snapshot: dict[str, object]) -> str:
    documents = [f"- {item['path']} — {item['title']} ({item['digest']})" for item in snapshot["documents"]]
    return _sections(
        "Catalogar a documentação ativa para retomada rápida.",
        "Cada entrada traz caminho, título e digest curto para detectar mudança.",
        ["## Fontes atuais", *documents, "## Links relacionados", "- [[00 - Retomar Agora]]", "- [[Visão Geral do Projeto]]", "- [[Referências Externas]]"],
        ["Leia esta nota antes de procurar documentação manualmente."],
    )


def _prompts_note(_: dict[str, object]) -> str:
    return _sections(
        "Guardar prompts curtos e baseados em evidência.",
        "Prompts usam contexto validado e não substituem testes.",
        ["## Prompt de retomada", "- Leia [[00 - Retomar Agora]] e [[00 - Mapa do Projeto]]. Resuma estado, evidência e próximo passo antes de sugerir código.", "## Links relacionados", "- [[ACP - AI Collaboration Protocol]]", "- [[Context Builder]]"],
        ["Adicionar prompts ligados a um lab ou ticket específico."],
    )


def _logs_note(_: dict[str, object]) -> str:
    return _sections(
        "Registrar evolução relevante do sistema e do vault.",
        "Logs conectam mudança, evidência, decisão e próximo passo.",
        ["## Registro inicial", "- O cérebro operacional foi inicializado a partir do APIForgeKit e conectado ao fluxo evidence-first.", "## Links relacionados", "- [[Decisões Técnicas]]", "- [[PREVC]]", "- [[00 - Retomar Agora]]"],
        ["Após cada entrega, anote commit, teste e próximo passo."],
    )


def _backlog_note(_: dict[str, object]) -> str:
    return _sections(
        "Manter trabalho futuro separado de evidência validada.",
        "O backlog recebe ideias antes de virarem ticket ou decisão.",
        ["## Critério", "- Todo item liga a um módulo, hipótese ou referência.", "## Links relacionados", "- [[Tickets Ativos]]", "- [[MVP Inicial]]", "- [[Decisões Técnicas]]"],
        ["Transformar itens priorizados em tickets com PREVC."],
    )


def _tickets_note(_: dict[str, object]) -> str:
    return _sections(
        "Mostrar trabalho ativo e estado de validação.",
        "Cada ticket indica objetivo, evidência necessária, decisão e próximo passo.",
        ["## Estado inicial", "- Nenhum ticket criado ainda.", "## Links relacionados", "- [[Backlog Geral]]", "- [[PREVC]]", "- [[00 - Retomar Agora]]"],
        ["Criar ticket por mudança de comportamento, contrato ou arquitetura."],
    )


def _decisions_note(_: dict[str, object]) -> str:
    return _sections(
        "Registrar decisões técnicas como ADR leve.",
        "Uma decisão contém contexto, escolha, alternativas, consequência e evidência.",
        ["## Decisão inicial", "- O vault é memória navegável; o repositório é fonte de código, testes e evidências.", "## Links relacionados", "- [[Arquitetura do Sistema]]", "- [[Logs de Evolução]]", "- [[Memória Operacional]]"],
        ["Registrar decisão que altere protocolo, persistência, segurança ou fluxo."],
    )


def _note_template(_: dict[str, object]) -> str:
    return _sections(
        "Servir como modelo de nota operacional.",
        "Copie este modelo para criar nota curta, ligada e acionável.",
        ["## Estrutura", "- Objetivo", "- Contexto", "- Conteúdo principal", "- Links relacionados", "- Próximas ações", "## Links relacionados", "- [[00 - Mapa do Projeto]]"],
        ["Criar nota específica a partir deste modelo."],
    )


def _decision_template(_: dict[str, object]) -> str:
    return _sections(
        "Servir como modelo de decisão técnica.",
        "Use para registrar escolha, alternativas, consequência e evidência.",
        ["## Estrutura ADR leve", "- Contexto", "- Decisão", "- Alternativas consideradas", "- Consequências", "- Evidência", "## Links relacionados", "- [[Decisões Técnicas]]", "- [[00 - Mapa do Projeto]]"],
        ["Criar nova nota em 10 - Decisões para cada decisão relevante."],
    )
