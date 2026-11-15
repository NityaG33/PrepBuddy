from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from vectorstore.store import get_vector_store
from rag.retriever import Retriever
from rag.rag_pipeline import answer_question


router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str
    top_k: int = 5
    workspace_id: int | None = None


@router.post("")
def chat(request: ChatRequest):

    vector_store = get_vector_store()

    if vector_store is None:
        raise HTTPException(
            status_code=400,
            detail="No documents have been uploaded yet"
        )

    retriever = Retriever(vector_store)

    result = answer_question(
        retriever,
        request.question,
        request.top_k,
        request.workspace_id
    )

    return result