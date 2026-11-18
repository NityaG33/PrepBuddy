import os

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.config import UPLOAD_DIR
from db.database import get_db
from db.models import Document, Workspace
from services.chunking_service import create_chunks
from services.document_processing.pipeline import (
    create_default_document_processing_pipeline,
)
from services.embedding_service import generate_embeddings
from vectorstore.faiss_store import FAISSStore
from vectorstore.store import (
    get_vector_store,
    set_vector_store,
    save_vector_store,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

document_processing_pipeline = (
    create_default_document_processing_pipeline()
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
):
    # 1. Validate the uploaded file
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    # 2. Find the requested workspace or create a default one
    if workspace_id is not None:
        workspace = db.get(Workspace, workspace_id)

        if workspace is None:
            raise HTTPException(
                status_code=404,
                detail="Workspace not found",
            )
    else:
        workspace = db.query(Workspace).first()

        if workspace is None:
            workspace = Workspace(name="Default Workspace")
            db.add(workspace)
            db.commit()
            db.refresh(workspace)

    # 3. Save the uploaded PDF persistently
    original_filename = Path(file.filename).name
    stored_filename = f"{uuid4().hex}_{original_filename}"
    file_path = UPLOAD_DIR / stored_filename

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    file_path.write_bytes(file_bytes)

    # 4. Create a database record before processing
    document = Document(
        workspace_id=workspace.id,
        filename=original_filename,
        file_path=str(file_path),
        status="uploaded",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        # 5. Mark the document as processing
        document.status = "processing"
        db.commit()

        # 6. Extract structured PDF content
        normalized_document = document_processing_pipeline.process(
            str(file_path)
        )

        # `pages` is a compatibility view used by our current fixed-size chunker.
        # Phase 3 will replace that chunker with one that reads structured blocks.
        pages = normalized_document["pages"]

        # 7. Create chunks
        chunks = create_chunks(pages)

        # Attach document identity to every chunk
        for chunk in chunks:
            chunk["document_id"] = document.id
            chunk["workspace_id"] = workspace.id
            chunk["filename"] = document.filename

        if not chunks:
            raise ValueError(
                "No text could be extracted from the PDF"
            )

        # 8. Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings(texts)

        # 9. Get or create the FAISS vector store
        vector_store = get_vector_store()

        if vector_store is None:
            vector_store = FAISSStore(embeddings.shape[1])
            set_vector_store(vector_store)

        # 10. Add vectors and metadata to FAISS
        vector_store.add(embeddings, chunks)

        # 11. Persist the FAISS index
        save_vector_store()

        # 12. Mark the document as indexed
        document.status = "indexed"
        document.page_count = len(pages)
        document.chunk_count = len(chunks)
        document.error_message = None

        db.commit()
        db.refresh(document)

        return {
            "document_id": document.id,
            "workspace_id": workspace.id,
            "filename": document.filename,
            "status": document.status,
            "total_pages": document.page_count,
            "total_chunks": document.chunk_count,
            "message": "Document indexed successfully",
        }

    except ValueError as exc:
        # ValueError represents an expected document-processing problem:
        # for example, a corrupt PDF or a PDF with no extractable text.
        document.status = "failed"
        document.error_message = str(exc)[:2000]
        db.commit()

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Any other exception is unexpected: database, vector-store,
        # embedding-service, or programming failures.
        document.status = "failed"
        document.error_message = str(exc)[:2000]
        db.commit()

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the document",
        ) from exc


@router.get("/workspace/{workspace_id}")
def list_workspace_documents(
    workspace_id: int,
    db: Session = Depends(get_db),
):
    # Check that the workspace exists
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .first()
    )

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    # Get documents belonging to this workspace
    documents = (
        db.query(Document)
        .filter(Document.workspace_id == workspace_id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return {
        "workspace_id": workspace_id,
        "documents": [
            {
                "id": document.id,
                "filename": document.filename,
                "status": document.status,
                "page_count": document.page_count,
                "chunk_count": document.chunk_count,
                "error_message": document.error_message,
                "created_at": document.created_at,
            }
            for document in documents
        ],
    }


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    # Find the document record
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    file_path = document.file_path

    # Delete the database record
    db.delete(document)
    db.commit()

    # Remove its chunks from FAISS
    vector_store = get_vector_store()
    removed_chunks = 0

    if vector_store is not None:
        removed_chunks = vector_store.remove_document(
            document_id
        )
        save_vector_store()

    # Delete the uploaded PDF from disk
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    return {
        "message": "Document deleted successfully",
        "document_id": document_id,
        "removed_chunks": removed_chunks,
    }