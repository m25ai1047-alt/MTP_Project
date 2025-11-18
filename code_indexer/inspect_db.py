import os
import sys
import chromadb
import json
from pathlib import Path

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db_storage")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "java_code_analysis")

def inspect_collection(limit=5):
    """Display contents of the ChromaDB collection."""

    db_path = Path(CHROMA_DB_PATH)
    if not db_path.exists():
        print(f"Database not found at {CHROMA_DB_PATH}")
        print("Run the code indexer first: python bulk_indexer.py")
        return

    print(f"Inspecting ChromaDB at: {CHROMA_DB_PATH}")
    print("-" * 80)

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    try:
        collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
        count = collection.count()

        print(f"Collection: {CHROMA_COLLECTION_NAME}")
        print(f"Total items: {count}")

        if count == 0:
            print("\nCollection is empty")
            return

        results = collection.get(limit=min(limit, count))

        print(f"\nShowing {min(limit, count)} samples:\n")

        for i in range(len(results['ids'])):
            print(f"\n{'='*80}")
            print(f"Item {i+1}")
            print(f"{'='*80}")
            print(f"ID: {results['ids'][i]}")

            metadata = results['metadatas'][i]
            print(f"\nFile: {metadata.get('file_path', 'N/A')}")
            print(f"Method: {metadata.get('method_name', 'N/A')}")
            print(f"Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}")

            code = results['documents'][i]
            print(f"\nCode:\n{code[:200]}...")

    except Exception as e:
        print(f"Error: {e}")
        print("Collection may not exist or database is corrupted")
        return 1

    return 0

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    return inspect_collection(limit)

if __name__ == "__main__":
    sys.exit(main())
