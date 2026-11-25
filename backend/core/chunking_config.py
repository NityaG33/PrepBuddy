from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkingConfig:
    """Configuration for structure-aware document chunking."""

    target_tokens: int = 500
    overlap_tokens: int = 80
    max_tokens: int = 700
    min_tokens: int = 100

    def __post_init__(self):
        if self.target_tokens <= 0:
            raise ValueError("target_tokens must be positive")

        if self.overlap_tokens < 0:
            raise ValueError("overlap_tokens cannot be negative")

        if self.max_tokens < self.target_tokens:
            raise ValueError("max_tokens must be >= target_tokens")

        if self.min_tokens <= 0:
            raise ValueError("min_tokens must be positive")

        if self.overlap_tokens >= self.target_tokens:
            raise ValueError("overlap_tokens must be smaller than target_tokens")


DEFAULT_CHUNKING_CONFIG = ChunkingConfig()
