import pytest

from codenames_heb.llm_client import FormatFailure, OpenRouterClient


def _mock_response(mocker, content: str):
    resp = mocker.Mock()
    resp.raise_for_status = mocker.Mock()
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return resp


def test_complete_returns_message_content_and_sends_model_and_auth(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(mocker, "hello world")
    client = OpenRouterClient(api_key="test-key")

    result = client.complete("some/model", "system", "user")

    assert result == "hello world"
    kwargs = mock_post.call_args.kwargs
    assert kwargs["json"]["model"] == "some/model"
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"


def test_complete_json_parses_valid_json(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(mocker, '{"clue": "אור", "count": 2}')
    client = OpenRouterClient(api_key="test-key")

    result = client.complete_json("some/model", "system", "user")

    assert result == {"clue": "אור", "count": 2}


def test_complete_json_strips_markdown_code_fence(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(mocker, '```json\n{"clue": "אור"}\n```')
    client = OpenRouterClient(api_key="test-key")

    result = client.complete_json("some/model", "system", "user")

    assert result == {"clue": "אור"}


def test_complete_json_retries_then_raises_format_failure(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(mocker, "not json at all")
    client = OpenRouterClient(api_key="test-key")

    with pytest.raises(FormatFailure):
        client.complete_json("some/model", "system", "user", max_retries=3)

    assert mock_post.call_count == 3


def test_complete_json_succeeds_after_one_retry(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.side_effect = [
        _mock_response(mocker, "not json"),
        _mock_response(mocker, '{"clue": "אור"}'),
    ]
    client = OpenRouterClient(api_key="test-key")

    result = client.complete_json("some/model", "system", "user", max_retries=3)

    assert result == {"clue": "אור"}
    assert mock_post.call_count == 2


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValueError):
        OpenRouterClient(api_key=None)
