import uuid
import streamlit as st
import httpx
import os

API_BASE = "http://127.0.0.1:8000"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


# Advanced options defaults
if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = int(os.getenv("CHUNK_SIZE", "512"))
if "chunk_overlap" not in st.session_state:
    st.session_state.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "100"))
if "top_k" not in st.session_state:
    st.session_state.top_k = int(os.getenv("TOP_K", "4"))
if "llm_model" not in st.session_state:
    default = os.getenv("LLM_MODEL", "mistral")
    st.session_state.llm_model = default if default in ["mistral", "llama3.2", "llama3.1", "phi3", "gemma2"] else "mistral"

# Chunking mode
if "chunk_mode" not in st.session_state:
    st.session_state.chunk_mode = "Words" if st.session_state.get("chunk_by_words") else "Characters"
if "chunk_by_words" not in st.session_state:
    st.session_state.chunk_by_words = (st.session_state.chunk_mode == "Words")
if "_last_chunk_by_words" not in st.session_state:
    st.session_state._last_chunk_by_words = st.session_state.chunk_by_words

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_ingested_fingerprint" not in st.session_state:
    st.session_state.last_ingested_fingerprint = None
if "last_ingested_result" not in st.session_state:
    st.session_state.last_ingested_result = None

headers = {"X-Session-ID": st.session_state.session_id}

st.set_page_config(page_title="RAG Chat", layout="centered")
st.title("RAG Q&A")
st.caption(f"Session: {st.session_state.session_id[:8]}...")

# Advanced options panel
with st.expander("Advanced options"):
    # Chunking mode toggle
    selected_mode = st.radio(
        "Chunk by",
        ["Characters", "Words"],
        key="chunk_mode",
        horizontal=True,
    )
    st.session_state.chunk_by_words = (selected_mode == "Words")

    # If mode changed, reset defaults for that mode
    if st.session_state._last_chunk_by_words != st.session_state.chunk_by_words:
        st.session_state._last_chunk_by_words = st.session_state.chunk_by_words
        if st.session_state.chunk_by_words:
            # Word-based defaults
            word_size_default = int(os.getenv("CHUNK_SIZE_WORDS", "100"))
            word_overlap_default = int(os.getenv("CHUNK_OVERLAP_WORDS", "20"))
            st.session_state.chunk_size = word_size_default
            st.session_state.chunk_overlap = word_overlap_default
        else:
            # Character-based defaults
            char_size_default = int(os.getenv("CHUNK_SIZE", "512"))
            char_overlap_default = int(os.getenv("CHUNK_OVERLAP", "100"))
            st.session_state.chunk_size = char_size_default
            st.session_state.chunk_overlap = char_overlap_default

    # Chunk size / overlap widgets, depending on mode
    if st.session_state.chunk_by_words:
        # Word-based chunking
        st.number_input(
            "Chunk size (words)",
            min_value=10,
            max_value=500,
            step=1,
            key="chunk_size",
        )

        max_overlap = max(0, int(st.session_state.chunk_size) - 1)
        if int(st.session_state.chunk_overlap) > max_overlap:
            st.session_state.chunk_overlap = max_overlap

        st.number_input(
            "Chunk overlap (words)",
            min_value=0,
            max_value=max_overlap,
            step=1,
            key="chunk_overlap",
        )
    else:
        # Character-based chunking
        st.number_input(
            "Chunk size (characters)",
            min_value=64,
            max_value=4096,
            step=1,
            key="chunk_size",
        )

        # Chunk overlap
        max_overlap = max(0, int(st.session_state.chunk_size) - 1)
        if int(st.session_state.chunk_overlap) > max_overlap:
            st.session_state.chunk_overlap = max_overlap

        st.number_input(
            "Chunk overlap (characters)",
            min_value=0,
            max_value=max_overlap,
            step=1,
            key="chunk_overlap",
        )

    # Top K
    st.number_input(
        "Top K (results per query)",
        min_value=1,
        max_value=20,
        step=1,
        key="top_k",
    )

    # LLM model (Ollama)
    st.selectbox(
        "LLM model",
        options=["mistral", "llama3.2", "llama3.1", "phi3", "gemma2"],
        key="llm_model",
    )

# Session reset
if st.button("Start new session"):
    try:
        with httpx.Client(timeout=20.0) as client:
            client.delete(f"{API_BASE}/session", headers=headers)
    except Exception:
        pass
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.session_state.last_ingested_fingerprint = None
    st.session_state.last_ingested_result = None
    st.rerun()

headers = {"X-Session-ID": st.session_state.session_id}

# File upload for ingest
with st.expander("Upload document (PDF, TXT, MD, HTML, CSV, DOCX)"):
    files = st.file_uploader(
        "Choose one or more files", 
        type=["pdf", "txt", "md", "html", "csv", "docx"], 
        accept_multiple_files=True,
    )
    if files:
        fingerprint = tuple((f.name, len(f.getvalue())) for f in sorted(files, key=lambda x: x.name))
        if fingerprint != st.session_state.last_ingested_fingerprint:
            with st.spinner("Ingesting..."):
                with httpx.Client(timeout=120.0) as client:
                    r = client.post(
                        f"{API_BASE}/ingest/files",
                        headers=headers,
                        files=[("files", (f.name, f.getvalue())) for f in files],
                        data={
                            "chunk_size": str(int(st.session_state.chunk_size)),
                            "chunk_overlap": str(int(st.session_state.chunk_overlap)),
                            "chunk_by_words": "true" if st.session_state.chunk_by_words else "false",
                        }
                    )
            data = r.json()
            if data.get("ok"):
                st.session_state.last_ingested_fingerprint = fingerprint
                total = data.get("total_chunks", 0)
                n_files = len(data.get("files", []))
                summary = f"Ingested {total} chunks from {n_files} file(s)."
                file_details = [
                    {"name": item.get("filename", "?"), "n": item.get("chunks_added", 0), "error": item.get("error")}
                    for item in data.get("files", [])
                ]
                st.session_state.last_ingested_result = {"summary": summary, "file_details": file_details}
                st.success(summary)
                for fd in file_details:
                    if fd["error"]:
                        st.caption(f"{fd['name']}: error - {fd['error']}")
                    else:
                        st.caption(f"{fd['name']}: {fd['n']} chunks")
            else:
                st.session_state.last_ingested_result = None
                st.error(data.get("error", "Ingest failed."))
        else:
            # Show stored last result
            if st.session_state.last_ingested_result:
                res = st.session_state.last_ingested_result
                st.success(res["summary"])
                for fd in res["file_details"]:
                    if fd["error"]:
                        st.caption(f"{fd['name']}: error - {fd['error']}")
                    else:
                        st.caption(f"{fd['name']}: {fd['n']} chunks")
            else:
                st.info("Documents already ingested. Ask a question below or change the file selection to re-ingest.")


# Chat history
if st.session_state.chat_history:
    st.subheader("Previous Q&A")
    for i, turn in enumerate(st.session_state.chat_history):
        with st.container():
            st.markdown(f"**Q:** {turn['question']}")
            st.write(turn["answer"])
            if turn.get("sources"):
                with st.expander("Sources", key=f"hist_sources_{i}"):
                    for j, src in enumerate(turn["sources"], 1):
                        st.caption(f"Source {j}: {src.get('metadata', {}).get('source', '-')}")
                        st.write(src.get("document", ""))
            st.divider()

# Question and answer
question = st.text_input("Ask a question", placeholder="What is in the documents?")
if question and st.button("Ask"):
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            f"{API_BASE}/query", 
            headers=headers, 
            json={
                "question": question,
                "top_k": int(st.session_state.top_k),
                "model": st.session_state.llm_model,
            },
        )
    data = r.json()
    if "error" in data:
        st.error(data["error"])
    else:
        turn = {
            "question": question,
            "answer": data.get("answer", ""),
            "sources": data.get("sources", []),
        }
        st.session_state.chat_history.append(turn)
        st.rerun()