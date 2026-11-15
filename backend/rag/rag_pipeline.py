from rag.prompt import build_prompt
from services.llm_service import generate_answer


def answer_question(
    retriever,
    question: str,
    top_k: int = 5,
    workspace_id: int | None = None,
):

    retrieved_chunks = retriever.retrieve(
        question,
        top_k=top_k,
        workspace_id=workspace_id
    )

    if not retrieved_chunks:
        return {
            "answer": (
                "I couldn't find relevant information "
                "in the uploaded documents."
            ),
            "sources": []
        }

    prompt = build_prompt(
        question,
        retrieved_chunks
    )

    answer = generate_answer(prompt)

    sources = [
        {
            "document_id": result["document"].get("document_id"),
            "workspace_id": result["document"].get("workspace_id"),
            "filename": result["document"].get("filename"),
            "page": result["document"].get("page"),
            "score": result["score"],
        }
        for result in retrieved_chunks
    ]

    return {
        "answer": answer,
        "sources": sources
    }