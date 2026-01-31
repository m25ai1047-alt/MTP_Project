"""
Enhanced retrieval strategy that leverages rich metadata for better RCA.

Improvements:
1. Service-aware filtering (restrict search to relevant microservice)
2. Complexity-based ranking (prefer simpler methods for clarity)
3. Call chain expansion (include called methods)
4. Signature matching (exact parameter type matching)
"""

import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple
import re
from config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
    HYBRID_SEARCH_WEIGHT,
    TOP_K_RESULTS
)


class EnhancedCodeRetriever:
    """
    Enhanced retriever that leverages metadata for smarter code retrieval.
    """

    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        try:
            self.collection = self.chroma_client.get_collection(name=CHROMA_COLLECTION_NAME)
        except:
            print(f"Warning: Collection '{CHROMA_COLLECTION_NAME}' not found.")
            self.collection = self.chroma_client.create_collection(name=CHROMA_COLLECTION_NAME)

        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def extract_microservice_from_error(self, error_log: str) -> str:
        """
        Attempt to extract microservice name from error log.

        Examples:
        - "org.train.ticket.booking.service..." -> booking
        - "PaymentService.java" -> payment
        """
        # Try extracting from package names
        packages = re.findall(r'([a-z]+)\.(?:service|controller|repository)', error_log.lower())
        if packages:
            return packages[0]

        # Try extracting from class names (CamelCase to lowercase)
        classes = re.findall(r'at\s+[\w.]*([A-Z][a-zA-Z]+Service)[\w.]*\(', error_log)
        if classes:
            # Convert CamelCase to lowercase: BookingService -> booking
            service_name = re.sub(r'([A-Z])', r'_\1', classes[0]).lower().split('_')[1]
            return service_name

        return None

    def search(self, query: str, top_k: int = TOP_K_RESULTS,
               microservice_filter: str = None) -> List[Dict]:
        """
        Perform enhanced hybrid search with metadata filtering.

        Args:
            query: Error log or search query
            top_k: Number of results to return
            microservice_filter: Optional microservice name to filter by
        """
        # Get all documents
        all_docs = self.collection.get()

        if not all_docs or not all_docs['documents']:
            return []

        # Filter by microservice if specified
        if microservice_filter:
            filtered_indices = []
            for idx, metadata in enumerate(all_docs['metadatas']):
                if metadata.get('microservice', '').lower() == microservice_filter.lower():
                    filtered_indices.append(idx)

            if not filtered_indices:
                print(f"Warning: No documents found for microservice '{microservice_filter}'")
                # Fall back to all documents
                filtered_indices = list(range(len(all_docs['documents'])))

            # Filter the documents
            filtered_ids = [all_docs['ids'][i] for i in filtered_indices]
            filtered_docs = [all_docs['documents'][i] for i in filtered_indices]
            filtered_metadatas = [all_docs['metadatas'][i] for i in filtered_indices]

            # Create temporary filtered view
            all_docs = {
                'ids': filtered_ids,
                'documents': filtered_docs,
                'metadatas': filtered_metadatas
            }

        # Semantic search using embeddings
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k * 3, len(all_docs['documents']))
        )

        # Keyword search using BM25
        tokenized_docs = [doc.lower().split() for doc in all_docs['documents']]
        bm25 = BM25Okapi(tokenized_docs)
        keyword_scores = bm25.get_scores(query.lower().split())

        # Also search in metadata (class names, method names, signatures)
        metadata_text = []
        for metadata in all_docs['metadatas']:
            text_parts = [
                metadata.get('method_name', ''),
                metadata.get('class', ''),
                metadata.get('signature', ''),
                ' '.join(metadata.get('called_methods', []))
            ]
            metadata_text.append(' '.join(text_parts).lower())

        # Boost keyword scores for metadata matches
        for idx, meta_text in enumerate(metadata_text):
            query_terms = set(query.lower().split())
            meta_terms = set(meta_text.split())
            matches = query_terms.intersection(meta_terms)
            keyword_scores[idx] += len(matches) * 2  # Boost metadata matches

        # Combine scores using weighted approach
        combined_scores = {}

        # Add semantic search scores
        if semantic_results and semantic_results['ids']:
            for idx, doc_id in enumerate(semantic_results['ids'][0]):
                # Only include if in filtered set
                if doc_id in all_docs['ids']:
                    distance = semantic_results['distances'][0][idx]
                    # Convert distance to similarity score
                    similarity = 1 / (1 + distance)
                    combined_scores[doc_id] = HYBRID_SEARCH_WEIGHT * similarity

        # Add keyword search scores
        for idx, doc_id in enumerate(all_docs['ids']):
            score = (1 - HYBRID_SEARCH_WEIGHT) * keyword_scores[idx]

            # Apply complexity penalty (prefer simpler methods for clarity)
            complexity = all_docs['metadatas'][idx].get('cyclomatic_complexity', 1)
            if complexity > 10:
                score *= 0.8  # 20% penalty for very complex methods

            # Apply large method penalty
            lines = all_docs['metadatas'][idx].get('lines_of_code', 0)
            if lines > 100:
                score *= 0.7  # 30% penalty for very large methods

            if doc_id in combined_scores:
                combined_scores[doc_id] += score
            else:
                combined_scores[doc_id] = score

        # Sort by combined score and get top k
        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Retrieve full documents
        results = []
        for doc_id, score in sorted_ids:
            idx = all_docs['ids'].index(doc_id)
            result = {
                'id': doc_id,
                'code': all_docs['documents'][idx],
                'metadata': all_docs['metadatas'][idx],
                'score': score
            }

            # Add explanation of why this was selected
            result['selection_reasons'] = self._explain_selection(
                query, all_docs['metadatas'][idx], score
            )

            results.append(result)

        return results

    def _explain_selection(self, query: str, metadata: dict, score: float) -> List[str]:
        """Explain why a code snippet was selected."""
        reasons = []

        # Check method name match
        method_name = metadata.get('method_name', '')
        if method_name.lower() in query.lower():
            reasons.append(f"Method name '{method_name}' matches query")

        # Check class name match
        class_name = metadata.get('class', '')
        if class_name and class_name.lower() in query.lower():
            reasons.append(f"Class '{class_name}' matches query")

        # Check microservice match
        microservice = metadata.get('microservice', '')
        if microservice and microservice.lower() in query.lower():
            reasons.append(f"Microservice '{microservice}' context")

        # Check called methods
        called_methods = metadata.get('called_methods', [])
        query_terms = set(query.lower().split())
        for called in called_methods:
            if called.lower() in query_terms:
                reasons.append(f"Calls '{called}' which appears in query")

        # Check exception handling
        if metadata.get('has_try_catch') and 'exception' in query.lower():
            reasons.append("Contains exception handling logic")

        if not reasons:
            reasons.append("Semantic similarity to error pattern")

        return reasons

    def expand_with_call_chain(self, results: List[Dict], max_depth: int = 1) -> List[Dict]:
        """
        Expand results with related methods from call chain.

        For each result, also retrieve:
        - Methods called by this method
        - Methods in the same class
        - Methods in the same microservice
        """
        if not results:
            return results

        all_doc_ids = self.collection.get()['ids']
        expanded_results = list(results)

        for result in results:
            metadata = result['metadata']
            method_name = metadata.get('method_name', '')
            called_methods = metadata.get('called_methods', [])
            microservice = metadata.get('microservice', '')
            class_name = metadata.get('class', '')

            # Find called methods
            if called_methods:
                all_docs = self.collection.get()
                for idx, doc_metadata in enumerate(all_docs['metadatas']):
                    if (doc_metadata.get('method_name') in called_methods and
                        doc_metadata.get('id') not in [r['id'] for r in expanded_results]):
                        # Add called method
                        expanded_results.append({
                            'id': all_docs['ids'][idx],
                            'code': all_docs['documents'][idx],
                            'metadata': doc_metadata,
                            'score': result['score'] * 0.7,  # Lower score for related methods
                            'selection_reasons': [f"Called by '{method_name}'"]
                        })

                        if len(expanded_results) >= len(results) * 2:
                            break

        return expanded_results[:len(results) * 2]  # Limit expansion


# Convenience function for backward compatibility
def hybrid_search_with_metadata(query: str, top_k: int = TOP_K_RESULTS,
                                use_microservice_filter: bool = True) -> List[Dict]:
    """
    Perform hybrid search with optional microservice filtering.

    Args:
        query: Search query or error log
        top_k: Number of results
        use_microservice_filter: Whether to auto-detect and filter by microservice
    """
    retriever = EnhancedCodeRetriever()

    microservice = None
    if use_microservice_filter:
        microservice = retriever.extract_microservice_from_error(query)
        if microservice:
            print(f"Detected microservice: {microservice}")

    results = retriever.search(query, top_k=top_k, microservice_filter=microservice)

    # Optionally expand with call chain
    # results = retriever.expand_with_call_chain(results)

    return results
