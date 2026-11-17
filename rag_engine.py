import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load OPENAI_API_KEY from .env
load_dotenv()

FAISS_INDEX_PATH = "faiss_index"

# Initialize OpenAI Embedding model and LLM
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def ingest_pdf(pdf_path: str) -> int:
    """
    Loads a PDF, splits it into chunks, creates embeddings,
    and saves/updates the local FAISS vector store.
    Returns the number of chunks added.
    """
    # 1. Load PDF pages
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # 2. Split text into manageable chunks with overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)

    if not chunks:
        raise ValueError("No readable text found in the uploaded PDF.")

    # 3. Create or update FAISS index
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    if os.path.exists(index_file):
        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        vectorstore.add_documents(chunks)
    else:
        vectorstore = FAISS.from_documents(chunks, embeddings)

    # 4. Persist to disk
    vectorstore.save_local(FAISS_INDEX_PATH)
    return len(chunks)


def translate_query_to_english(question: str) -> str:
    """
    Translates Tamil or Tanglish agricultural queries into clear English
    so FAISS vector search matches English PDF chunks accurately.
    If the query is already in English, returns it unchanged.
    """
    translation_prompt = ChatPromptTemplate.from_template(
        """Translate the following user question about Tamil Nadu agriculture schemes into clear, accurate English for document search.
- If the question is already in English, return it as-is without changing its meaning.
- Preserve crop names, scheme names, and agricultural terms accurately (e.g., 'மானியம்' -> 'subsidy', 'விதைப் பண்ணை' -> 'seed farm', 'பயறு வகைகள்' -> 'pulses').
- Output ONLY the English search query, nothing else.

User Question: {question}
English Query:"""
    )
    chain = translation_prompt | llm | StrOutputParser()
    return chain.invoke({"question": question}).strip()


def ask_rag(question: str, language: str = "Auto") -> dict:
    """
    Retrieves relevant English scheme chunks from FAISS using a translated search query,
    and generates a grounded answer in the requested language (Tamil, English, or Auto-detect).
    """
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    if not os.path.exists(index_file):
        return {
            "answer": "திட்ட ஆவணங்கள் இன்னும் பதிவேற்றப்படவில்லை. முதலில் PDF ஆவணத்தைப் பதிவேற்றவும். (No scheme documents uploaded yet.)",
            "contexts": []
        }

    # 1. Translate Tamil/Tanglish query to English for high-precision FAISS retrieval
    english_search_query = translate_query_to_english(question)

    # 2. Load FAISS vector store and retrieve top 4 chunks
    vectorstore = FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    retrieved_docs = retriever.invoke(english_search_query)
    contexts = [doc.page_content for doc in retrieved_docs]

    formatted_context = "\n\n---\n\n".join(
        [
            f"[Source: {os.path.basename(doc.metadata.get('source', 'Unknown'))}, Page {doc.metadata.get('page', 0) + 1}]\n{doc.page_content}"
            for doc in retrieved_docs
        ]
    )

    # 3. Determine output language instruction
    if language == "Tamil":
        lang_instruction = "Respond completely in clear, natural, respectful Tamil (தமிழ்) suitable for Tamil Nadu farmers. Keep official scheme acronyms (like SC/ST, PMFBY, PM-KUSUM) clear."
    elif language == "English":
        lang_instruction = "Respond in clear English."
    else:
        lang_instruction = "Detect the language of the User Question. If the user asked in Tamil (or Tanglish), respond completely in clear, respectful Tamil (தமிழ்). If the user asked in English, respond in English."

    # 4. Build strict cross-lingual RAG prompt
    prompt = ChatPromptTemplate.from_template(
        """You are an official assistant for Tamil Nadu Government Agriculture Schemes.
Answer the user's question strictly using ONLY the provided English context below.

Rules:
- {lang_instruction}
- Do NOT merge or combine separate percentages, quotas, or conditions from different sentences unless the text explicitly states they apply to the same item.
- Quote exact subsidy percentages, amounts, and conditions (such as "subject to availability of funds" / "நிதி இருப்பைப் பொறுத்து") accurately.
- If the answer is not found in the context, state clearly in the response language that this information is not available in the uploaded scheme documents.

Context (English):
{context}

User Question: {question}

Answer:"""
    )

    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({
        "lang_instruction": lang_instruction,
        "context": formatted_context,
        "question": question
    })

    return {
        "answer": answer,
        "contexts": contexts
    }