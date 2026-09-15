from services.embedding_service import generate_embeddings
from vectorstore.faiss_store import FAISSStore
from rag.retriever import Retriever
from rag.rag_pipeline import answer_question


documents = [
    {
        "text": "Database normalization reduces data redundancy and improves data consistency.",
        "page": 1
    },
    {
        "text": "Indexes improve the speed of database queries by allowing faster data retrieval.",
        "page": 2
    },
    {
        "text": "TCP uses congestion control to regulate network traffic and prevent congestion.",
        "page": 3
    }
]


texts = [document["text"] for document in documents]

embeddings = generate_embeddings(texts)

store = FAISSStore(embeddings.shape[1])

store.add(
    embeddings,
    documents
)

retriever = Retriever(store)


question = "How does database normalization help?"

result = answer_question(
    retriever,
    question
)


print("\nANSWER:")
print(result["answer"])

print("\nSOURCES:")

for source in result["sources"]:
    print(
        f"Page {source['document']['page']} "
        f"(score: {source['score']:.3f})"
    )