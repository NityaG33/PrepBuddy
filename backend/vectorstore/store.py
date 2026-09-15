import os

from vectorstore.faiss_store import FAISSStore


vector_store = None

INDEX_PATH = "data/faiss.index"
METADATA_PATH = "data/metadata.npy"


def get_vector_store():
    return vector_store


def set_vector_store(store):
    global vector_store
    vector_store = store


def load_vector_store():

    global vector_store

    if (
        os.path.exists(INDEX_PATH)
        and os.path.exists(METADATA_PATH)
    ):
        vector_store = FAISSStore.load(
            INDEX_PATH,
            METADATA_PATH
        )

    return vector_store


def save_vector_store():

    if vector_store is not None:
        vector_store.save(
            INDEX_PATH,
            METADATA_PATH
        )