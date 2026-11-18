from services.chunking_service import create_chunks
from services.document_processing.pipeline import (
    create_default_document_processing_pipeline,
)
from services.embedding_service import generate_embeddings
from vectorstore.faiss_store import FAISSStore


def index_pdf(file_path: str):
    """
    Process one PDF, create chunks, generate embeddings, and return
    a new FAISS store.

    This helper does not save the store globally. The upload API handles
    persistent storage separately through its existing vector-store flow.
    """
    document_processing_pipeline = (
        create_default_document_processing_pipeline()
    )

    normalized_document = document_processing_pipeline.process(file_path)

    # The current chunker still consumes page text.
    # Phase 3 will replace it with structure-aware chunking.
    chunks = create_chunks(normalized_document["pages"])

    if not chunks:
        raise ValueError("No text could be extracted from the PDF")

    texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(texts)

    store = FAISSStore(embeddings.shape[1])
    store.add(embeddings, chunks)

    return store, chunks
