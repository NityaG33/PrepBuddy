from services.embedding_service import generate_embeddings
from vectorstore.faiss_store import FAISSStore


documents = [
    {
        "text": "Database normalization reduces data redundancy.",
        "page": 1
    },
    {
        "text": "Indexes improve the speed of database queries.",
        "page": 2
    },
    {
        "text": "TCP uses congestion control to manage network traffic.",
        "page": 3
    }
]


texts = [document["text"] for document in documents]

embeddings = generate_embeddings(texts)

store = FAISSStore(embeddings.shape[1])

store.add(embeddings, documents)


query = "How can we reduce redundancy in a database?"

query_embedding = generate_embeddings([query])[0]

results = store.search(query_embedding, top_k=2)


for result in results:
    print("\nScore:", result["score"])
    print("Page:", result["document"]["page"])
    print("Text:", result["document"]["text"])