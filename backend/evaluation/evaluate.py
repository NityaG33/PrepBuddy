import json

from services.embedding_service import generate_embeddings
from services.pdf_service import extract_text_from_pdf
from services.chunking_service import create_chunks
from vectorstore.faiss_store import FAISSStore
from rag.retriever import Retriever


PDF_PATH = "data/DBMS.pdf"


def load_test_cases():

    with open(
        "evaluation/test_cases.json",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def build_retriever():

    pages = extract_text_from_pdf(PDF_PATH)

    chunks = create_chunks(pages)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = generate_embeddings(texts)

    store = FAISSStore(
        embeddings.shape[1]
    )

    store.add(
        embeddings,
        chunks
    )

    return Retriever(store)


def evaluate():

    test_cases = load_test_cases()

    retriever = build_retriever()

    correct = 0

    for test_case in test_cases:

        results = retriever.retrieve(
            test_case["question"],
            top_k=5
        )

        retrieved_pages = [
            result["document"]["page"]
            for result in results
        ]

        expected_pages = test_case["expected_pages"]

        is_correct = any(
            page in expected_pages
            for page in retrieved_pages
        )

        if is_correct:
            correct += 1

        print("\nQuestion:", test_case["question"])
        print("Expected:", expected_pages)
        print("Retrieved:", retrieved_pages)
        print("Correct:", is_correct)

    accuracy = correct / len(test_cases)

    print("\n-------------------------")
    print(f"Retrieval Accuracy: {accuracy:.2%}")
    print("-------------------------")


if __name__ == "__main__":
    evaluate()