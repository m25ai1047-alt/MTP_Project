import os
from config import PROJECT_PATH
from parser_enhanced import extract_method_chunks_enhanced, get_statistics
from vector_store import upsert_to_chromadb


def crawl_and_index_project_enhanced(use_enhanced_parser=True):
    """
    Crawls the entire project directory, finds all Java files,
    and indexes them in a single run with enhanced parsing.

    Args:
        use_enhanced_parser: If True, use enhanced parser with rich metadata
    """
    print(f"--- Starting Enhanced Bulk Indexing for project at: {PROJECT_PATH} ---")
    print(f"Parser: {'Enhanced (AST + Metadata)' if use_enhanced_parser else 'Basic'}\n")

    java_files_found = 0
    java_files_failed = 0
    chunks_indexed = 0
    all_chunks = []

    # Import appropriate parser
    if use_enhanced_parser:
        from parser_enhanced import extract_method_chunks_enhanced as extract_func
    else:
        from parser import extract_method_chunks as extract_func

    # os.walk recursively visits all directories and files from the root path
    for root, dirs, files in os.walk(PROJECT_PATH):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in [
            'target', 'build', '.git', 'node_modules', 'dist', 'out'
        ]]

        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                java_files_found += 1

                print(f"[{java_files_found}] Processing: {file_path}")

                # Use the parsing logic
                chunks = extract_func(file_path)

                if chunks:
                    all_chunks.extend(chunks)
                    chunks_indexed += len(chunks)
                    print(f"    ✓ Extracted {len(chunks)} chunk(s)")
                else:
                    java_files_failed += 1
                    print(f"    ✗ Failed to parse")

    # Index all chunks in batches
    if all_chunks:
        print(f"\n--- Indexing {len(all_chunks)} chunks into ChromaDB ---")
        upsert_to_chromadb(all_chunks)

    # Generate and display statistics
    print("\n" + "="*60)
    print("           INDEXING STATISTICS")
    print("="*60)

    if use_enhanced_parser:
        stats = get_statistics(all_chunks)
        print(f"Total Java files processed: {java_files_found}")
        print(f"Files successfully parsed: {java_files_found - java_files_failed}")
        print(f"Files failed: {java_files_failed}")
        print(f"\nTotal chunks indexed: {stats['total_chunks']}")
        print(f"  - Complete methods: {stats['total_methods']}")
        print(f"  - Split method blocks: {stats['split_chunks']}")
        print(f"\nMicroservices detected: {stats['microservices']}")
        print(f"Average cyclomatic complexity: {stats['avg_complexity']:.2f}")
        print(f"\nCode quality metrics:")
        print(f"  - Large methods (>100 lines): {stats['large_methods']}")
        print(f"  - Complex methods (complexity > 10): {stats['complex_methods']}")
    else:
        print(f"Total Java files processed: {java_files_found}")
        print(f"Total chunks indexed: {chunks_indexed}")

    print("="*60)
    print("\n✓ Bulk indexing complete!\n")

    return all_chunks


def show_microservice_topology(chunks):
    """Display detected microservice topology."""
    if not chunks:
        print("No chunks to analyze.")
        return

    microservices = {}
    for chunk in chunks:
        ms = chunk['metadata'].get('microservice', 'unknown')
        if ms not in microservices:
            microservices[ms] = {'methods': set(), 'files': set()}
        microservices[ms]['methods'].add(chunk['metadata'].get('method_name', 'unknown'))
        microservices[ms]['files'].add(chunk['metadata'].get('file_path', 'unknown'))

    print("\n" + "="*60)
    print("         MICROSERVICE TOPOLOGY")
    print("="*60)

    for ms, data in sorted(microservices.items()):
        print(f"\n📦 {ms}")
        print(f"   Methods: {len(data['methods'])}")
        print(f"   Files: {len(data['files'])}")

    print("="*60 + "\n")


if __name__ == "__main__":
    # Ensure the project path is valid before starting
    if not os.path.isdir(PROJECT_PATH):
        print(f"Error: The provided PROJECT_PATH is not a valid directory.")
        print(f"Path: {PROJECT_PATH}")
    else:
        chunks = crawl_and_index_project_enhanced(use_enhanced_parser=True)

        # Optionally show topology
        if chunks:
            show_microservice_topology(chunks)
