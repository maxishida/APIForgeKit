# Algorithm Validation Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a user-friendly lab that validates local algorithms and API-based algorithms with expected-vs-actual evidence.

**Architecture:** Add a generic algorithm validation layer beside the existing xAI observability layer. Store algorithm definitions, cases, runs and results in PostgreSQL, then render a NiceGUI page with manual case execution, suite execution, diff display and context export.

**Tech Stack:** NiceGUI, SQLAlchemy 2.x, PostgreSQL, Plotly, Pandas, Pytest.

---

## File Structure

- Modify `core/models.py`: add algorithm validation tables.
- Create `core/algorithm_validation.py`: validation dataclasses, repository helpers, diff logic and context builder.
- Create `core/http_harness.py`: safe HTTP runner for API-based algorithms.
- Create `ui/algorithm_lab.py`: NiceGUI page for manual cases and suites.
- Modify `ui/app_shell.py`: add navigation item.
- Modify `app.py`: register `/algorithm-lab`.
- Create `tests/test_algorithm_validation.py`: unit tests for diff, persistence and context.
- Create `tests/test_http_harness.py`: tests for HTTP payload validation without real network.
- Modify `README.md`, `USER_GUIDE.md`, `ALGORITHM_TEST_PLAN.md`: document final commands and user flow.

---

### Task 1: Algorithm Data Model

**Files:**
- Modify: `core/models.py`
- Test: `tests/test_algorithm_validation.py`

- [ ] **Step 1: Write failing model/repository test**

```python
from sqlalchemy import create_engine

from core.algorithm_validation import AlgorithmCaseInput, AlgorithmValidationRepository
from core.database import build_session_factory, init_db


def test_algorithm_case_and_result_are_persisted():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    repo = AlgorithmValidationRepository(build_session_factory(engine))

    definition = repo.create_definition(
        name="lead_score",
        description="Classifica leads por intenção de compra.",
        input_schema={"type": "object"},
        output_schema={"type": "object"},
    )
    case = repo.create_case(
        AlgorithmCaseInput(
            algorithm_id=definition["id"],
            name="Lead quente WhatsApp",
            input_payload={"source": "WhatsApp", "message": "Quero orçamento hoje"},
            expected_output={"classification": "urgent_lead", "min_score": 80},
        )
    )
    result = repo.record_result(
        case_id=case["id"],
        run_id="run-1",
        status="passed",
        actual_output={"classification": "urgent_lead", "score": 95},
        diff={},
        latency_ms=2.5,
        recommendation="Algoritmo aprovado para este caso.",
    )

    assert definition["name"] == "lead_score"
    assert case["name"] == "Lead quente WhatsApp"
    assert result["status"] == "passed"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_algorithm_validation.py::test_algorithm_case_and_result_are_persisted -q
```

Expected:

```txt
ModuleNotFoundError: No module named 'core.algorithm_validation'
```

- [ ] **Step 3: Add SQLAlchemy models**

Add to `core/models.py`:

```python
class AlgorithmDefinition(Base):
    __tablename__ = "algorithm_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    input_schema: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    output_schema: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class AlgorithmCase(Base):
    __tablename__ = "algorithm_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    algorithm_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    input_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    expected_output: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)


class AlgorithmRun(Base):
    __tablename__ = "algorithm_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    algorithm_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(40), default="running", index=True)
    summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class AlgorithmResult(Base):
    __tablename__ = "algorithm_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    actual_output: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    diff: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    recommendation: Mapped[str] = mapped_column(Text, default="")
```

- [ ] **Step 4: Create minimal repository**

Create `core/algorithm_validation.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from core.models import AlgorithmCase, AlgorithmDefinition, AlgorithmResult


@dataclass(frozen=True)
class AlgorithmCaseInput:
    algorithm_id: str
    name: str
    input_payload: dict[str, object]
    expected_output: dict[str, object]
    tags: list[str] = field(default_factory=list)


class AlgorithmValidationRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def create_definition(self, name: str, description: str, input_schema: dict[str, object], output_schema: dict[str, object]) -> dict[str, object]:
        with self.session_factory() as session:
            row = AlgorithmDefinition(
                id=str(uuid4()),
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
            )
            session.add(row)
            session.commit()
            return {"id": row.id, "name": row.name, "description": row.description}

    def create_case(self, case: AlgorithmCaseInput) -> dict[str, object]:
        with self.session_factory() as session:
            row = AlgorithmCase(id=str(uuid4()), **case.__dict__)
            session.add(row)
            session.commit()
            return {"id": row.id, "name": row.name, "algorithm_id": row.algorithm_id}

    def record_result(self, case_id: str, run_id: str, status: str, actual_output: dict[str, object], diff: dict[str, object], latency_ms: float, recommendation: str) -> dict[str, object]:
        with self.session_factory() as session:
            row = AlgorithmResult(
                id=str(uuid4()),
                case_id=case_id,
                run_id=run_id,
                status=status,
                actual_output=actual_output,
                diff=diff,
                latency_ms=latency_ms,
                recommendation=recommendation,
            )
            session.add(row)
            session.commit()
            return {"id": row.id, "status": row.status, "diff": row.diff}
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_algorithm_validation.py::test_algorithm_case_and_result_are_persisted -q
```

Expected:

```txt
1 passed
```

---

### Task 2: Expected vs Actual Diff

**Files:**
- Modify: `core/algorithm_validation.py`
- Test: `tests/test_algorithm_validation.py`

- [ ] **Step 1: Write failing diff tests**

```python
from core.algorithm_validation import compare_expected_actual


def test_compare_expected_actual_supports_exact_and_min_score():
    diff = compare_expected_actual(
        expected={"classification": "urgent_lead", "min_score": 80},
        actual={"classification": "urgent_lead", "score": 95},
    )

    assert diff["passed"] is True
    assert diff["mismatches"] == []


def test_compare_expected_actual_reports_mismatch():
    diff = compare_expected_actual(
        expected={"classification": "hot_lead", "min_score": 80},
        actual={"classification": "warm_lead", "score": 55},
    )

    assert diff["passed"] is False
    assert diff["mismatches"][0]["field"] == "classification"
    assert diff["mismatches"][1]["field"] == "score"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_algorithm_validation.py::test_compare_expected_actual_supports_exact_and_min_score tests/test_algorithm_validation.py::test_compare_expected_actual_reports_mismatch -q
```

Expected:

```txt
ImportError: cannot import name 'compare_expected_actual'
```

- [ ] **Step 3: Implement diff helper**

Add to `core/algorithm_validation.py`:

```python
def compare_expected_actual(expected: dict[str, object], actual: dict[str, object]) -> dict[str, object]:
    mismatches: list[dict[str, object]] = []

    for field, expected_value in expected.items():
        if field == "min_score":
            actual_score = actual.get("score")
            if not isinstance(actual_score, (int, float)) or actual_score < expected_value:
                mismatches.append({"field": "score", "expected": f">= {expected_value}", "actual": actual_score})
            continue
        if field == "max_score":
            actual_score = actual.get("score")
            if not isinstance(actual_score, (int, float)) or actual_score > expected_value:
                mismatches.append({"field": "score", "expected": f"<= {expected_value}", "actual": actual_score})
            continue
        actual_value = actual.get(field)
        if actual_value != expected_value:
            mismatches.append({"field": field, "expected": expected_value, "actual": actual_value})

    return {"passed": not mismatches, "mismatches": mismatches}
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
python -m pytest tests/test_algorithm_validation.py -q
```

Expected:

```txt
3 passed
```

---

### Task 3: HTTP Harness For API Algorithms

**Files:**
- Create: `core/http_harness.py`
- Test: `tests/test_http_harness.py`

- [ ] **Step 1: Write failing tests without network**

```python
from core.http_harness import build_http_case_event


def test_build_http_case_event_redacts_authorization():
    event = build_http_case_event(
        name="Lead Score API",
        method="POST",
        url="http://localhost:3000/api/score",
        headers={"Authorization": "Bearer secret", "Content-Type": "application/json"},
        payload={"message": "Quero comprar agora"},
    )

    assert event["request"]["headers"]["Authorization"] == "<redacted>"
    assert event["request"]["payload"]["message"] == "Quero comprar agora"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/test_http_harness.py -q
```

Expected:

```txt
ModuleNotFoundError: No module named 'core.http_harness'
```

- [ ] **Step 3: Implement safe event builder**

Create `core/http_harness.py`:

```python
from __future__ import annotations


SECRET_HEADER_NAMES = {"authorization", "x-api-key", "cookie"}


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: "<redacted>" if key.lower() in SECRET_HEADER_NAMES else value
        for key, value in headers.items()
    }


def build_http_case_event(name: str, method: str, url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
    return {
        "name": name,
        "request": {
            "method": method.upper(),
            "url": url,
            "headers": redact_headers(headers),
            "payload": payload,
        },
    }
```

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
python -m pytest tests/test_http_harness.py -q
```

Expected:

```txt
1 passed
```

---

### Task 4: NiceGUI Algorithm Lab Page

**Files:**
- Create: `ui/algorithm_lab.py`
- Modify: `app.py`
- Modify: `ui/app_shell.py`
- Test: `python -m compileall app.py ui core`

- [ ] **Step 1: Add navigation item**

Modify `NAV_ITEMS` in `ui/app_shell.py`:

```python
NAV_ITEMS = (
    ("Live Dashboard", "/", "monitor_heart"),
    ("Algorithm Lab", "/algorithm-lab", "rule"),
    ("Lead Algorithm Lab", "/lead-lab", "science"),
    ("Logs", "/logs", "terminal"),
    ("Context Builder", "/context-builder", "integration_instructions"),
    ("Blueprint Archive", "/blueprint", "account_tree"),
    ("Settings", "/settings", "settings"),
)
```

- [ ] **Step 2: Create first page skeleton**

Create `ui/algorithm_lab.py`:

```python
from __future__ import annotations

import json

from nicegui import ui

from core.algorithm_validation import compare_expected_actual


def render_algorithm_lab(services) -> None:
    with ui.column().classes("afk-card w-full gap-4").style("padding:18px;"):
        ui.label("Algorithm Validation Lab").classes("text-xl font-bold afk-title")
        ui.label("Teste algoritmo local ou API comparando esperado x real.").classes("afk-muted")

        algorithm_name = ui.input("Nome do algoritmo", value="lead_score").classes("w-full")
        actual_json = ui.textarea("Resultado real JSON", value='{"classification":"urgent_lead","score":95}').classes("w-full")
        expected_json = ui.textarea("Resultado esperado JSON", value='{"classification":"urgent_lead","min_score":80}').classes("w-full")
        output = ui.code("{}", language="json").classes("w-full")

        def run_case() -> None:
            actual = json.loads(actual_json.value or "{}")
            expected = json.loads(expected_json.value or "{}")
            diff = compare_expected_actual(expected, actual)
            output.set_content(json.dumps({"algorithm": algorithm_name.value, "diff": diff}, ensure_ascii=False, indent=2))

        ui.button("Executar caso", icon="play_arrow", on_click=run_case).classes("afk-primary-btn")
```

- [ ] **Step 3: Register route**

Modify `app.py`:

```python
from ui.algorithm_lab import render_algorithm_lab


@ui.page("/algorithm-lab")
def algorithm_lab_page() -> None:
    apply_theme()
    render_shell(
        "Algorithm Lab",
        "Algorithm Validation Lab",
        "Valide algoritmos locais ou APIs com esperado x real",
        lambda: render_algorithm_lab(_services()),
    )
```

- [ ] **Step 4: Compile**

Run:

```bash
python -m compileall app.py ui core
```

Expected:

```txt
Compiling
```

---

### Task 5: Context For Algorithm Cases

**Files:**
- Modify: `core/algorithm_validation.py`
- Test: `tests/test_algorithm_validation.py`

- [ ] **Step 1: Write failing context test**

```python
from core.algorithm_validation import build_algorithm_context


def test_build_algorithm_context_is_ai_ready():
    context = build_algorithm_context(
        algorithm_name="lead_score",
        cases=[
            {
                "name": "Lead quente",
                "input": {"message": "Quero orçamento hoje"},
                "expected": {"classification": "urgent_lead"},
                "actual": {"classification": "urgent_lead", "score": 95},
                "status": "passed",
            }
        ],
    )

    assert "Contexto Técnico - Algorithm Validation Lab" in context
    assert "lead_score" in context
    assert "Lead quente" in context
```

- [ ] **Step 2: Implement context builder**

Add to `core/algorithm_validation.py`:

```python
import json


def build_algorithm_context(algorithm_name: str, cases: list[dict[str, object]]) -> str:
    rendered_cases = "\n".join(
        f"- {case['name']}: status={case['status']} input={json.dumps(case['input'], ensure_ascii=False)} actual={json.dumps(case['actual'], ensure_ascii=False)}"
        for case in cases
    )
    return f"""# Contexto Técnico - Algorithm Validation Lab

## Algoritmo

{algorithm_name}

## Casos de Teste

{rendered_cases or "- Nenhum caso registrado."}

## Recomendação

Usar estes casos como contrato antes de implementar site, API ou automação SaaS.
"""
```

- [ ] **Step 3: Run tests**

Run:

```bash
python -m pytest tests/test_algorithm_validation.py -q
```

Expected:

```txt
4 passed
```

---

### Task 6: Final Verification

**Files:**
- Modify: `README.md`
- Modify: `USER_GUIDE.md`
- Modify: `ALGORITHM_TEST_PLAN.md`

- [ ] **Step 1: Run full tests**

Run:

```bash
python -m pytest -q
```

Expected:

```txt
all tests passed
```

- [ ] **Step 2: Run app smoke check**

Run:

```bash
npm run db
python app.py
```

Open:

```txt
http://localhost:8080/algorithm-lab
```

Expected:

```txt
Algorithm Validation Lab page loads and "Executar caso" shows diff JSON.
```

- [ ] **Step 3: Commit**

Run:

```bash
git add core/models.py core/algorithm_validation.py core/http_harness.py ui/algorithm_lab.py ui/app_shell.py app.py tests/test_algorithm_validation.py tests/test_http_harness.py README.md USER_GUIDE.md ALGORITHM_TEST_PLAN.md
git commit -m "feat: add algorithm validation lab"
```

---

## Self-Review

Spec coverage:

- User-friendly explanation: covered in page skeleton and docs.
- Algorithm using site/API: covered by HTTP harness task.
- Expected vs actual: covered by diff helper and UI output.
- Context for AI: covered by algorithm context builder.
- SaaS validation path: covered by docs and final context.

Placeholder scan:

- No TODO/TBD placeholders.
- Every task has exact files, commands and expected outputs.

Type consistency:

- `AlgorithmCaseInput`, `AlgorithmValidationRepository`, `compare_expected_actual` and `build_algorithm_context` are defined before use in UI/tests.
