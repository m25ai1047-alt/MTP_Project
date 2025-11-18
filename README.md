# Automated Root Cause Analysis System

An intelligent system for automated root cause analysis of production issues in microservices using anomaly detection and RAG (Retrieval-Augmented Generation).

## Overview

This system addresses the challenge of high MTTR (Mean Time to Resolution) in large-scale enterprise systems by:
- Automatically detecting anomalies in log data
- Retrieving relevant code context using hybrid search
- Generating root cause analysis using LLMs

## Architecture

The system consists of three main components:

### 1. Anomaly Detection
- Uses Isolation Forest for unsupervised anomaly detection
- TF-IDF vectorization of log messages
- Identifies unusual patterns in production logs

### 2. Code Indexer (RAG Knowledge Base)
- Parses Java source code into method-level chunks
- Generates embeddings using sentence-transformers
- Stores in ChromaDB for efficient retrieval
- Supports hybrid search (semantic + keyword)

### 3. RCA Agent
- Hybrid retrieval combining semantic and keyword search (BM25)
- LLM-powered analysis with code context
- REST API and CLI interfaces

## Installation

### Prerequisites
- Python 3.8+
- Java project to index (optional)

### Setup

1. Clone the repository and install dependencies:

```bash
# Install anomaly detector dependencies
cd anomaly_detector
pip install -r requirements.txt

# Install code indexer dependencies
cd ../code_indexer
pip install -r requirements.txt

# Install RCA agent dependencies
cd ../rca_agent
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
# Create .env file in project root
export CHROMA_DB_PATH="./code_indexer/chroma_db_storage"
export LLM_API_KEY="your-openai-api-key"
export LLM_MODEL="gpt-3.5-turbo"
export PROJECT_PATH="/path/to/your/java/project"
```

## Usage

### Step 1: Train Anomaly Detection Model

First, collect normal logs from your application during stable operation:

```bash
cd anomaly_detector
python train_model.py data/normal_logs.csv 0.1
```

The CSV should have a `log_message` column with log entries.

### Step 2: Index Your Codebase

Index your Java codebase for code retrieval:

```bash
cd code_indexer
# Update PROJECT_PATH in config.py
python bulk_indexer.py
```

For continuous indexing:
```bash
python main.py  # Watches for file changes
```

### Step 3: Run RCA Analysis

#### Option A: CLI
```bash
cd rca_agent
python cli.py "ERROR: NullPointerException at com.example.UserService.getUser(UserService.java:42)"
```

#### Option B: REST API
```bash
cd rca_agent
python main_rca_agent.py
```

Then make requests:
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"error_log": "ERROR: Database connection timeout..."}'
```

#### Option C: Complete Pipeline
```bash
# Analyze single error
python pipeline.py "ERROR: Connection timeout at DatabaseService.java:123"

# Process log file
python pipeline.py logs/production.log
```

## Project Structure

```
Log Analyser/
├── anomaly_detector/          # Anomaly detection module
│   ├── train_model.py        # Train Isolation Forest
│   ├── detect_anomalies.py   # Detection logic
│   └── requirements.txt
├── code_indexer/             # Code indexing and RAG
│   ├── parser.py             # Java code parser
│   ├── vector_store.py       # ChromaDB integration
│   ├── bulk_indexer.py       # Batch indexing
│   ├── main.py               # File watcher
│   └── requirements.txt
├── rca_agent/                # RCA analysis engine
│   ├── rca_service.py        # Core RCA logic with hybrid search
│   ├── main_rca_agent.py     # FastAPI server
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration
│   └── requirements.txt
├── pipeline.py               # End-to-end pipeline
└── README.md
```

## Key Features

### Hybrid Search
The system implements hybrid search combining:
- **Semantic Search**: Vector similarity using embeddings (all-MiniLM-L6-v2)
- **Keyword Search**: BM25 for exact term matching
- **Weighted Combination**: Configurable weight (default 70% semantic, 30% keyword)

This ensures both conceptual relevance and precise matching of error codes, class names, etc.

### Error Keyword Extraction
Automatically extracts:
- Exception types (NullPointerException, TimeoutException)
- Stack trace elements (class and method names)
- Technical terms (timeout, connection, database)

### Context-Aware Analysis
The LLM receives:
- Original error log
- Top-k most relevant code snippets
- Metadata (file paths, method names, line numbers)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CHROMA_DB_PATH` | ChromaDB storage path | `./code_indexer/chroma_db_storage` |
| `LLM_API_KEY` | OpenAI API key | - |
| `LLM_MODEL` | Model to use | `gpt-3.5-turbo` |
| `LLM_PROVIDER` | LLM provider | `openai` |
| `HYBRID_SEARCH_WEIGHT` | Semantic vs keyword weight | `0.7` |
| `TOP_K_RESULTS` | Number of code snippets to retrieve | `5` |
| `PROJECT_PATH` | Java project to index | `/path/to/project` |

## API Reference

### POST /analyze
Analyze an error log and return root cause analysis.

**Request:**
```json
{
  "error_log": "ERROR: NullPointerException at UserService.getUser",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "error_log": "ERROR: NullPointerException...",
  "analysis": "Root cause analysis...",
  "relevant_code": [...],
  "keywords_extracted": ["NullPointerException", "UserService"]
}
```

### GET /health
Health check endpoint.

## Development

### Adding Support for Other Languages

To support languages beyond Java, modify `code_indexer/parser.py`:

```python
# Example for Python
from tree_sitter_languages import get_parser
parser = get_parser('python')
```

### Customizing LLM Prompts

Edit the `_build_prompt` method in `rca_agent/rca_service.py` to customize analysis prompts.

### Adjusting Anomaly Detection

Tune the Isolation Forest parameters in `anomaly_detector/train_model.py`:
- `contamination`: Expected proportion of anomalies
- `n_estimators`: Number of trees
- `max_features`: Features per tree

## Troubleshooting

**Issue: No code chunks found**
- Ensure PROJECT_PATH is set correctly
- Run `python code_indexer/bulk_indexer.py` to index
- Check ChromaDB at `$CHROMA_DB_PATH`

**Issue: LLM API errors**
- Verify LLM_API_KEY is set
- Check API quota and rate limits
- Test with: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $LLM_API_KEY"`

**Issue: Poor anomaly detection**
- Retrain with more representative normal logs
- Adjust contamination parameter
- Ensure training data has diverse normal patterns

## Performance

- **Indexing**: ~100 Java files/minute (depends on file size)
- **RCA Latency**: ~2-5 seconds (depends on LLM API)
- **Storage**: ~1MB per 1000 code chunks

## Future Enhancements

- Support for multi-language codebases
- Integration with Jira for historical incident data
- Fine-tuned embeddings for domain-specific code
- Real-time log streaming integration
- Advanced conversation context tracking

## License

MIT License - See LICENSE file for details
