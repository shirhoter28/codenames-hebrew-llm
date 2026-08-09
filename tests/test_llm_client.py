import pytest
import requests

from codenames_heb.llm_client import FormatFailure, OpenRouterClient


def _mock_response(mocker, content: str):
    resp = mocker.Mock()
    resp.raise_for_status = mocker.Mock()
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return resp


def _http_error_response(mocker, status_code: int):
    """A response whose raise_for_status() raises an HTTPError with that status."""
    resp = mocker.Mock()
    resp.status_code = status_code
    resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
        f"{status_code} error", response=resp
    )
    return resp


def _fast_client() -> OpenRouterClient:
    """Client with zero backoff so retry tests don't actually sleep."""
    return OpenRouterClient(api_key="test-key", retry_backoff=0.0)


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


# --- Fix 1.1: non-dict JSON payloads must not escape as AttributeError/TypeError ---


def test_complete_json_rejects_non_dict_payload_as_format_failure(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(mocker, '["אור", "ירח"]')
    client = _fast_client()

    with pytest.raises(FormatFailure) as excinfo:
        client.complete_json("some/model", "system", "user", max_retries=2)

    assert "expected a JSON object" in str(excinfo.value)
    # A non-dict payload is a retryable format problem, so all attempts are used.
    assert mock_post.call_count == 2


def test_complete_json_rejects_bare_scalar_payload(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(mocker, "42")
    client = _fast_client()

    with pytest.raises(FormatFailure) as excinfo:
        client.complete_json("some/model", "system", "user", max_retries=1)

    assert "expected a JSON object, got int" in str(excinfo.value)


# --- Fix 1.2: JSON wrapped in prose ---


def test_complete_json_extracts_object_wrapped_in_prose(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(
        mocker, 'הנה הרמז שלי: {"clue": "אור", "count": 2} בהצלחה!'
    )
    client = _fast_client()

    result = client.complete_json("some/model", "system", "user")

    assert result == {"clue": "אור", "count": 2}


def test_complete_json_extracts_object_with_nested_braces_from_prose(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(
        mocker,
        'Sure! {"clue": "אור", "translation_map": {"ירח": "moon"}} -- done',
    )
    client = _fast_client()

    result = client.complete_json("some/model", "system", "user")

    assert result == {"clue": "אור", "translation_map": {"ירח": "moon"}}


def test_complete_json_ignores_braces_inside_strings_when_extracting(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(
        mocker, 'note: {"reasoning": "a } brace in a string"} end'
    )
    client = _fast_client()

    result = client.complete_json("some/model", "system", "user")

    assert result == {"reasoning": "a } brace in a string"}


def test_complete_json_still_fails_when_no_object_present(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(mocker, "I cannot help with that.")
    client = _fast_client()

    with pytest.raises(FormatFailure):
        client.complete_json("some/model", "system", "user", max_retries=1)


# --- Fix 2: transport / rate-limit retry ---


def test_complete_retries_on_connection_error_then_succeeds(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.side_effect = [
        requests.exceptions.ConnectionError("boom"),
        _mock_response(mocker, "hello"),
    ]
    client = _fast_client()

    assert client.complete("some/model", "system", "user") == "hello"
    assert mock_post.call_count == 2


def test_complete_retries_on_timeout_then_succeeds(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.side_effect = [
        requests.exceptions.Timeout("slow"),
        _mock_response(mocker, "hello"),
    ]
    client = _fast_client()

    assert client.complete("some/model", "system", "user") == "hello"
    assert mock_post.call_count == 2


def test_complete_retries_on_429_then_succeeds(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.side_effect = [
        _http_error_response(mocker, 429),
        _mock_response(mocker, "hello"),
    ]
    client = _fast_client()

    assert client.complete("some/model", "system", "user") == "hello"
    assert mock_post.call_count == 2


def test_complete_retries_on_500_then_succeeds(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.side_effect = [
        _http_error_response(mocker, 503),
        _mock_response(mocker, "hello"),
    ]
    client = _fast_client()

    assert client.complete("some/model", "system", "user") == "hello"
    assert mock_post.call_count == 2


def test_complete_does_not_retry_on_400_client_error(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _http_error_response(mocker, 400)
    client = _fast_client()

    with pytest.raises(requests.exceptions.HTTPError):
        client.complete("some/model", "system", "user")

    assert mock_post.call_count == 1


def test_complete_does_not_retry_on_401_unauthorized(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _http_error_response(mocker, 401)
    client = _fast_client()

    with pytest.raises(requests.exceptions.HTTPError):
        client.complete("some/model", "system", "user")

    assert mock_post.call_count == 1


def test_complete_gives_up_after_max_attempts_and_reraises(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.side_effect = requests.exceptions.ConnectionError("boom")
    client = OpenRouterClient(api_key="test-key", retry_backoff=0.0, max_attempts=4)

    with pytest.raises(requests.exceptions.ConnectionError):
        client.complete("some/model", "system", "user")

    assert mock_post.call_count == 4


# --- Fix 5: explicit max_tokens ---


def test_complete_sends_default_max_tokens(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(mocker, "hi")
    client = _fast_client()

    client.complete("some/model", "system", "user")

    assert mock_post.call_args.kwargs["json"]["max_tokens"] == 1024


def test_complete_max_tokens_is_overridable(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.return_value = _mock_response(mocker, "hi")
    client = OpenRouterClient(api_key="test-key", max_tokens=77, retry_backoff=0.0)

    client.complete("some/model", "system", "user")

    assert mock_post.call_args.kwargs["json"]["max_tokens"] == 77


# --- Fix 6: FormatFailure carries the raw model response ---


def test_format_failure_carries_raw_response_attribute():
    exc = FormatFailure("boom", raw_response="the raw text")

    assert exc.raw_response == "the raw text"
    assert str(exc) == "boom"


def test_format_failure_raw_response_defaults_to_none():
    assert FormatFailure("boom").raw_response is None


def test_complete_json_attaches_last_raw_response_to_format_failure(mocker):
    mock_post = mocker.patch("codenames_heb.llm_client.requests.post")
    mock_post.side_effect = [
        _mock_response(mocker, "first garbage"),
        _mock_response(mocker, "second garbage"),
    ]
    client = _fast_client()

    with pytest.raises(FormatFailure) as excinfo:
        client.complete_json("some/model", "system", "user", max_retries=2)

    assert excinfo.value.raw_response == "second garbage"
