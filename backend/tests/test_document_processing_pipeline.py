import unittest

from services.document_processing.base import PDFProcessor
from services.document_processing.normalizer import DocumentNormalizer
from services.document_processing.pipeline import DocumentProcessingPipeline


class FakePDFProcessor(PDFProcessor):
    """
    A fake processor used only for testing.

    It avoids opening a real file, so this test checks pipeline behavior
    without depending on PyMuPDF or a real PDF.
    """

    def __init__(self, raw_document):
        self.raw_document = raw_document
        self.received_file_path = None

    def extract(self, file_path: str):
        self.received_file_path = file_path

        return self.raw_document


class FailingPDFProcessor(PDFProcessor):
    """A fake processor that simulates an invalid PDF."""

    def extract(self, file_path: str):
        raise ValueError("The uploaded file is not a valid PDF")


class TestDocumentProcessingPipeline(unittest.TestCase):
    def test_processes_raw_document_with_the_normalizer(self):
        raw_document = {
            "metadata": {"title": "Pipeline Test"},
            "page_count": 1,
            "pages": [
                {
                    "page_number": 1,
                    "blocks": [
                        {
                            "bbox": (50, 50, 400, 70),
                            "lines": [
                                {
                                    "bbox": (50, 50, 400, 70),
                                    "spans": [
                                        {
                                            "text": "Pipeline test paragraph.",
                                            "bbox": (50, 50, 400, 70),
                                            "font": "Arial",
                                            "font_size": 12.0,
                                            "flags": 0,
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        processor = FakePDFProcessor(raw_document)

        pipeline = DocumentProcessingPipeline(
            processor=processor,
            normalizer=DocumentNormalizer(),
        )

        result = pipeline.process("example.pdf")

        self.assertEqual(processor.received_file_path, "example.pdf")
        self.assertEqual(result["metadata"]["title"], "Pipeline Test")
        self.assertEqual(result["pages"][0]["page"], 1)
        self.assertEqual(
            result["blocks"][0]["text"],
            "Pipeline test paragraph.",
        )

    def test_propagates_processing_errors(self):
        pipeline = DocumentProcessingPipeline(
            processor=FailingPDFProcessor(),
            normalizer=DocumentNormalizer(),
        )

        with self.assertRaisesRegex(ValueError, "not a valid PDF"):
            pipeline.process("broken.pdf")


if __name__ == "__main__":
    unittest.main()