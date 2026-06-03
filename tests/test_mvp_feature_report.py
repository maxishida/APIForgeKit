from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mvp_feature_report_documents_test_sequence_and_optimization_backlog():
    report_path = ROOT / "docs" / "MVP_FEATURE_TEST_REPORT.md"

    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")

    assert "Test Sequence" in text
    assert "Optimization Backlog" in text
    assert "Algorithm Test Lab" in text
    assert "ACP Harness" in text
    assert "evidence_mode" in text
