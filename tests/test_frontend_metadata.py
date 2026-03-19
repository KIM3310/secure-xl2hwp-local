from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "site" / "index.html"
PREVIEW_CARD = ROOT / "site" / "review-pack.svg"


def test_frontend_metadata_contract() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    required_tokens = [
        'name="description"',
        'property="og:title"',
        'property="og:description"',
        'property="og:image"',
        'property="og:image:alt"',
        'name="twitter:title"',
        'name="twitter:description"',
        'name="twitter:image"',
    ]

    for token in required_tokens:
        assert token in html, token


def test_preview_asset_exists() -> None:
    assert PREVIEW_CARD.exists()


def test_first_secure_workflow_copy_is_present() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "First secure workflow clarity" in html
    assert "Handoff certainty second." in html
    assert "Only point to signed bundles after" in html
