# Copyright (c) 2026 Martial Systems LLC

from rainstage.claims import scan_text
from rainstage.config import QUESTION


def test_question_and_bans() -> None:
    from rainstage.config import LIVE_ATTRIBUTION_SUBTITLE

    assert scan_text(QUESTION) == []
    assert scan_text(LIVE_ATTRIBUTION_SUBTITLE) == []
    assert "flood_ai" in scan_text("we built flood AI")
    assert "attrib_wet" in scan_text("attribution map is a wet mask")
    assert "attrib_firm" in scan_text("attribution layer is a FIRM")
    assert "attrib_runoff" in scan_text("attribution map is a runoff map")
    assert "fixture_rescues" in scan_text("fixture skill rescues live")
    assert "flood_warning" in scan_text("this is a flood warning")
    assert "forecast" in scan_text("P(sfha | hydro) is a flood forecast")
