def build_prompt(question: str, retrieved_chunks: list):

    context_parts = []

    for i, result in enumerate(retrieved_chunks, start=1):

        document = result["document"]

        context_parts.append(
            f"[Source {i}]\n"
            f"Page: {document['page']}\n"
            f"Content:\n{document['text']}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are an interview preparation assistant.

Answer the user's question using ONLY the provided context.

If the answer cannot be found in the context,
clearly say that the information is not available
in the provided documents.

Do not make up information.

User Question:
{question}

Context:
{context}

Instructions:
- Answer using Markdown formatting.
- Use clear headings where appropriate.
- Use bullet points for lists.
- Use numbered lists for step-by-step explanations.
- Use **bold** for important concepts.
- Use code blocks for code.
- Keep paragraphs short and readable.
- Do not use unnecessary headings.
- Do not invent information that isn't supported by the context.
"""

    return prompt