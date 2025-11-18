import os
from pathlib import Path

# ChromaDB configuration
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(BASE_DIR / "code_indexer" / "chroma_db_storage"))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "java_code_analysis")

# LLM configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")

# Search configuration
HYBRID_SEARCH_WEIGHT = float(os.getenv("HYBRID_SEARCH_WEIGHT", "0.7"))  # Weight for semantic vs keyword
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
