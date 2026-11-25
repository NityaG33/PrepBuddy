
import pytest

from services.token_count_service import TokenCountService


class FakeTokenizer:
    """Lightweight tokenizer for isolated unit tests."""

    def encode(self, text, add_special_tokens=False):
        return text.split()

    def decode(self, token_ids, skip_special_tokens=True):
        return " ".join(token_ids)


@pytest.fixture
def token_service():
    return TokenCountService(tokenizer=FakeTokenizer())


def test_count_tokens(token_service):
    assert token_service.count_tokens("hello world") == 2


def test_count_tokens_empty_text(token_service):
    assert token_service.count_tokens("") == 0


def test_split_text_respects_max_tokens(token_service):
    text = "one two three four five six"
    chunks = token_service.split_text(text, max_tokens=2)

    assert chunks == ["one two", "three four", "five six"]


def test_split_text_keeps_final_partial_chunk(token_service):
    text = "one two three four five"
    chunks = token_service.split_text(text, max_tokens=2)

    assert chunks == ["one two", "three four", "five"]


def test_split_text_empty_text(token_service):
    assert token_service.split_text("", max_tokens=2) == []


def test_split_text_rejects_invalid_max_tokens(token_service):
    with pytest.raises(ValueError):
        token_service.split_text("hello world", max_tokens=0)


def test_get_last_tokens_returns_trailing_tokens():
    service = TokenCountService(tokenizer=FakeTokenizer())

    text = "one two three four five"

    result = service.get_last_tokens(text, 2)

    assert result == "four five"


def test_get_last_tokens_returns_all_when_requested_more():
    service = TokenCountService(tokenizer=FakeTokenizer())

    result = service.get_last_tokens("one two three", 10)

    assert result == "one two three"


def test_get_last_tokens_returns_empty_for_invalid_input():
    service = TokenCountService(tokenizer=FakeTokenizer())

    assert service.get_last_tokens("", 5) == ""
    assert service.get_last_tokens("one two", 0) == ""
    assert service.get_last_tokens("one two", -1) == ""
