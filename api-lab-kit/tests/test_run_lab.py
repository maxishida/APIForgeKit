import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_lab


class RunLabTests(unittest.TestCase):
    def test_provider_registry_matches_skill_cases(self):
        self.assertEqual(run_lab.PROVIDERS["openai"].cases, ("auth", "basic", "stream", "tools", "structured"))
        self.assertEqual(run_lab.PROVIDERS["gemini"].cases, ("auth", "basic", "stream", "tools", "vision"))
        self.assertEqual(run_lab.PROVIDERS["anthropic"].cases, ("auth", "basic", "stream", "tools"))
        self.assertEqual(run_lab.PROVIDERS["xai"].cases, ("auth", "basic", "stream", "tools"))

    def test_select_run_returns_one_focused_case(self):
        selected = run_lab.select_runs("xai", "basic")

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].provider.name, "xai")
        self.assertEqual(selected[0].case, "basic")

    def test_select_run_rejects_case_not_supported_by_provider(self):
        with self.assertRaisesRegex(ValueError, "not supported"):
            run_lab.select_runs("xai", "structured")

    def test_expected_output_path_uses_existing_lab_naming(self):
        selected = run_lab.select_runs("xai", "stream")[0]

        path = run_lab.expected_output_path(ROOT, selected, date(2026, 5, 7))

        self.assertEqual(path, ROOT / "outputs" / "2026-05-07_xai_stream_result.json")

    def test_backup_existing_output_copies_without_deleting_original(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "2026-05-07_xai_basic_result.json"
            output.write_text('{"status": "ok"}', encoding="utf-8")

            backup = run_lab.backup_existing_output(output, "20260507T150000Z")

            self.assertTrue(output.exists())
            self.assertTrue(backup.exists())
            self.assertEqual(backup.name, "backup_20260507T150000Z_2026-05-07_xai_basic_result.json")
            self.assertEqual(backup.read_text(encoding="utf-8"), '{"status": "ok"}')

    def test_load_env_status_never_exposes_secret_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("XAI_API_KEY=secret-value\nXAI_MODEL=grok-test\n", encoding="utf-8")

            env = run_lab.load_env_file(env_path)
            status = run_lab.status_lines(env)
            joined = "\n".join(status)

            self.assertEqual(env["XAI_API_KEY"], "secret-value")
            self.assertIn("XAI_API_KEY: present", joined)
            self.assertNotIn("secret-value", joined)

    def test_parse_output_and_report_use_skill_template(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "2026-05-07_xai_basic_result.json"
            output.write_text(
                json.dumps(
                    {
                        "provider": "xai",
                        "test_name": "basic",
                        "status": "ok",
                        "model_used": "grok-test",
                        "latency_ms": 123.45,
                        "request_summary": "xAI chat sample text call",
                        "response_summary": "api-lab-ok",
                        "error_message": "",
                    }
                ),
                encoding="utf-8",
            )

            result = run_lab.parse_lab_output(output)
            report = run_lab.format_technical_report(result)

            self.assertEqual(result.status, "ok")
            self.assertIn("Provider: xai", report)
            self.assertIn("Case: basic", report)
            self.assertIn("Output file:", report)
            self.assertIn("Status: ok", report)
            self.assertIn("TypeScript implication:", report)


if __name__ == "__main__":
    unittest.main()
