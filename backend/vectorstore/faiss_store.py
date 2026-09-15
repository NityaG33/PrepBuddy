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

    def search(self, query_embedding, top_k: int = 5):

        query_embedding = np.array(
            [query_embedding],
            dtype="float32"
        )

        top_k = min(top_k, len(self.documents))

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for score, index in zip(scores[0], indices[0]):

            if index != -1:
                results.append({
                    "score": float(score),
                    "document": self.documents[index]
                })

        return results

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