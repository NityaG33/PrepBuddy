import numpy as np
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
from services.hash_service import calculate_file_hash

from api import documents
from db.database import Base
from db.models import Document, Workspace




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


class TestDocumentUploadSuccess(unittest.TestCase):
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

    def test_successful_upload_persists_content_hash(self):
        pdf_content = b"%PDF-1.7\n"

        upload = UploadFile(
            filename="test.pdf",
            file=BytesIO(pdf_content),
        )

        class FakePipeline:
            def process(self, _file_path):
                return {
                    "pages": [
                        {"text": "Sample document content"}
                    ]
                }

        class FakeVectorStore:
            def add(self, _embeddings, _chunks):
                pass

        fake_vector_store = FakeVectorStore()

        with (
            patch.object(
                documents,
                "document_processing_pipeline",
                FakePipeline(),
            ),
            patch.object(
                documents,
                "create_chunks",
                return_value=[
                    {"text": "Sample document content"}
                ],
            ),
            patch.object(
                documents,
                "generate_embeddings",
                return_value=np.array([[0.1, 0.2, 0.3]]),
            ),
            patch.object(
                documents,
                "get_vector_store",
                return_value=fake_vector_store,
            ),
            patch.object(
                documents,
                "save_vector_store",
            ),
        ):
            response = asyncio.run(
                documents.upload_document(
                    upload,
                    None,
                    self.session,
                )
            )

        # Verify API response
        self.assertEqual(response["status"], "indexed")
        self.assertEqual(response["filename"], "test.pdf")
        self.assertEqual(response["total_pages"], 1)
        self.assertEqual(response["total_chunks"], 1)

        # Verify the persisted database record
        document = self.session.query(Document).one()

        self.assertEqual(document.status, "indexed")
        self.assertEqual(document.filename, "test.pdf")
        self.assertEqual(document.document_version, 1)

        # Verify the hash against the actual uploaded file
        expected_hash = calculate_file_hash(document.file_path)

        self.assertEqual(document.content_hash, expected_hash)
        self.assertEqual(len(document.content_hash), 64)

        # Verify the uploaded PDF exists
        self.assertTrue(Path(document.file_path).exists())


    def test_duplicate_upload_returns_409_and_skips_processing(self):
        pdf_content = b"%PDF-1.7\n"

        class FakePipeline:
            def process(self, _file_path):
                return {
                    "pages": [
                        {"text": "Sample document content"}
                    ]
                }

        class FakeVectorStore:
            def add(self, _embeddings, _chunks):
                pass

        fake_vector_store = FakeVectorStore()

        # First upload: successfully index the document.
        first_upload = UploadFile(
            filename="original.pdf",
            file=BytesIO(pdf_content),
        )

        with (
            patch.object(
                documents,
                "document_processing_pipeline",
                FakePipeline(),
            ),
            patch.object(
                documents,
                "create_chunks",
                return_value=[
                    {"text": "Sample document content"}
                ],
            ),
            patch.object(
                documents,
                "generate_embeddings",
                return_value=np.array([[0.1, 0.2, 0.3]]),
            ),
            patch.object(
                documents,
                "get_vector_store",
                return_value=fake_vector_store,
            ),
            patch.object(
                documents,
                "save_vector_store",
            ),
        ):
            first_response = asyncio.run(
                documents.upload_document(
                    first_upload,
                    None,
                    self.session,
                )
            )

        self.assertEqual(first_response["status"], "indexed")

        # Second upload: same PDF content, same workspace.
        second_upload = UploadFile(
            filename="duplicate.pdf",
            file=BytesIO(pdf_content),
        )

        with (
            patch.object(
                documents,
                "document_processing_pipeline",
            ) as mock_pipeline,
            patch.object(
                documents,
                "create_chunks",
            ) as mock_chunking,
            patch.object(
                documents,
                "generate_embeddings",
            ) as mock_embeddings,
            patch.object(
                documents,
                "get_vector_store",
            ) as mock_vector_store,
            patch.object(
                documents,
                "save_vector_store",
            ) as mock_save,
        ):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(
                    documents.upload_document(
                        second_upload,
                        None,
                        self.session,
                    )
                )

        # Verify the duplicate API response.
        error = raised.exception

        self.assertEqual(error.status_code, 409)
        self.assertEqual(
            error.detail["message"],
            "Duplicate document detected in this workspace",
        )

        # Verify the original document is identified.
        original_document = (
            self.session.query(Document)
            .filter_by(filename="original.pdf")
            .one()
        )

        self.assertEqual(
            error.detail["duplicate_document_id"],
            original_document.id,
        )

        # Verify the duplicate record is persisted as failed.
        duplicate_document = (
            self.session.query(Document)
            .filter_by(filename="duplicate.pdf")
            .one()
        )

        self.assertEqual(duplicate_document.status, "failed")
        self.assertEqual(
            duplicate_document.error_message,
            "Duplicate document detected in this workspace",
        )
        self.assertEqual(
            duplicate_document.content_hash,
            original_document.content_hash,
        )

        # Verify downstream processing was skipped.
        mock_pipeline.process.assert_not_called()
        mock_chunking.assert_not_called()
        mock_embeddings.assert_not_called()
        mock_vector_store.assert_not_called()
        mock_save.assert_not_called()


    def test_same_pdf_can_be_uploaded_to_different_workspaces(self):
        pdf_content = b"%PDF-1.7\n"

        # Create two separate workspaces.
        workspace_one = Workspace(name="Workspace 1")
        workspace_two = Workspace(name="Workspace 2")

        self.session.add_all([workspace_one, workspace_two])
        self.session.commit()

        self.session.refresh(workspace_one)
        self.session.refresh(workspace_two)

        class FakePipeline:
            def process(self, _file_path):
                return {
                    "pages": [
                        {"text": "Sample document content"}
                    ]
                }

        class FakeVectorStore:
            def add(self, _embeddings, _chunks):
                pass

        fake_vector_store = FakeVectorStore()

        def upload_to_workspace(filename, workspace_id):
            upload = UploadFile(
                filename=filename,
                file=BytesIO(pdf_content),
            )

            return asyncio.run(
                documents.upload_document(
                    upload,
                    workspace_id,
                    self.session,
                )
            )

        with (
            patch.object(
                documents,
                "document_processing_pipeline",
                FakePipeline(),
            ),
            patch.object(
                documents,
                "create_chunks",
                return_value=[
                    {"text": "Sample document content"}
                ],
            ),
            patch.object(
                documents,
                "generate_embeddings",
                return_value=np.array([[0.1, 0.2, 0.3]]),
            ),
            patch.object(
                documents,
                "get_vector_store",
                return_value=fake_vector_store,
            ),
            patch.object(
                documents,
                "save_vector_store",
            ),
        ):
            # Upload identical bytes into Workspace 1.
            first_response = upload_to_workspace(
                "original.pdf",
                workspace_one.id,
            )

            # Upload identical bytes into Workspace 2.
            second_response = upload_to_workspace(
                "same_content.pdf",
                workspace_two.id,
            )

        # Both uploads should succeed.
        self.assertEqual(first_response["status"], "indexed")
        self.assertEqual(second_response["status"], "indexed")

        # Verify each upload belongs to the correct workspace.
        first_document = (
            self.session.query(Document)
            .filter_by(filename="original.pdf")
            .one()
        )

        second_document = (
            self.session.query(Document)
            .filter_by(filename="same_content.pdf")
            .one()
        )

        self.assertEqual(
            first_document.workspace_id,
            workspace_one.id,
        )

        self.assertEqual(
            second_document.workspace_id,
            workspace_two.id,
        )

        # Both files have identical content fingerprints.
        self.assertEqual(
            first_document.content_hash,
            second_document.content_hash,
        )

        # Both documents were independently indexed.
        self.assertEqual(first_document.status, "indexed")
        self.assertEqual(second_document.status, "indexed")


if __name__ == "__main__":
    unittest.main()