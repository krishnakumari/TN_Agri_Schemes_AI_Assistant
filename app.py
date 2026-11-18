import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="TN Agriculture Schemes AI Assistant | தமிழ்நாடு வேளாண்மைத் திட்டங்கள்",
    page_icon="🌾",
    layout="wide"
)

st.title("🌾 Tamil Nadu Agriculture Schemes AI Assistant")
st.caption("தமிழ்நாடு அரசின் வேளாண்மைத் திட்டங்களுக்கான AI உதவியாளர் • English & தமிழ் Support")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "வணக்கம்! (Vanakkam!) Ask me anything about the uploaded Tamil Nadu Government Agriculture Schemes "
                "in **Tamil (தமிழ்)** or **English**.\n\n"
                "மானியங்கள், தகுதி வரம்புகள், பயிர் காப்பீடு மற்றும் சூரிய சக்தி பம்ப் திட்டங்கள் குறித்து கேளுங்கள்."
            )
        }
    ]

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# --- SIDEBAR: Language, Status & Multi-PDF Upload ---
with st.sidebar:
    st.header("🌐 Response Language / மொழி")
    selected_lang = st.selectbox(
        "Choose answer language:",
        options=["Auto", "Tamil", "English"],
        format_func=lambda x: {
            "Auto": "Auto-Detect (கேள்வியின் மொழியில்)",
            "Tamil": "தமிழ் (Tamil)",
            "English": "English"
        }[x]
    )

    st.divider()
    st.header("📄 Scheme Knowledge Base")

    # Check FastAPI backend health
    try:
        health_res = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if health_res.status_code == 200:
            health_data = health_res.json()
            st.success("Backend API: Connected")
            if health_data.get("faiss_index_ready"):
                st.info("FAISS Vector Store: Ready")
                pdfs = health_data.get("uploaded_pdfs", [])
                if pdfs:
                    with st.expander(f"Indexed PDFs ({len(pdfs)})", expanded=False):
                        for pdf in pdfs:
                            st.write(f"• `{pdf}`")
            else:
                st.warning("FAISS Vector Store: Empty (Upload PDFs)")
        else:
            st.error("Backend API: Error")
    except requests.exceptions.ConnectionError:
        st.error("Backend API: Offline (Start FastAPI on port 8000)")

    st.divider()

    # Multi-PDF Uploader
    uploaded_files = st.file_uploader(
        "Upload TN Agriculture Scheme PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select one or multiple official Tamil Nadu agriculture scheme PDFs to index into FAISS."
    )

    if uploaded_files:
        st.caption(f"{len(uploaded_files)} file(s) selected")
        if st.button("📥 Process & Index All PDFs", width="stretch"):
            with st.spinner(f"Chunking & embedding {len(uploaded_files)} PDF(s) into FAISS..."):
                try:
                    # Build multipart list of ("files", (filename, bytes, mime)) tuples
                    files_payload = [
                        ("files", (f.name, f.getvalue(), "application/pdf"))
                        for f in uploaded_files
                    ]
                    response = requests.post(
                        f"{API_BASE_URL}/upload",
                        files=files_payload,
                        timeout=300
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.success(data["message"])

                        # Show per-file chunk breakdown
                        for item in data.get("processed_files", []):
                            st.write(f"✅ `{item['filename']}` — {item['chunks_added']} chunks")

                        # Show any files that failed (e.g., scanned image-only PDFs)
                        for err in data.get("failed_files", []):
                            st.warning(f"⚠️ `{err['filename']}`: {err['error']}")
                    else:
                        error_detail = response.json().get("detail", "Upload failed.")
                        st.error(f"Error: {error_detail}")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")

    st.divider()
    if st.button("🗑️ Clear Chat History", width="stretch"):
        st.session_state.messages = []
        st.rerun()

# --- QUICK SAMPLE QUESTIONS (English & Tamil) ---
st.markdown("**💡 Try Sample Questions / மாதிரி கேள்விகள்:**")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("பயறு விதைப் பண்ணை மானியம் எவ்வளவு?", width="stretch"):
        st.session_state.pending_prompt = "பயறு வகை விதைப் பண்ணை அமைக்க மானியம் எவ்வளவு சதவீதம்?"

with col2:
    if st.button("யார் இந்த மானியத்திற்கு தகுதியானவர்கள்?", width="stretch"):
        st.session_state.pending_prompt = "பயறு வகை பயிர்களில் விதைப் பண்ணை அமைக்க மானியம் பெற யார் தகுதியானவர்கள்?"

with col3:
    if st.button("Pulses seed farm subsidy (English)", width="stretch"):
        st.session_state.pending_prompt = "What is the subsidy percentage and eligibility for pulses seed farms?"

st.divider()

# --- MAIN AREA: Render Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle either typed chat input or clicked sample question button
chat_input_prompt = st.chat_input("கேள்வியை தமிழிலோ அல்லது ஆங்கிலத்திலோ கேளுங்கள்... (Ask in Tamil or English)")
user_prompt = chat_input_prompt or st.session_state.pending_prompt

if user_prompt:
    st.session_state.pending_prompt = None

    # 1. Display user message immediately
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # 2. Query FastAPI /chat endpoint
    with st.chat_message("assistant"):
        with st.spinner("திட்ட ஆவணங்களைத் தேடுகிறது... (Searching schemes & checking guardrails...)"):
            try:
                res = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={
                        "question": user_prompt,
                        "language": selected_lang
                    },
                    timeout=60
                )
                if res.status_code == 200:
                    bot_reply = res.json()["answer"]
                else:
                    bot_reply = f"⚠️ API Error ({res.status_code}): {res.json().get('detail', 'Unknown error')}"
            except requests.exceptions.ConnectionError:
                bot_reply = "⚠️ Cannot reach FastAPI backend. Please make sure `uvicorn main:app --port 8000` is running."
            except Exception as e:
                bot_reply = f"⚠️ Unexpected error: {str(e)}"

            st.markdown(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})