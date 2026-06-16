from ui import context_builder


def test_context_builder_exposes_markdown_download_action():
    labels = {action["label"] for action in context_builder.CONTEXT_EXPORT_ACTIONS}

    assert "Download .md" in labels
    assert "Generate AI Prompt" in labels
    assert "Export Markdown" in labels
    assert "Export JSON" in labels
    assert "Export HTML" in labels
    assert "Export ZIP" in labels


def test_context_builder_markdown_download_payload_is_safe_and_reusable():
    bundle = {
        "source_mode": "algorithm_api",
        "generated_at": "2026-06-05T01:02:03+00:00",
        "context": "# Contexto\n\n- lead_score validado",
    }

    payload = context_builder.build_markdown_download_payload(bundle)

    assert payload["filename"] == "apiforgekit_context_algorithm_api_20260605T0102030000.md"
    assert payload["media_type"] == "text/markdown"
    assert payload["content"] == "# Contexto\n\n- lead_score validado"
