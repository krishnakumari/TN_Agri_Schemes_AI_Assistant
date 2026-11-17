import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from nemoguardrails import RailsConfig, LLMRails

from rag_engine import ingest_pdf, FAISS_INDEX_PATH

app = FastAPI(
    title="Tamil Nadu Agriculture Schemes Bilingual RAG API",
    description="English & Tamil RAG API powered by LangChain, FAISS, OpenAI, and NeMo Guardrails",
    version="2.0.0"
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
async def upload_pdf(file: UploadFile = File(...)):
    """
    Receives a Tamil Nadu agriculture scheme PDF from the UI,
    saves it locally, and adds its embeddings to FAISS.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(DATA_DIR, safe_filename)

    try:
        # Stream uploaded file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process PDF and update FAISS vector store
        chunks_added = ingest_pdf(file_path)

        return {
            "filename": safe_filename,
            "chunks_added": chunks_added,
            "message": f"Successfully indexed '{safe_filename}' ({chunks_added} chunks added to FAISS)."
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        await file.close()


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