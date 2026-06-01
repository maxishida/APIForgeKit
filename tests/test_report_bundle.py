import zipfile
from pathlib import Path

from core.report_bundle import create_report_bundle


def test_report_bundle_exports_markdown_json_html_and_zip(tmp_path):
    bundle = create_report_bundle(
        output_dir=tmp_path,
        name="demo",
        markdown="# Demo\n\nEvidence.",
        payload={"summary": {"tests": 2}},
    )

    assert set(bundle) == {"markdown", "json", "html", "zip"}
    assert Path(bundle["markdown"]).read_text(encoding="utf-8").startswith("# Demo")
    assert '"tests": 2' in Path(bundle["json"]).read_text(encoding="utf-8")
    assert "<!doctype html>" in Path(bundle["html"]).read_text(encoding="utf-8")

    with zipfile.ZipFile(bundle["zip"]) as archive:
        assert sorted(archive.namelist()) == ["demo.html", "demo.json", "demo.md"]
