from schemas.document import Chunk
from core.chunking_config import DEFAULT_CHUNKING_CONFIG, ChunkingConfig
from services.token_count_service import TokenCountService
from dataclasses import dataclass


@dataclass
class BlockContext:
    """A normalized block enriched with its section context."""

    text: str
    block_type: str
    page_number: int
    heading_path: list[str]


def _get_value(obj, key, default=None):
    """Read a value from either a dictionary or a Pydantic object."""
    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def extract_block_contexts(document) -> list[BlockContext]:
    """Extract normalized blocks while tracking heading hierarchy."""

    contexts = []
    heading_stack = []

    pages = _get_value(document, "pages", [])

    for page in pages:
        page_number = _get_value(page, "page_number")

        blocks = _get_value(page, "blocks", [])

        for block in blocks:
            text = _get_value(block, "text", "")

            if not text or not text.strip():
                continue

            block_type = _get_value(block, "block_type", "paragraph")
            heading_level = _get_value(block, "heading_level")

            if block_type == "heading":
                if heading_level is None:
                    heading_level = 1

                heading_level = max(1, heading_level)

                heading_stack = heading_stack[:heading_level - 1]
                heading_stack.append(text.strip())

            contexts.append(
                BlockContext(
                    text=text.strip(),
                    block_type=block_type,
                    page_number=page_number,
                    heading_path=heading_stack.copy(),
                )
            )

    return contexts



def split_oversized_context(
    block: BlockContext,
    token_service: TokenCountService,
    max_tokens: int,
) -> list[BlockContext]:
    """Split a single block if it exceeds the hard token limit."""

    block_tokens = token_service.count_tokens(block.text)

    if block_tokens <= max_tokens:
        return [block]

    text_parts = token_service.split_text(
        block.text,
        max_tokens=max_tokens,
    )

    return [
        BlockContext(
            text=part,
            block_type=block.block_type,
            page_number=block.page_number,
            heading_path=block.heading_path.copy(),
        )
        for part in text_parts
    ]


def create_overlap_text(
    previous_chunk_text: str,
    token_service: TokenCountService,
    overlap_tokens: int,
) -> str:
    """Extract trailing token context from the previous chunk."""
    if not previous_chunk_text or overlap_tokens <= 0:
        return ""

    return token_service.get_last_tokens(
        previous_chunk_text,
        overlap_tokens,
    )


def fit_overlap_to_budget(
    overlap_text: str,
    token_service: TokenCountService,
    available_tokens: int,
) -> str:
    """Trim overlap context to fit the available token budget."""
    if not overlap_text or available_tokens <= 0:
        return ""

    overlap_tokens = token_service.count_tokens(overlap_text)

    if overlap_tokens <= available_tokens:
        return overlap_text

    return token_service.get_last_tokens(
        overlap_text,
        available_tokens,
    )


def assemble_chunks(
    contexts: list[BlockContext],
    token_service: TokenCountService,
    config: ChunkingConfig = DEFAULT_CHUNKING_CONFIG,
    document_id: int | None = None,
) -> list[Chunk]:
    chunks = []

    current_blocks = []
    current_section = None

    current_overlap = ""
    current_overlap_pages = []

    pending_overlap = ""
    pending_overlap_pages = []

    def source_text():
        return "\n\n".join(block.text for block in current_blocks)

    def source_token_count():
        return token_service.count_tokens(source_text())

    def flush(allow_overlap=True):
        nonlocal current_blocks, current_section
        nonlocal current_overlap, current_overlap_pages
        nonlocal pending_overlap, pending_overlap_pages

        if not current_blocks:
            return

        actual_source_text = source_text()
        source_pages = sorted(
            {block.page_number for block in current_blocks}
        )

        rendered_text = actual_source_text

        if current_overlap:
            rendered_text = f"{current_overlap}\n\n{actual_source_text}"

        overlap_token_count = token_service.count_tokens(
            current_overlap
        )

        final_token_count = token_service.count_tokens(
            rendered_text.strip()
        )

        metadata = {
            "document_id": document_id,
            "chunk_index": len(chunks),
            "heading_path": current_blocks[0].heading_path.copy(),
            "block_types": [block.block_type for block in current_blocks],
            "overlap_tokens": overlap_token_count,
            "overlap_pages": current_overlap_pages.copy(),
            "token_count": final_token_count,
        }

        chunks.append(
            Chunk(
                chunk_id=f"{document_id or 'doc'}_chunk_{len(chunks)}",
                text=rendered_text.strip(),
                page_start=min(source_pages),
                page_end=max(source_pages),
                section_title=(
                    current_blocks[0].heading_path[-1]
                    if current_blocks[0].heading_path
                    else None
                ),
                metadata=metadata,
            )
        )

        # Derive the next overlap exclusively from source content.
        if allow_overlap:
            pending_overlap = create_overlap_text(
                actual_source_text,
                token_service,
                config.overlap_tokens,
            )
            pending_overlap_pages = source_pages.copy()
        else:
            pending_overlap = ""
            pending_overlap_pages = []

        current_blocks = []
        current_section = None
        current_overlap = ""
        current_overlap_pages = []

    def start_chunk(block):
        nonlocal current_blocks, current_section
        nonlocal current_overlap, current_overlap_pages

        block_tokens = token_service.count_tokens(block.text)

        current_section = block.heading_path

        # Apply pending overlap only if it leaves room for the block.
        overlap_budget = max(
            0,
            config.target_tokens - block_tokens,
        )

        current_overlap = fit_overlap_to_budget(
            pending_overlap,
            token_service,
            overlap_budget,
        )

        current_overlap_pages = (
            pending_overlap_pages.copy() if current_overlap else []
        )

        current_blocks = [block]

    for original_block in contexts:
        if original_block.block_type == "heading":
            continue

        if not original_block.text.strip():
            continue

        block_parts = split_oversized_context(
            original_block,
            token_service,
            config.max_tokens,
        )

        for block in block_parts:
            block_tokens = token_service.count_tokens(block.text)

            if block_tokens == 0:
                continue

            section_path = block.heading_path

            # A section change is a hard boundary.
            if current_blocks and section_path != current_section:
                flush(allow_overlap=False)
                pending_overlap = ""
                pending_overlap_pages = []

            if not current_blocks:
                start_chunk(block)
                continue

            proposed_tokens = (
                token_service.count_tokens(current_overlap)
                + source_token_count()
                + block_tokens
            )

            # Flush when the target would be exceeded.
            if proposed_tokens > config.target_tokens:
                flush(allow_overlap=True)
                start_chunk(block)
                continue

            # Hard safety check before appending.
            final_tokens = (
                token_service.count_tokens(current_overlap)
                + source_token_count()
                + block_tokens
            )

            if final_tokens > config.max_tokens:
                flush(allow_overlap=True)
                start_chunk(block)
                continue

            current_blocks.append(block)

    flush(allow_overlap=False)

    return chunks