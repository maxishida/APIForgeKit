import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    env_key: str
    model_env_key: str
    script_name: str
    cases: tuple[str, ...]


@dataclass(frozen=True)
class LabRun:
    provider: ProviderSpec
    case: str


@dataclass(frozen=True)
class LabResult:
    provider: str
    case: str
    output_file: Path
    status: str
    model: str
    latency_ms: object
    request_summary: str
    response_summary: str
    error_message: str


PROVIDERS = {
    "openai": ProviderSpec(
        name="openai",
        env_key="OPENAI_API_KEY",
        model_env_key="OPENAI_MODEL",
        script_name="openai_lab.py",
        cases=("auth", "basic", "stream", "tools", "structured"),
    ),
    "gemini": ProviderSpec(
        name="gemini",
        env_key="GEMINI_API_KEY",
        model_env_key="GEMINI_MODEL",
        script_name="gemini_lab.py",
        cases=("auth", "basic", "stream", "tools", "vision"),
    ),
    "anthropic": ProviderSpec(
        name="anthropic",
        env_key="ANTHROPIC_API_KEY",
        model_env_key="ANTHROPIC_MODEL",
        script_name="anthropic_lab.py",
        cases=("auth", "basic", "stream", "tools"),
    ),
    "xai": ProviderSpec(
        name="xai",
        env_key="XAI_API_KEY",
        model_env_key="XAI_MODEL",
        script_name="xai_lab.py",
        cases=("auth", "basic", "stream", "tools"),
    ),
}


def load_env_file(path: Path) -> dict[str, str]:
    values = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def current_lab_env(root: Path = ROOT) -> dict[str, str]:
    env = dict(os.environ)
    env.update(load_env_file(root / ".env"))
    return env


def status_lines(env: dict[str, str]) -> list[str]:
    lines = ["API Builder Lab status:"]
    for provider in PROVIDERS.values():
        key_status = "present" if env.get(provider.env_key) else "missing"
        model = env.get(provider.model_env_key) or "(default)"
        lines.append(f"{provider.name}:")
        lines.append(f"  {provider.env_key}: {key_status}")
        lines.append(f"  {provider.model_env_key}: {model}")
        lines.append(f"  cases: {', '.join(provider.cases)}")
    return lines


def select_runs(provider_name: str, case: str) -> list[LabRun]:
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name}")

    provider = PROVIDERS[provider_name]
    if case not in provider.cases:
        raise ValueError(f"Case {case!r} is not supported by provider {provider_name!r}")

    return [LabRun(provider=provider, case=case)]


def expected_output_path(root: Path, run: LabRun, output_date=None) -> Path:
    day = output_date or datetime.now(timezone.utc).date()
    return root / "outputs" / f"{day}_{run.provider.name}_{run.case}_result.json"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def backup_existing_output(path: Path, stamp: str | None = None) -> Path | None:
    if not path.exists():
        return None

    output_stamp = stamp or utc_stamp()
    backup = path.with_name(f"backup_{output_stamp}_{path.name}")
    suffix = 1
    while backup.exists():
        backup = path.with_name(f"backup_{output_stamp}_{suffix}_{path.name}")
        suffix += 1

    shutil.copy2(path, backup)
    return backup


def parse_lab_output(path: Path) -> LabResult:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return LabResult(
        provider=str(payload.get("provider", "")),
        case=str(payload.get("test_name", "")),
        output_file=path,
        status=str(payload.get("status", "")),
        model=str(payload.get("model_used", "")),
        latency_ms=payload.get("latency_ms", ""),
        request_summary=str(payload.get("request_summary", "")),
        response_summary=str(payload.get("response_summary", "")),
        error_message=str(payload.get("error_message", "")),
    )


def type_script_implication(result: LabResult) -> str:
    if result.status == "ok":
        return "Use this saved response shape as evidence before TypeScript adapter work."
    if result.status == "skipped_missing_env":
        return "Provider adapter planning is blocked until the local API key is configured."
    if result.status == "missing_dependency":
        return "Install or repair the Python SDK before trusting provider payload shape."
    return "Investigate provider docs or SDK behavior before TypeScript adapter work."


def format_technical_report(result: LabResult) -> str:
    failure_mode = result.error_message or ("none" if result.status == "ok" else result.status)
    finding = result.response_summary or result.request_summary or result.status
    return "\n".join(
        [
            f"Provider: {result.provider}",
            f"Case: {result.case}",
            f"Command: python labs/{result.provider}_lab.py --case {result.case}",
            f"Output file: {result.output_file}",
            f"Status: {result.status}",
            f"Model: {result.model}",
            f"Finding: {finding}",
            f"Failure mode: {failure_mode}",
            f"TypeScript implication: {type_script_implication(result)}",
            "Next action: Stop here if this case is not ok; otherwise use the JSON evidence for the next plan.",
        ]
    )


def run_focused_case(run: LabRun, root: Path = ROOT, python_exe: str = sys.executable) -> tuple[LabResult, Path | None, int]:
    output_path = expected_output_path(root, run)
    backup_path = backup_existing_output(output_path)
    script = root / "labs" / run.provider.script_name
    completed = subprocess.run(
        [python_exe, str(script), "--case", run.case],
        cwd=root,
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )

    if output_path.exists():
        return parse_lab_output(output_path), backup_path, completed.returncode

    message = (completed.stderr or completed.stdout or "Lab script did not create an output JSON.").strip()
    return (
        LabResult(
            provider=run.provider.name,
            case=run.case,
            output_file=output_path,
            status="runner_error",
            model="",
            latency_ms="",
            request_summary=f"python labs/{run.provider.script_name} --case {run.case}",
            response_summary="",
            error_message=message,
        ),
        backup_path,
        completed.returncode,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute one focused API Builder Lab case.")
    parser.add_argument("--status", action="store_true", help="Show provider readiness without making API calls.")
    parser.add_argument("--provider", choices=sorted(PROVIDERS), help="Provider to execute.")
    parser.add_argument("--case", help="Focused case to execute for the provider.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.status or (not args.provider and not args.case):
        print("\n".join(status_lines(current_lab_env())))
        if not args.status:
            print("\nNo API call executed. Use --provider <name> --case <case> for one focused lab run.")
        return 0

    if not args.provider or not args.case:
        parser.error("--provider and --case are required for execution")

    try:
        selected_runs = select_runs(args.provider, args.case)
    except ValueError as exc:
        parser.error(str(exc))

    result, backup_path, returncode = run_focused_case(selected_runs[0])
    if backup_path:
        print(f"Backup: {backup_path}")
    print(format_technical_report(result))

    if result.status != "ok":
        return 1
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
