import re
import chromadb
import requests
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
    LLM_API_KEY,
    LLM_API_URL,
    LLM_MODEL,
    HYBRID_SEARCH_WEIGHT,
    TOP_K_RESULTS
)

# Optional: Use enhanced retrieval if available
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code_indexer'))
    from retrieval_enhanced import EnhancedCodeRetriever
    USE_ENHANCED_RETRIEVAL = True
except ImportError:
    USE_ENHANCED_RETRIEVAL = False
    print("Note: Enhanced retrieval not available, using standard retrieval")

class HybridCodeRetriever:
    """Retrieves relevant code using hybrid semantic + keyword search."""

    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        try:
            self.collection = self.chroma_client.get_collection(name=CHROMA_COLLECTION_NAME)
        except:
            print(f"Warning: Collection '{CHROMA_COLLECTION_NAME}' not found. Creating new collection.")
            self.collection = self.chroma_client.create_collection(name=CHROMA_COLLECTION_NAME)

        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Dict]:
        """Perform hybrid search combining semantic and keyword matching."""

        # Get all documents for keyword search
        all_docs = self.collection.get()

        if not all_docs or not all_docs['documents']:
            return []

        # Semantic search using embeddings
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k * 2, len(all_docs['documents']))
        )

        # Keyword search using BM25
        tokenized_docs = [doc.lower().split() for doc in all_docs['documents']]
        bm25 = BM25Okapi(tokenized_docs)
        keyword_scores = bm25.get_scores(query.lower().split())

        # Combine scores using weighted approach
        combined_scores = {}

        # Add semantic search scores
        if semantic_results and semantic_results['ids']:
            for idx, doc_id in enumerate(semantic_results['ids'][0]):
                distance = semantic_results['distances'][0][idx]
                # Convert distance to similarity score (lower distance = higher similarity)
                similarity = 1 / (1 + distance)
                combined_scores[doc_id] = HYBRID_SEARCH_WEIGHT * similarity

        # Add keyword search scores
        for idx, (doc_id, score) in enumerate(zip(all_docs['ids'], keyword_scores)):
            if doc_id in combined_scores:
                combined_scores[doc_id] += (1 - HYBRID_SEARCH_WEIGHT) * score
            else:
                combined_scores[doc_id] = (1 - HYBRID_SEARCH_WEIGHT) * score

        # Sort by combined score and get top k
        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Retrieve full documents
        results = []
        for doc_id, score in sorted_ids:
            idx = all_docs['ids'].index(doc_id)
            results.append({
                'id': doc_id,
                'code': all_docs['documents'][idx],
                'metadata': all_docs['metadatas'][idx],
                'score': score
            })

        return results

class RCAAnalyzer:
    """Performs root cause analysis using LLM."""

    def __init__(self, use_enhanced=None):
        # Auto-detect whether to use enhanced retrieval
        if use_enhanced is None:
            use_enhanced = USE_ENHANCED_RETRIEVAL

        if use_enhanced:
            self.retriever = EnhancedCodeRetriever()
            self.enhanced_mode = True
        else:
            self.retriever = HybridCodeRetriever()
            self.enhanced_mode = False

    def _extract_error_keywords(self, error_log: str) -> List[str]:
        """Extract key terms from error log for better retrieval."""
        keywords = []

        # Extract exception types
        exceptions = re.findall(r'(\w+Exception|\w+Error)', error_log)
        keywords.extend(exceptions)

        # Extract class/method names
        classes = re.findall(r'at\s+([a-zA-Z0-9_.]+)\(', error_log)
        keywords.extend(classes)

        # Extract other technical terms
        tech_terms = re.findall(r'\b(timeout|connection|database|null|failed|error)\b', error_log.lower())
        keywords.extend(tech_terms)

        return list(set(keywords))

    def _build_prompt(self, error_log: str, code_context: List[Dict]) -> str:
        """Construct analysis prompt for LLM with enhanced metadata."""

        context_section = ""
        if code_context:
            context_section = "\n\nRelevant code snippets:\n"
            for i, ctx in enumerate(code_context, 1):
                metadata = ctx.get('metadata', {})
                file_path = metadata.get('file_path', 'Unknown')
                method_name = metadata.get('method_name', 'Unknown')
                signature = metadata.get('signature', method_name)
                microservice = metadata.get('microservice', '')
                class_name = metadata.get('class', '')
                complexity = metadata.get('cyclomatic_complexity', 'N/A')
                start_line = metadata.get('start_line', '?')
                end_line = metadata.get('end_line', '?')

                # Build header with enhanced metadata
                header = f"--- Snippet {i} ---\n"
                if microservice:
                    header += f"Service: {microservice} | "
                header += f"Class: {class_name}\n"
                header += f"Method: {signature}\n"
                header += f"Location: {file_path}:{start_line}-{end_line}\n"
                if complexity != 'N/A':
                    header += f"Complexity: {complexity}\n"

                # Add selection reasons if available
                reasons = ctx.get('selection_reasons', [])
                if reasons:
                    header += f"Relevance: {', '.join(reasons)}\n"

                context_section += f"{header}\n{ctx['code']}\n"

        return f"""You are an experienced software engineer analyzing a production error in a microservices architecture.

Error log:
{error_log}
{context_section}

Based on the error log and code context above, provide a comprehensive root cause analysis:

1. **Root Cause**: What specifically caused this error?
2. **Location**: Which method, class, and service is the source?
3. **Analysis**: Explain the code flow that led to this error
4. **Fix**: Provide specific code changes to fix this issue
5. **Prevention**: How to prevent similar errors in the future

Keep the analysis technical, specific, and actionable."""

    def _call_llm(self, prompt: str) -> str:
        """Call LLM API for analysis."""

        if not LLM_API_KEY:
            return "LLM API key not configured. Please set LLM_API_KEY environment variable."

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert software engineer specializing in debugging and root cause analysis."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }

        try:
            response = requests.post(LLM_API_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                return "Unable to get analysis from LLM."

        except requests.exceptions.Timeout:
            return "LLM request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Error calling LLM API: {str(e)}"

    def analyze(self, error_log: str) -> Dict:
        """Perform complete RCA analysis with optional microservice filtering."""

        # Enhance query with extracted keywords
        keywords = self._extract_error_keywords(error_log)
        enhanced_query = f"{error_log} {' '.join(keywords)}"

        # Retrieve relevant code
        if self.enhanced_mode:
            # Use enhanced retrieval with microservice detection
            microservice = self.retriever.extract_microservice_from_error(error_log)
            code_context = self.retriever.search(enhanced_query, microservice_filter=microservice)
        else:
            code_context = self.retriever.search(enhanced_query)

        # Build prompt and get analysis
        prompt = self._build_prompt(error_log, code_context)
        analysis = self._call_llm(prompt)

        result = {
            "error_log": error_log,
            "analysis": analysis,
            "relevant_code": code_context,
            "keywords_extracted": keywords
        }

        # Add mode indicator
        if self.enhanced_mode:
            result["retrieval_mode"] = "enhanced"
            result["microservice_detected"] = self.retriever.extract_microservice_from_error(error_log)
        else:
            result["retrieval_mode"] = "standard"

        return result

def perform_root_cause_analysis(error_log: str) -> Dict:
    """Main entry point for RCA."""
    analyzer = RCAAnalyzer()
    return analyzer.analyze(error_log)
