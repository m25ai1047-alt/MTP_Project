import chromadb
from sentence_transformers import SentenceTransformer
from config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
)

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

# Using a lightweight, efficient embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of text chunks."""
    try:
        embeddings = embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return []

def upsert_to_chromadb(chunks: list[dict]):
    """Index code chunks with embeddings in ChromaDB."""
    if not chunks:
        return

    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]

        ids = [chunk['id'] for chunk in batch_chunks]
        documents = [chunk['code'] for chunk in batch_chunks]
        metadatas = [chunk['metadata'] for chunk in batch_chunks]

        embeddings = generate_embeddings(documents)

        if not embeddings:
            print(f"Skipping batch {i//batch_size + 1} due to embedding failure")
            continue

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print(f"Indexed {len(batch_chunks)} code chunks")
