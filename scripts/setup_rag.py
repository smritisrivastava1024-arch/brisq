import chromadb
from chromadb.utils import embedding_functions

# Read the policy document
with open("policies.txt", "r") as f:
    content = f.read()

# Split into chunks by double newline (each policy section)
chunks = [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]

print(f"Created {len(chunks)} policy chunks")

# Set up ChromaDB with a free local embedding model
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="store_policies",
    embedding_function=embedding_fn
)

# Add each chunk to the vector database
for i, chunk in enumerate(chunks):
    collection.add(
        documents=[chunk],
        ids=[f"policy_{i}"]
    )

print("Policy documents added to vector database successfully!")