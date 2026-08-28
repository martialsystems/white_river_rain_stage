# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

from rainstage.claims import scan_text
from rainstage.config import QUESTION

REPO = Path(__file__).resolve().parents[1]


def test_readme_opens_with_the_question() -> None:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    body = "\n".join(text.splitlines()[1:]).lstrip()
    assert body.startswith(QUESTION)
    assert "1,219" in text
    assert "03351000" in text
    assert "p_sfha" in text
    assert "white_river_stage_inundation" in text
    assert "indiana_flood_completion" in text
    assert scan_text(text) == []
    assert "—" not in text
    assert "What it is not" not in text
