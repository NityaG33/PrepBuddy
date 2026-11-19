from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.upload_validation import UploadValidationError, save_pdf_upload


class FakeUpload:
    """Small UploadFile substitute used to test streaming behavior."""

    def __init__(self, content: bytes):
        self.content = content
        self.position = 0
        self.closed = False

    async def read(self, size: int) -> bytes:
        chunk = self.content[self.position : self.position + size]
        self.position += len(chunk)
        return chunk

    async def close(self) -> None:
        self.closed = True


class TestUploadValidation(unittest.TestCase):
    def setUp(self):
        self.temp_directory = TemporaryDirectory()
        self.destination = Path(self.temp_directory.name) / "document.pdf"

    def tearDown(self):
        self.temp_directory.cleanup()

    def save(self, upload: FakeUpload, **overrides: int) -> int:
        options = {
            "max_upload_bytes": 100,
            "read_chunk_bytes": 4,
            **overrides,
        }
        coroutine = save_pdf_upload(upload, self.destination, **options)

        # FakeUpload's async methods complete immediately, so the coroutine
        # can be exercised without creating a platform-specific event loop.
        # This keeps the unit test focused on validation behavior.
        try:
            coroutine.send(None)
        except StopIteration as completed:
            return completed.value

        self.fail("FakeUpload unexpectedly yielded control")

    def test_streams_valid_pdf_without_reading_all_at_once(self):
        upload = FakeUpload(b"%PDF-1.7\nminimal content")

        bytes_written = self.save(upload)

        self.assertEqual(bytes_written, len(b"%PDF-1.7\nminimal content"))
        self.assertEqual(self.destination.read_bytes(), b"%PDF-1.7\nminimal content")
        self.assertTrue(upload.closed)

    def test_rejects_upload_larger_than_limit_and_cleans_temporary_file(self):
        upload = FakeUpload(b"%PDF-" + b"x" * 100)

        with self.assertRaisesRegex(UploadValidationError, "size limit"):
            self.save(upload, max_upload_bytes=20)

        self.assertFalse(self.destination.exists())
        self.assertFalse(
            self.destination.with_suffix(".pdf.uploading").exists()
        )
        self.assertTrue(upload.closed)

    def test_rejects_file_without_pdf_signature(self):
        upload = FakeUpload(b"not a PDF")

        with self.assertRaisesRegex(UploadValidationError, "PDF signature"):
            self.save(upload)

        self.assertFalse(self.destination.exists())
        self.assertTrue(upload.closed)

    def test_rejects_empty_upload(self):
        upload = FakeUpload(b"")

        with self.assertRaisesRegex(UploadValidationError, "empty"):
            self.save(upload)

        self.assertFalse(self.destination.exists())
        self.assertTrue(upload.closed)
