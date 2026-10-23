import pytest
from pydantic import ValidationError

from backend.app.services.ai_analysis.baseline import analyze_text
from backend.app.services.ai_analysis.schemas import (
    RiskCategory,
    ScamAnalysisRequest,
)


def test_message_asking_for_otp_is_high_risk():
    result = analyze_text("Send your OTP now to stop your account being closed.")

    assert result.category == RiskCategory.HIGH
    assert result.indicators[0].code == "credential_request"
    assert result.indicators[0].evidence == "send your otp"


def test_urgent_payment_is_medium_risk():
    result = analyze_text("Act now and pay now to keep this offer.")

    assert result.category == RiskCategory.MEDIUM
    assert result.indicators[0].code == "urgent_payment"


def test_benign_text_has_no_matching_indicators():
    result = analyze_text("The library will be closed on Sunday.")

    assert result.category == RiskCategory.LOW
    assert result.indicators == []
    assert "does not confirm" in result.explanation


def test_blank_text_is_inconclusive():
    result = analyze_text("   ")

    assert result.category == RiskCategory.INCONCLUSIVE


def test_request_strips_surrounding_whitespace():
    request = ScamAnalysisRequest(text="  Check this message  ")

    assert request.text == "Check this message"


@pytest.mark.parametrize("text", ["", "   ", "x" * 5001])
def test_request_rejects_empty_or_too_long_text(text):
    with pytest.raises(ValidationError):
        ScamAnalysisRequest(text=text)
