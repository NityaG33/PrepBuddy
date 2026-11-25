
from transformers import AutoTokenizer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class TokenCountService:
    """Token counting and token-based text splitting."""

    def __init__(self, tokenizer=None, model_name: str = MODEL_NAME):
        self._tokenizer = tokenizer
        self.model_name = model_name

    @property
    def tokenizer(self):
        """Load tokenizer only when it is first needed."""
        if self._tokenizer is None:
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name
            )

        return self._tokenizer

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0

        token_ids = self.tokenizer.encode(
            text,
            add_special_tokens=False,
        )

        return len(token_ids)

    def split_text(self, text: str, max_tokens: int) -> list[str]:
        if not text:
            return []

        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        token_ids = self.tokenizer.encode(
            text,
            add_special_tokens=False,
        )

        chunks = []

        for start in range(0, len(token_ids), max_tokens):
            token_slice = token_ids[start:start + max_tokens]

            chunk_text = self.tokenizer.decode(
                token_slice,
                skip_special_tokens=True,
            ).strip()

            if chunk_text:
                chunks.append(chunk_text)

        return chunks

    def get_last_tokens(self, text: str, num_tokens: int) -> str:
        """Return the trailing N tokens from text."""
        if not text or num_tokens <= 0:
            return ""

        token_ids = self.tokenizer.encode(
            text,
            add_special_tokens=False,
        )

        trailing_ids = token_ids[-num_tokens:]

        return self.tokenizer.decode(
            trailing_ids,
            skip_special_tokens=True,
        ).strip()


