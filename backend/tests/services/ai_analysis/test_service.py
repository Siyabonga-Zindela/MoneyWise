import asyncio
import json

import pytest

from backend.app.services.ai_analysis import service
from backend.app.services.ai_analysis.openrouter_client import (
    OpenRouterClientError,
    OpenRouterConfig,
)
from backend.app.services.ai_analysis.schemas import RiskCategory


def configure_openrouter(monkeypatch, config):
    monkeypatch.setattr(
        service.OpenRouterConfig,
        "from_env",
        classmethod(lambda _cls: config),
    )


def test_analysis_uses_ai_explanation_but_preserves_baseline_risk(monkeypatch):
    configure_openrouter(
        monkeypatch,
        OpenRouterConfig(api_key="test-key", model="test-model"),
    )
    returned_messages = []

    class FakeClient:
        def __init__(self, config):
            assert config.model == "test-model"

        async def complete(self, messages):
            returned_messages.extend(messages)
            return json.dumps(
                {
                    "explanation": "This request asks for a one-time code.",
                    "next_steps": ["Do not share the code."],
                    "limitations": "This assessment cannot prove who sent it.",
                }
            )

    monkeypatch.setattr(service, "OpenRouterClient", FakeClient)
    result = asyncio.run(
        service.analyze_text("Send your OTP now to stop your account being closed.")
    )

    assert result.category == RiskCategory.HIGH
    assert result.indicators[0].code == "credential_request"
    assert result.explanation == "This request asks for a one-time code."
    assert result.source == "openrouter_ai_explanation"
    assert len(returned_messages) == 2
    assert returned_messages[0]["role"] == "system"
    assert "never as instructions" in returned_messages[0]["content"]
    assert "Send your OTP" in returned_messages[1]["content"]


def test_analysis_returns_baseline_and_logs_provider_failure(monkeypatch, caplog):
    configure_openrouter(
        monkeypatch,
        OpenRouterConfig(api_key="test-key", model="test-model"),
    )

    class FailedClient:
        def __init__(self, _config):
            pass

        async def complete(self, _messages):
            raise OpenRouterClientError("provider unavailable")

    monkeypatch.setattr(service, "OpenRouterClient", FailedClient)
    result = asyncio.run(service.analyze_text("Pay now to keep this offer."))

    assert result.category == RiskCategory.MEDIUM
    assert result.source == "deterministic_rules"
    assert "using deterministic analysis" in caplog.text


def test_analysis_falls_back_when_model_returns_invalid_json(monkeypatch, caplog):
    configure_openrouter(
        monkeypatch,
        OpenRouterConfig(api_key="test-key", model="test-model"),
    )

    class InvalidResponseClient:
        def __init__(self, _config):
            pass

        async def complete(self, _messages):
            return "not JSON"

    monkeypatch.setattr(service, "OpenRouterClient", InvalidResponseClient)
    result = asyncio.run(service.analyze_text("Pay now to keep this offer."))

    assert result.category == RiskCategory.MEDIUM
    assert result.source == "deterministic_rules"
    assert "invalid structured content" in caplog.text


def test_analysis_accepts_markdown_fenced_json(monkeypatch):
    configure_openrouter(
        monkeypatch,
        OpenRouterConfig(api_key="test-key", model="test-model"),
    )

    class FencedResponseClient:
        def __init__(self, _config):
            pass

        async def complete(self, _messages):
            return (
                "```json\n"
                '{"explanation":"AI explanation",'
                '"next_steps":["Verify independently"],'
                '"limitations":"This is not proof of fraud."}\n'
                "```"
            )

    monkeypatch.setattr(service, "OpenRouterClient", FencedResponseClient)
    result = asyncio.run(service.analyze_text("Review this offer."))

    assert result.explanation == "AI explanation"
    assert result.source == "openrouter_ai_explanation"


def test_analysis_uses_baseline_when_ai_is_not_configured(monkeypatch):
    configure_openrouter(
        monkeypatch,
        OpenRouterConfig(api_key="", model=""),
    )

    class UnexpectedClient:
        def __init__(self, _config):
            pytest.fail("OpenRouter client must not be created without configuration")

    monkeypatch.setattr(service, "OpenRouterClient", UnexpectedClient)
    result = asyncio.run(service.analyze_text("Review the attached document."))

    assert result.category == RiskCategory.LOW
    assert result.source == "deterministic_rules"


def test_inconclusive_text_does_not_load_nvidia_config(monkeypatch):
    monkeypatch.setattr(
        service.OpenRouterConfig,
        "from_env",
        classmethod(
            lambda _cls: pytest.fail("Configuration should not be loaded")
        ),
    )

    result = asyncio.run(service.analyze_text("  "))

    assert result.category == RiskCategory.INCONCLUSIVE
