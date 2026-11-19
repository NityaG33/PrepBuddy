import asyncio
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import UploadFile

from api import documents
from db.database import Base
from db.models import Document


class TestDocumentUploadFailures(unittest.TestCase):
    def setUp(self):
        self.temp_directory = TemporaryDirectory()
        self.upload_dir = Path(self.temp_directory.name) / "uploads"
        self.upload_dir.mkdir()
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.settings = patch.multiple(
            documents,
            UPLOAD_DIR=self.upload_dir,
            MAX_PDF_UPLOAD_BYTES=16,
            UPLOAD_READ_CHUNK_BYTES=4,
        )
        self.settings.start()
        self.addCleanup(self.settings.stop)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()
        self.temp_directory.cleanup()

    def run_upload(self, filename: str, content: bytes) -> HTTPException:
        upload = UploadFile(filename=filename, file=BytesIO(content))

        with self.assertRaises(HTTPException) as raised:
            asyncio.run(documents.upload_document(upload, None, self.session))

        return raised.exception

    def test_size_failure_is_distinct_and_persisted(self):
        error = self.run_upload("large.pdf", b"%PDF-" + b"x" * 20)

        self.assertEqual(error.status_code, 400)
        self.assertEqual(
            error.detail,
            "Uploaded PDF exceeds the configured size limit",
        )
        self.assert_failed_document(error.detail)

    def test_signature_failure_is_distinct_and_persisted(self):
        error = self.run_upload("not-a-pdf.pdf", b"not a PDF")

        self.assertEqual(error.status_code, 400)
        self.assertEqual(
            error.detail,
            "Uploaded file does not have a valid PDF signature",
        )
        self.assert_failed_document(error.detail)

    def test_processing_error_does_not_expose_parser_details(self):
        class FailingPipeline:
            def process(self, _file_path):
                raise RuntimeError("internal parser diagnostic")

        with patch.object(
            documents,
            "document_processing_pipeline",
            FailingPipeline(),
        ):
            error = self.run_upload("valid.pdf", b"%PDF-1.7\n")

        self.assertEqual(error.status_code, 500)
        self.assertEqual(
            error.detail,
            "An unexpected error occurred while processing the document",
        )
        self.assertNotIn("internal parser diagnostic", error.detail)
        self.assert_failed_document(
            "internal parser diagnostic",
            file_exists=True,
        )

    def assert_failed_document(
        self,
        expected_error: str,
        *,
        file_exists: bool = False,
    ):
        document = self.session.query(Document).one()

        self.assertEqual(document.status, "failed")
        self.assertIn(expected_error, document.error_message)
        self.assertEqual(Path(document.file_path).exists(), file_exists)


if __name__ == "__main__":
    unittest.main()
