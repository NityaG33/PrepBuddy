from services.embedding_service import generate_embeddings


texts = [
    "Database normalization reduces data redundancy.",
    "Normalization organizes database tables efficiently.",
    "Cricket is played between two teams."
]

embeddings = generate_embeddings(texts)

print("Number of embeddings:", len(embeddings))
print("Embedding dimensions:", embeddings.shape)
print(embeddings[0])