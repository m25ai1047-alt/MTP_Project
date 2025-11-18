from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from rca_service import perform_root_cause_analysis

app = FastAPI(
    title="RCA Analysis Service",
    description="Root cause analysis for production errors using RAG",
    version="1.0.0"
)

class RCARequest(BaseModel):
    error_log: str = Field(..., min_length=10, description="Error log or stack trace to analyze")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation tracking")

class RCAResponse(BaseModel):
    error_log: str
    analysis: str
    relevant_code: list
    keywords_extracted: list

@app.post("/analyze", response_model=RCAResponse)
async def analyze_error(request: RCARequest):
    """Analyze error log and return root cause analysis with relevant code."""
    try:
        result = perform_root_cause_analysis(request.error_log)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rca-analysis"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
