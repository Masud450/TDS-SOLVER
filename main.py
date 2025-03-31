from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import zipfile
from io import BytesIO
import openai  # Remove if not using OpenAI
import logging

app = FastAPI(
    title="TDS Solver API",
    description="Automated solution generator for IIT Madras Data Science assignments",
    version="1.0"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Core Functions ---
def process_csv(file: BytesIO):
    """Process CSV files and extract answers"""
    try:
        df = pd.read_csv(file)
        if 'answer' in df.columns:
            return str(df['answer'].iloc[0])
        return "No 'answer' column found"
    except Exception as e:
        logger.error(f"CSV processing error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {str(e)}")

def process_zip(file: BytesIO):
    """Extract and process ZIP files"""
    try:
        with zipfile.ZipFile(file) as z:
            for filename in z.namelist():
                if filename.endswith('.csv'):
                    with z.open(filename) as f:
                        return process_csv(BytesIO(f.read()))
        return "No CSV found in ZIP"
    except Exception as e:
        logger.error(f"ZIP processing error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid ZIP: {str(e)}")

# --- API Endpoints ---
@app.post("/api/")
async def solve_assignment(
    question: str = Form(..., description="Assignment question text"),
    file: UploadFile = File(None, description="Optional CSV/ZIP file")
):
    """
    Processes assignment questions with optional file attachments.
    Returns answer in format: {"answer": "solution"}
    """
    try:
        # File processing logic
        file_content = None
        if file:
            content = await file.read()
            if file.filename.endswith('.csv'):
                file_content = process_csv(BytesIO(content))
            elif file.filename.endswith('.zip'):
                file_content = process_zip(BytesIO(content))
        
        # Question processing logic (add your custom logic here)
        if "capital of india" in question.lower():
            answer = "New Delhi"
        elif file_content:
            answer = f"File content: {file_content}"
        else:
            answer = "42"  # Default response
            
        return {"answer": str(answer)}
        
    except Exception as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Health Check ---
@app.get("/")
def health_check():
    return {"status": "active", "docs": "/docs"}

# --- Error Handling ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )