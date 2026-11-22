import pytest
from pydantic import ValidationError

from schemas.document import RawPage, RawDocument, Chunk, RetrievalResult


def test_raw_page_validates_page_number():
    page = RawPage(
        page_number=1,
        text="Sample PDF content",
    )

    assert page.page_number == 1
    assert page.text == "Sample PDF content"


def test_raw_page_rejects_invalid_page_number():
    with pytest.raises(ValidationError):
        RawPage(
            page_number=0,
            text="Sample PDF content",
        )


def test_raw_document_creation():
    document = RawDocument(
        metadata={"title": "Sample"},
        pages=[
            RawPage(
                page_number=1,
                text="Page one",
            )
        ],
    )

    assert len(document.pages) == 1
    assert document.pages[0].page_number == 1


def test_chunk_creation():
    chunk = Chunk(
        chunk_id="chunk-001",
        text="Gradient descent is an optimization algorithm.",
        page_start=1,
        page_end=2,
        section_title="Gradient Descent",
    )

    assert chunk.chunk_id == "chunk-001"
    assert chunk.page_start == 1
    assert chunk.page_end == 2


def test_retrieval_result_creation():
    chunk = Chunk(
        chunk_id="chunk-001",
        text="Gradient descent is an optimization algorithm.",
        page_start=1,
        page_end=1,
    )

    result = RetrievalResult(
        chunk=chunk,
        score=0.85,
    )

    assert result.score == 0.85
    assert result.chunk.chunk_id == "chunk-001"


def test_chunk_rejects_unexpected_field():
    with pytest.raises(ValidationError):
        Chunk(
            chunk_id="chunk-001",
            text="Content",
            page_start=1,
            page_end=1,
            unexpected_field="not allowed",
        )


def test_chunk_rejects_invalid_page_range():
    with pytest.raises(ValidationError):
        Chunk(
            chunk_id="chunk-002",
            text="Content",
            page_start=5,
            page_end=2,
        )