
from abc import ABC, abstractmethod
from typing import Any


class PDFProcessor(ABC):
    """
    Common interface for PDF extraction implementations.

    Every PDF processor must implement the extract() method
    and return a standardized extraction result.
    """

    @abstractmethod
    def extract(self, file_path: str) -> dict[str, Any]:
        """
        Extract structured content from a PDF.

        Expected result:
        {
            "metadata": {},
            "pages": [
                {
                    "page": 1,
                    "blocks": [
                        {
                            "text": "...",
                            "bbox": (...),
                            "font_sizes": [...],
                            "fonts": [...],
                            "is_bold": False,
                        }
                    ]
                }
            ]
        }
        """
        raise NotImplementedError
