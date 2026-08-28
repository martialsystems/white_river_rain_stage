# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_FORBIDDEN = (
    "p_sfha_calibrated",
    "indiana_flood_completion",
    "from indiana",
    "import p_sfha",
)


def test_src_does_not_import_p_sfha() -> None:
    hits: list[str] = []
    for path in (REPO / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        low = text.lower()
        for token in _FORBIDDEN:
            if token in low:
                hits.append(f"{path.name}:{token}")
    assert hits == []
