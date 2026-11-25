from services.intelligent_chunking_service import (
    create_overlap_text,
    extract_block_contexts,
    fit_overlap_to_budget,
)
from schemas.document import Chunk
from services.intelligent_chunking_service import (
    BlockContext,
    assemble_chunks,
)
from core.chunking_config import ChunkingConfig

def test_extract_block_contexts_tracks_heading_hierarchy():
    document = {
        "pages": [
            {
                "page_number": 1,
                "blocks": [
                    {
                        "text": "Machine Learning",
                        "block_type": "heading",
                        "heading_level": 1,
                    },
                    {
                        "text": "Gradient Descent",
                        "block_type": "heading",
                        "heading_level": 2,
                    },
                    {
                        "text": "Learning Rate",
                        "block_type": "heading",
                        "heading_level": 3,
                    },
                    {
                        "text": "The learning rate controls step size.",
                        "block_type": "paragraph",
                    },
                    {
                        "text": "Momentum",
                        "block_type": "heading",
                        "heading_level": 2,
                    },
                    {
                        "text": "Momentum accelerates optimization.",
                        "block_type": "paragraph",
                    },
                ],
            }
        ]
    }

    contexts = extract_block_contexts(document)

    assert contexts[3].heading_path == [
        "Machine Learning",
        "Gradient Descent",
        "Learning Rate",
    ]

    assert contexts[5].heading_path == [
        "Machine Learning",
        "Momentum",
    ]


def test_extract_block_contexts_ignores_empty_blocks():
    document = {
        "pages": [
            {
                "page_number": 1,
                "blocks": [
                    {"text": "", "block_type": "paragraph"},
                    {"text": "   ", "block_type": "paragraph"},
                    {"text": "Useful content", "block_type": "paragraph"},
                ],
            }
        ]
    }

    contexts = extract_block_contexts(document)

    assert len(contexts) == 1
    assert contexts[0].text == "Useful content"


def test_extract_block_contexts_preserves_page_numbers():
    document = {
        "pages": [
            {
                "page_number": 1,
                "blocks": [
                    {"text": "Page one content", "block_type": "paragraph"},
                ],
            },
            {
                "page_number": 2,
                "blocks": [
                    {"text": "Page two content", "block_type": "paragraph"},
                ],
            },
        ]
    }

    contexts = extract_block_contexts(document)

    assert contexts[0].page_number == 1
    assert contexts[1].page_number == 2


class FakeTokenService:
    def count_tokens(self, text):
        return len(text.split())


def test_assemble_chunks_groups_blocks():
    contexts = [
        BlockContext(
            text="First paragraph",
            block_type="paragraph",
            page_number=1,
            heading_path=["Introduction"],
        ),
        BlockContext(
            text="Second paragraph",
            block_type="paragraph",
            page_number=1,
            heading_path=["Introduction"],
        ),
        BlockContext(
            text="Third paragraph",
            block_type="paragraph",
            page_number=2,
            heading_path=["Introduction"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        document_id=10,
    )

    assert len(chunks) == 1
    assert chunks[0].text == (
        "First paragraph\n\nSecond paragraph\n\nThird paragraph"
    )
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 2
    assert chunks[0].section_title == "Introduction"
    assert chunks[0].metadata["document_id"] == 10


def test_assemble_chunks_flushes_at_target():
    contexts = [
        BlockContext(
            text="one two three",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="four five six",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        config=ChunkingConfig(
            target_tokens=4,
            overlap_tokens=1,
            max_tokens=5,
            min_tokens=1,
        ),
    )

    assert len(chunks) == 2
    assert chunks[0].text == "one two three"
    assert chunks[1].text == "three\n\nfour five six"


def test_assemble_chunks_keeps_sections_separate():
    contexts = [
        BlockContext(
            text="Content from A",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="Content from B",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section B"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        document_id=1,
    )

    assert len(chunks) == 2
    assert chunks[0].section_title == "Section A"
    assert chunks[1].section_title == "Section B"



from schemas.document import Chunk
from services.intelligent_chunking_service import (
    BlockContext,
    assemble_chunks,
)


class FakeTokenService:
    def count_tokens(self, text):
        return len(text.split())

    def split_text(self, text, max_tokens):
        words = text.split()

        return [
            " ".join(words[i:i + max_tokens])
            for i in range(0, len(words), max_tokens)
        ]

    def get_last_tokens(self, text, num_tokens):
        if not text or num_tokens <= 0:
            return ""

        words = text.split()
        return " ".join(words[-num_tokens:])

    
def test_assemble_chunks_groups_blocks():
    contexts = [
        BlockContext(
            text="First paragraph",
            block_type="paragraph",
            page_number=1,
            heading_path=["Introduction"],
        ),
        BlockContext(
            text="Second paragraph",
            block_type="paragraph",
            page_number=1,
            heading_path=["Introduction"],
        ),
        BlockContext(
            text="Third paragraph",
            block_type="paragraph",
            page_number=2,
            heading_path=["Introduction"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        document_id=10,
    )

    assert len(chunks) == 1
    assert chunks[0].text == (
        "First paragraph\n\nSecond paragraph\n\nThird paragraph"
    )
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 2
    assert chunks[0].section_title == "Introduction"
    assert chunks[0].metadata["document_id"] == 10


def test_assemble_chunks_flushes_at_target():
    contexts = [
        BlockContext(
            text="one two three",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="four five six",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        config=ChunkingConfig(
            target_tokens=4,
            overlap_tokens=1,
            max_tokens=5,
            min_tokens=1,
        ),
    )

    assert len(chunks) == 2
    assert chunks[0].text == "one two three"
    assert chunks[1].text == "three\n\nfour five six"
    assert chunks[1].metadata["overlap_tokens"] == 1
    assert chunks[1].metadata["overlap_pages"] == [1]


def test_assemble_chunks_keeps_sections_separate():
    contexts = [
        BlockContext(
            text="Content from A",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="Content from B",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section B"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        document_id=1,
    )

    assert len(chunks) == 2
    assert chunks[0].section_title == "Section A"
    assert chunks[1].section_title == "Section B"




def test_split_oversized_context_splits_block():
    from services.intelligent_chunking_service import split_oversized_context

    block = BlockContext(
        text="one two three four five six",
        block_type="paragraph",
        page_number=2,
        heading_path=["Section A"],
    )

    parts = split_oversized_context(
        block,
        token_service=FakeTokenService(),
        max_tokens=2,
    )

    assert [part.text for part in parts] == [
        "one two",
        "three four",
        "five six",
    ]

    assert all(part.page_number == 2 for part in parts)
    assert all(part.heading_path == ["Section A"] for part in parts)


def test_split_oversized_context_keeps_small_block():
    from services.intelligent_chunking_service import split_oversized_context

    block = BlockContext(
        text="one two",
        block_type="paragraph",
        page_number=1,
        heading_path=["Section A"],
    )

    parts = split_oversized_context(
        block,
        token_service=FakeTokenService(),
        max_tokens=5,
    )

    assert len(parts) == 1
    assert parts[0].text == "one two"


def test_assemble_chunks_enforces_max_tokens():
    contexts = [
        BlockContext(
            text="one two three four five six seven eight",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        )
    ]

    config = ChunkingConfig(
        target_tokens=3,
        overlap_tokens=0,
        max_tokens=3,
        min_tokens=1,
    )

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        config=config,
        document_id=1,
    )

    assert len(chunks) == 3
    assert all(
        FakeTokenService().count_tokens(chunk.text) <= config.max_tokens
        for chunk in chunks
    )


def test_create_overlap_text_returns_trailing_context():
    service = FakeTokenService()

    result = create_overlap_text(
        previous_chunk_text="one two three four five",
        token_service=service,
        overlap_tokens=2,
    )

    assert result == "four five"


def test_create_overlap_text_returns_empty_for_invalid_input():
    service = FakeTokenService()

    assert create_overlap_text("", service, 5) == ""
    assert create_overlap_text("one two three", service, 0) == ""
    assert create_overlap_text("one two three", service, -1) == ""


def test_create_overlap_text_returns_all_when_text_is_shorter():
    service = FakeTokenService()

    result = create_overlap_text(
        previous_chunk_text="one two",
        token_service=service,
        overlap_tokens=5,
    )

    assert result == "one two"


def test_fit_overlap_to_budget_keeps_text_when_it_fits():
    service = FakeTokenService()

    result = fit_overlap_to_budget(
        "one two three",
        service,
        5,
    )

    assert result == "one two three"


def test_fit_overlap_to_budget_trims_text():
    service = FakeTokenService()

    result = fit_overlap_to_budget(
        "one two three four five",
        service,
        2,
    )

    assert result == "four five"


def test_fit_overlap_to_budget_returns_empty_for_invalid_input():
    service = FakeTokenService()

    assert fit_overlap_to_budget("", service, 5) == ""
    assert fit_overlap_to_budget("one two", service, 0) == ""
    assert fit_overlap_to_budget("one two", service, -1) == ""



def test_overlap_does_not_accumulate_recursively():
    contexts = [
        BlockContext(
            text="alpha beta gamma",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="delta epsilon zeta",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="eta theta iota",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        config=ChunkingConfig(
            target_tokens=4,
            overlap_tokens=1,
            max_tokens=5,
            min_tokens=1,
        ),
    )

    assert len(chunks) == 3

    assert chunks[0].text == "alpha beta gamma"

    assert chunks[1].text == "gamma\n\ndelta epsilon zeta"
    assert chunks[1].metadata["overlap_tokens"] == 1

    assert chunks[2].text == "zeta\n\neta theta iota"
    assert chunks[2].metadata["overlap_tokens"] == 1

    # The third chunk must not inherit "gamma" recursively.
    assert "gamma" not in chunks[2].text


def test_overlap_does_not_cross_section_boundaries():
    contexts = [
        BlockContext(
            text="alpha beta gamma",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="delta epsilon zeta",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section B"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        config=ChunkingConfig(
            target_tokens=4,
            overlap_tokens=1,
            max_tokens=5,
            min_tokens=1,
        ),
    )

    assert len(chunks) == 2

    assert chunks[0].text == "alpha beta gamma"
    assert chunks[1].text == "delta epsilon zeta"

    assert chunks[1].metadata["overlap_tokens"] == 0
    assert chunks[1].metadata["overlap_pages"] == []


def test_single_block_between_target_and_max_is_kept_intact():
    text = " ".join(["word"] * 6)

    contexts = [
        BlockContext(
            text=text,
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        )
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        config=ChunkingConfig(
            target_tokens=4,
            overlap_tokens=1,
            max_tokens=8,
            min_tokens=1,
        ),
    )

    assert len(chunks) == 1
    assert chunks[0].text == text
    assert FakeTokenService().count_tokens(chunks[0].text) == 6


def test_chunk_tracks_page_range_across_pages():
    contexts = [
        BlockContext(
            text="alpha beta",
            block_type="paragraph",
            page_number=2,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="gamma delta",
            block_type="paragraph",
            page_number=3,
            heading_path=["Section A"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        config=ChunkingConfig(
            target_tokens=10,
            overlap_tokens=0,
            max_tokens=10,
            min_tokens=1,
        ),
    )

    assert len(chunks) == 1
    assert chunks[0].page_start == 2
    assert chunks[0].page_end == 3
    assert chunks[0].section_title == "Section A"
    assert chunks[0].metadata["heading_path"] == ["Section A"]


def test_chunks_have_sequential_ids_and_metadata():
    contexts = [
        BlockContext(
            text="alpha beta gamma",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="delta epsilon zeta",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
    ]

    chunks = assemble_chunks(
        contexts,
        token_service=FakeTokenService(),
        config=ChunkingConfig(
            target_tokens=4,
            overlap_tokens=0,
            max_tokens=8,
            min_tokens=1,
        ),
        document_id=42,
    )

    assert len(chunks) == 2

    assert chunks[0].chunk_id == "42_chunk_0"
    assert chunks[1].chunk_id == "42_chunk_1"

    assert chunks[0].metadata["document_id"] == 42
    assert chunks[1].metadata["document_id"] == 42

    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[1].metadata["chunk_index"] == 1


def test_chunk_metadata_records_final_token_count():
    contexts = [
        BlockContext(
            text="alpha beta gamma",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
        BlockContext(
            text="delta epsilon zeta",
            block_type="paragraph",
            page_number=1,
            heading_path=["Section A"],
        ),
    ]

    token_service = FakeTokenService()

    chunks = assemble_chunks(
        contexts,
        token_service=token_service,
        config=ChunkingConfig(
            target_tokens=4,
            overlap_tokens=1,
            max_tokens=5,
            min_tokens=1,
        ),
    )

    for chunk in chunks:
        assert chunk.metadata["token_count"] == (
            token_service.count_tokens(chunk.text)
        )