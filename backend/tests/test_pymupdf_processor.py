from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pymupdf

from services.document_processing.pymupdf_processor import PyMuPDFProcessor


class TestPyMuPDFProcessor(unittest.TestCase):
    def setUp(self):
        """
        Runs before every test.

        It creates a fresh temporary folder and a very small PDF inside it.
        Each test starts with clean, predictable data.
        """
        self.temp_directory = TemporaryDirectory()
        self.temp_path = Path(self.temp_directory.name)
        self.processor = PyMuPDFProcessor()

        self.valid_pdf_path = self.temp_path / "sample.pdf"

        document = pymupdf.open()
        page = document.new_page()

        page.insert_text(
            (72, 72),
            "PrepBuddy PDF processing test",
            fontsize=12,
            fontname="helv",
        )

        document.set_metadata(
            {
                "title": "PrepBuddy Test PDF",
                "author": "PrepBuddy",
            }
        )

        document.save(self.valid_pdf_path)
        document.close()

    def tearDown(self):
        """
        Runs after every test and deletes the temporary test folder.
        """
        self.temp_directory.cleanup()

    def test_extracts_text_and_layout_from_valid_pdf(self):
        result = self.processor.extract(str(self.valid_pdf_path))

        self.assertEqual(result["page_count"], 1)
        self.assertEqual(result["metadata"]["title"], "PrepBuddy Test PDF")
        self.assertEqual(len(result["pages"]), 1)

        page = result["pages"][0]
        self.assertEqual(page["page_number"], 1)
        self.assertGreater(len(page["blocks"]), 0)

        extracted_text = " ".join(
            span["text"]
            for block in page["blocks"]
            for line in block["lines"]
            for span in line["spans"]
        )

        self.assertIn("PrepBuddy PDF processing test", extracted_text)

    def test_raises_error_when_file_does_not_exist(self):
        missing_file = self.temp_path / "missing.pdf"

        with self.assertRaises(FileNotFoundError):
            self.processor.extract(str(missing_file))

    def test_rejects_non_pdf_extension(self):
        text_file = self.temp_path / "notes.txt"
        text_file.write_text("This is not a PDF", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Only PDF files"):
            self.processor.extract(str(text_file))

    def test_rejects_invalid_pdf_content(self):
        broken_pdf = self.temp_path / "broken.pdf"
        broken_pdf.write_text("This is not really a PDF", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "not a valid PDF"):
            self.processor.extract(str(broken_pdf))


if __name__ == "__main__":
    unittest.main()