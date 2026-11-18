import os
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from nemoguardrails import RailsConfig, LLMRails

from rag_engine import ingest_pdf, FAISS_INDEX_PATH

app = FastAPI(
    title="Tamil Nadu Agriculture Schemes Bilingual RAG API",
    description="English & Tamil RAG API powered by LangChain, FAISS, OpenAI, and NeMo Guardrails",
    version="2.1.0"
)

# Initialize NeMo Guardrails once at server startup
rails_config = RailsConfig.from_path("guardrails")
rails = LLMRails(rails_config)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


class ChatRequest(BaseModel):
    question: str
    language: str = Field(
        default="Auto",
        description="Response language preference: 'Auto', 'Tamil', or 'English'"
    )


class ChatResponse(BaseModel):
    answer: str
    language_used: str


@app.get("/health")
def health_check():
    """
    Returns backend status and whether the FAISS vector index is populated.
    """
    index_exists = os.path.exists(os.path.join(FAISS_INDEX_PATH, "index.faiss"))
    indexed_files = [
        f for f in os.listdir(DATA_DIR) if f.lower().endswith(".pdf")
    ]
    return {
        "status": "healthy",
        "faiss_index_ready": index_exists,
        "uploaded_pdfs": indexed_files
    }


@app.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Receives one or multiple Tamil Nadu agriculture scheme PDFs from the UI,
    saves each locally, and merges all embeddings into the FAISS vector store.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    processed_files = []
    failed_files = []
    total_chunks_added = 0

    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            failed_files.append({
                "filename": file.filename or "Unknown",
                "error": "Only PDF files are supported."
            })
            await file.close()
            continue

        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(DATA_DIR, safe_filename)

        try:
            # Save uploaded file to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Process PDF and merge into FAISS vector store
            chunks_added = ingest_pdf(file_path)
            total_chunks_added += chunks_added
            processed_files.append({
                "filename": safe_filename,
                "chunks_added": chunks_added
            })
        except Exception as e:
            failed_files.append({
                "filename": safe_filename,
                "error": str(e)
            })
        finally:
            await file.close()

    if not processed_files and failed_files:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process uploaded files: {failed_files}"
        )

    return {
        "total_files_indexed": len(processed_files),
        "total_chunks_added": total_chunks_added,
        "processed_files": processed_files,
        "failed_files": failed_files,
        "message": f"Successfully indexed {len(processed_files)} PDF(s) ({total_chunks_added} total chunks added to FAISS)."
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """
    Passes the user's English or Tamil question and language preference
    through NeMo Guardrails -> Cross-Lingual FAISS RAG Engine.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    allowed_languages = {"Auto", "Tamil", "English"}
    selected_lang = request.language if request.language in allowed_languages else "Auto"

    try:
        response = await rails.generate_async(
            messages=[
                {
                    "role": "context",
                    "content": {"language": selected_lang}
                },
                {
                    "role": "user",
                    "content": request.question
                }
            ]
        )
        return ChatResponse(
            answer=response["content"],
            language_used=selected_lang
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")