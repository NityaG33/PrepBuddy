import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException

from services.pdf_service import extract_text_from_pdf
from services.chunking_service import create_chunks
from services.embedding_service import generate_embeddings
from vectorstore.faiss_store import FAISSStore
from vectorstore.store import (
    get_vector_store,
    set_vector_store,
    save_vector_store
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    file_bytes = await file.read()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as temp_file:

        temp_file.write(file_bytes)
        temp_file_path = temp_file.name

    try:
        # 1. Extract text
        pages = extract_text_from_pdf(temp_file_path)

        # 2. Create chunks
        chunks = create_chunks(pages)

        # 3. Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings(texts)

        # 4. Get existing vector store
        vector_store = get_vector_store()

        # 5. Create FAISS index if one doesn't exist
        if vector_store is None:
            vector_store = FAISSStore(
                embeddings.shape[1]
            )

            set_vector_store(vector_store)

        # 6. Add embeddings + metadata
        vector_store.add(
            embeddings,
            chunks
        )

        # 7. Persist vector store
        save_vector_store()

        return {
            "filename": file.filename,
            "total_pages": len(pages),
            "total_chunks": len(chunks),
            "message": "Document indexed successfully"
        }

    finally:
        os.remove(temp_file_path)