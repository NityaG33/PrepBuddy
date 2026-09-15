from services.pdf_service import extract_text_from_pdf
from services.chunking_service import create_chunks
from services.embedding_service import generate_embeddings
from vectorstore.faiss_store import FAISSStore


def index_pdf(file_path: str):

    pages = extract_text_from_pdf(file_path)

    chunks = create_chunks(pages)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = generate_embeddings(texts)

    store = FAISSStore(embeddings.shape[1])

    store.add(embeddings, chunks)

    return store, chunks