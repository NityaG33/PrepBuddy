from typing import Any
from pydantic import model_validator
from pydantic import BaseModel, ConfigDict, Field



class DocumentSchema(BaseModel):
    """Base schema for document-related data contracts."""

    model_config = ConfigDict(extra="forbid")


class RawPage(DocumentSchema):
    page_number: int = Field(ge=1)
    text: str
    blocks: list[dict[str, Any]] = Field(default_factory=list)
    body_font_size: float | None = None


class RawDocument(DocumentSchema):
    metadata: dict[str, Any] = Field(default_factory=dict)
    pages: list[RawPage]


class NormalizedBlock(DocumentSchema):
    text: str
    block_type: str
    page_number: int = Field(ge=1)
    bbox: list[float] | None = None
    heading_level: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedPage(DocumentSchema):
    page_number: int = Field(ge=1)
    text: str
    blocks: list[NormalizedBlock] = Field(default_factory=list)


class NormalizedDocument(DocumentSchema):
    metadata: dict[str, Any] = Field(default_factory=dict)
    pages: list[NormalizedPage]


class Chunk(DocumentSchema):
    chunk_id: str
    text: str
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    section_title: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode="after")
    def validate_page_range(self):
        if self.page_end < self.page_start:
            raise ValueError("page_end cannot be less than page_start")

        return self


class RetrievalResult(DocumentSchema):
    chunk: Chunk
    score: float