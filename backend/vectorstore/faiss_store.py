import faiss  # type: ignore[import-not-found]
import numpy as np


class FAISSStore:

    def __init__(self, dimension: int):
        self.index = faiss.IndexFlatIP(dimension)
        self.documents = []

    def add(self, embeddings, documents):

        embeddings = np.array(
            embeddings,
            dtype="float32"
        )

        self.index.add(embeddings)
        self.documents.extend(documents)

    def search(
        self,
        query_embedding,
        top_k: int = 5,
        workspace_id: int | None = None,
    ):
        if len(self.documents) == 0 or top_k <= 0:
            return []

        query_embedding = np.array(
            [query_embedding],
            dtype="float32",
        )

        # Search all indexed vectors so workspace filtering
        # happens before choosing the top_k results.
        scores, indices = self.index.search(
            query_embedding,
            len(self.documents),
        )

        results = []

        for score, index in zip(scores[0], indices[0]):
            if index == -1:
                continue

            document = self.documents[index]

            # Filter by workspace when one is specified.
            if workspace_id is not None:
                if document.get("workspace_id") != workspace_id:
                    continue

            results.append({
                "score": float(score),
                "document": document,
            })

        return results[:top_k]

    def save(self, index_path: str, metadata_path: str):

        faiss.write_index(
            self.index,
            index_path
        )

        np.save(
            metadata_path,
            np.array(
                self.documents,
                dtype=object
            ),
            allow_pickle=True
        )

    @classmethod
    def load(cls, index_path: str, metadata_path: str):

        store = cls.__new__(cls)

        store.index = faiss.read_index(index_path)

        store.documents = np.load(
            metadata_path,
            allow_pickle=True
        ).tolist()

        return store


    def remove_documents(self, document_ids: set[int]) -> int:
        if not document_ids:
            return 0

        # Keep only chunks that do not belong to the documents being deleted
        keep_indices = [
            i
            for i, document in enumerate(self.documents)
            if document.get("document_id") not in document_ids
        ]

        removed_count = len(self.documents) - len(keep_indices)

        if removed_count == 0:
            return 0

        # Reconstruct vectors for the remaining chunks
        if keep_indices:
            embeddings = np.vstack([
                self.index.reconstruct(i)
                for i in keep_indices
            ]).astype("float32")
        else:
            embeddings = np.empty(
                (0, self.index.d),
                dtype="float32",
            )

        # Keep matching metadata
        remaining_documents = [
            self.documents[i]
            for i in keep_indices
        ]

        # Rebuild the FAISS index
        self.index = faiss.IndexFlatIP(self.index.d)

        if len(embeddings) > 0:
            self.index.add(embeddings)

        self.documents = remaining_documents

        return removed_count


    def remove_document(self, document_id: int) -> int:
        # Reuse the bulk deletion method for one document
        return self.remove_documents({document_id})