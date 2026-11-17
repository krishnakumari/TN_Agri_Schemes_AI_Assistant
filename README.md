# 🌾 Tamil Nadu Agriculture Schemes AI Assistant (Bilingual RAG Bot)

An end-to-end **Retrieval-Augmented Generation (RAG)** application built to help Tamil Nadu farmers and agricultural officers query official government agriculture scheme PDFs in **English and Tamil (தமிழ்)**.

The system ingests scheme PDFs into a local **FAISS** vector store, enforces strict topic boundaries using **NVIDIA NeMo Guardrails**, exposes asynchronous REST APIs via **FastAPI**, provides a bilingual **Streamlit** interface, and validates response accuracy using **DeepEval**.

---

## 🏗️ System Architecture

```text
┌─────────────────────┐      HTTP / JSON / PDF       ┌──────────────────────────┐
│   Streamlit UI      │ ───────────────────────────► │     FastAPI Backend      │
│  (English & தமிழ்)   │ ◄─────────────────────────── │   (/upload, /chat, /health)│
└─────────────────────┘                              └────────────┬─────────────┘
                                                                  │
                        ┌─────────────────────────────────────────┼────────────────────────────────┐
                        ▼                                         ▼                                ▼
          ┌──────────────────────────┐             ┌─────────────────────────────┐   ┌──────────────────────────┐
          │   NeMo Guardrails        │             │   Cross-Lingual RAG Engine  │   │   DeepEval Suite         │
          │  (Colang + Self-Check)   │             │  (LangChain + OpenAI + FAISS)│   │  (Faithfulness, Relevancy,│
          │ • Blocks off-topic input │             │ • Translates Tamil → English │   │   Contextual Precision)    │
          │ • Prevents jailbreaks    │             │ • Retrieves top-k PDF chunks │   └──────────────────────────┘
          └──────────────────────────┘             │ • Generates grounded answer  │
                                                   └─────────────────────────────┘