import asyncio
import json

import httpx
import pytest

from backend.app.services.ai_analysis.openrouter_client import (
    OpenRouterClient,
    OpenRouterClientError,
    OpenRouterConfig,
)


def test_config_reads_env_values_without_loading_dotenv():
    config = OpenRouterConfig.from_env(
        {
            "OPENROUTER_API_KEY": "test-key",
            "OPENROUTER_MODEL": "test-model",
            "OPENROUTER_BASE_URL": "https://example.test/v1/",
            "OPENROUTER_TIMEOUT_SECONDS": "12.5",
        }
    )

    assert config.api_key == "test-key"
    assert config.model == "test-model"
    assert config.base_url == "https://example.test/v1"
    assert config.timeout_seconds == 12.5
    assert config.is_configured


@pytest.mark.parametrize("timeout", ["invalid", "0", "-1", "nan", "inf"])
def test_config_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError, match="OPENROUTER_TIMEOUT_SECONDS"):
        OpenRouterConfig.from_env({"OPENROUTER_TIMEOUT_SECONDS": timeout})


def test_config_defaults_to_gemma_and_openrouter_endpoint():
    config = OpenRouterConfig.from_env({"OPENROUTER_API_KEY": "test-key"})

    assert config.model == "google/gemma-4-31b-it"
    assert config.base_url == "https://openrouter.ai/api/v1"


def test_client_sends_openai_compatible_request():
    requests = []

    async def handler(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"ok": true}'}}]},
        )

    client = OpenRouterClient(
        OpenRouterConfig(
            api_key="test-key",
            model="test-model",
            base_url="https://openrouter.example/v1",
        ),
        transport=httpx.MockTransport(handler),
    )

    content = asyncio.run(
        client.complete([{"role": "user", "content": "Check this text"}])
    )

    assert content == '{"ok": true}'
    assert len(requests) == 1
    request = requests[0]
    assert request.url == "https://openrouter.example/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer test-key"
    assert json.loads(request.content)["model"] == "test-model"


def test_client_raises_safe_error_for_provider_error():
    async def handler(_request):
        return httpx.Response(503, json={"detail": "unavailable"})

    client = OpenRouterClient(
        OpenRouterConfig(api_key="test-key", model="test-model"),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(OpenRouterClientError, match="HTTP 503") as error:
        asyncio.run(client.complete([]))

    assert "test-key" not in str(error.value)


def test_client_rejects_invalid_completion_shape():
    async def handler(request):
        return httpx.Response(200, json={"choices": []})

    client = OpenRouterClient(
        OpenRouterConfig(api_key="test-key", model="test-model"),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(OpenRouterClientError, match="invalid chat completion"):
        asyncio.run(client.complete([]))
