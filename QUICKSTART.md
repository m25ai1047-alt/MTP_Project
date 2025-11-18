# Quick Start Guide

Get up and running with the RCA system in 5 minutes.

## 1. Install Dependencies

```bash
# Install all dependencies at once
pip install -r anomaly_detector/requirements.txt
pip install -r code_indexer/requirements.txt
pip install -r rca_agent/requirements.txt
```

Or install individually:
```bash
pip install scikit-learn pandas joblib watchdog tree-sitter-languages \
    chromadb sentence-transformers rank-bm25 requests fastapi uvicorn \
    pydantic numpy
```

## 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env and add your OpenAI API key
# Or export directly:
export LLM_API_KEY="sk-your-openai-key-here"
```

## 3. Train Anomaly Detection Model

```bash
cd anomaly_detector
python train_model.py ../sample_data/normal_logs.csv
cd ..
```

This creates `isolation_forest.joblib` and `tfidf_vectorizer.joblib`.

## 4. Index Your Codebase (Optional)

If you have a Java project to index:

```bash
cd code_indexer
# Edit config.py and set PROJECT_PATH to your Java project
python bulk_indexer.py
cd ..
```

Skip this step if you just want to test the system.

## 5. Test the System

### Test with sample logs:
```bash
python pipeline.py sample_data/test_logs.txt
```

### Test with a single error:
```bash
python pipeline.py "ERROR: NullPointerException at UserService.getUser(UserService.java:42)"
```

### Test RCA only:
```bash
cd rca_agent
python cli.py "ERROR: Database connection timeout at DatabaseService.connect()"
```

## 6. Start the API Server (Optional)

```bash
cd rca_agent
python main_rca_agent.py
```

Then test with:
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "error_log": "ERROR: Connection refused at port 5432"
  }'
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Index your actual codebase for better RCA results
- Train the anomaly detector with your real logs
- Customize prompts in `rca_agent/rca_service.py`
- Adjust hybrid search weights in `.env`

## Troubleshooting

**No analysis returned:**
- Check that LLM_API_KEY is set correctly
- Verify API key has credits
- Check internet connection

**No code context found:**
- Run the code indexer first: `python code_indexer/bulk_indexer.py`
- Verify PROJECT_PATH points to a Java project
- Check ChromaDB was created at `code_indexer/chroma_db_storage/`

**Model not found:**
- Train the model: `python anomaly_detector/train_model.py sample_data/normal_logs.csv`
- Check that .joblib files exist in anomaly_detector/

## Example Output

```
Analyzing error log...
--------------------------------------------------------------------------------

=== ROOT CAUSE ANALYSIS ===

Error: ERROR: NullPointerException at UserService.getUser(UserService.java:42)

Analysis:
1. Root Cause: The error indicates a NullPointerException in the getUserProfile
   method, likely due to an unvalidated null user object.

2. Location: UserService.java, line 42 in the getUser method

3. Fix: Add null checking before accessing user properties:
   if (user == null) {
       throw new UserNotFoundException("User not found");
   }

4. Prevention: Implement input validation and use Optional<User> return types

Found 2 relevant code snippets
1. /project/UserService.java - getUser
2. /project/UserService.java - getUserProfile

Keywords: NullPointerException, UserService
```
