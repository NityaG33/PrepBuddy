from services.embedding_service import generate_embeddings


class Retriever:

    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.4,
        workspace_id: int | None = None,
    ):
        query_embedding = generate_embeddings([query])[0]

        results = self.vector_store.search(
            query_embedding,
            top_k=top_k,
            workspace_id=workspace_id,
        )

        filtered_results = [
            result
            for result in results
            if result["score"] >= score_threshold
        ]

        return filtered_results