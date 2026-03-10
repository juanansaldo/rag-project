import uuid
import threading
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

if "confirm_new_session" not in st.session_state:
    st.session_state.confirm_new_session = False
if "ingest_thread" not in st.session_state:
    st.session_state.ingest_thread = None
if "ingest_in_progress" not in st.session_state:
    st.session_state.ingest_in_progress = False
if "_ingest_result_holder" not in st.session_state:
    st.session_state._ingest_result_holder = {}

headers = {"X-Session-ID": st.session_state.session_id}


def _run_ingest_in_thread(holder, file_tuples, req_headers, chunk_size, chunk_overlap, chunk_by_words):
    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(
                f"{API_BASE}/ingest/files",
                headers=req_headers,
                files=[("files", (name, content)) for name, content in file_tuples],
                data={
                    "chunk_size": str(chunk_size),
                    "chunk_overlap": str(chunk_overlap),
                    "chunk_by_words": "true" if chunk_by_words else "false",
                },
            )
        data = r.json()
        holder["done"] = True
        holder["data"] = data
    except Exception as e:
        holder["done"] = True
        holder["data"] = {"ok": False, "error": str(e)}


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
if st.session_state.confirm_new_session:
    st.warning("Are you sure? This will clear your documents and chat for this session.")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Yes, start new session", type="primary"):
            try:
                with httpx.Client(timeout=20.0) as client:
                    client.delete(f"{API_BASE}/session", headers=headers)
            except Exception:
                pass
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.chat_history = []
            st.session_state.last_ingested_fingerprint = None
            st.session_state.last_ingested_result = None
            st.session_state.confirm_new_session = False
            st.session_state.ingest_in_progress = False
            st.session_state.ingest_thread = None
            st.session_state._ingest_result_holder.clear()
            st.rerun()
    with col2:
        if st.button("Cancel"):
            st.session_state.confirm_new_session = False
            st.rerun()
else:
    if st.button("Start new session"):
        st.session_state.confirm_new_session = True
        st.rerun()

headers = {"X-Session-ID": st.session_state.session_id}

# File upload for ingest
with st.expander("Upload document (PDF, TXT, MD, HTML, CSV, DOCX)"):
    files = st.file_uploader(
        "Choose one or more files", 
        type=["pdf", "txt", "md", "html", "csv", "docx"], 
        accept_multiple_files=True,
    )
    # Sync completed background ingest from holder into session state
    holder = st.session_state._ingest_result_holder
    if holder.get("done"):
        st.session_state.ingest_in_progress = False
        st.session_state.ingest_thread = None
        data = holder.get("data", {})
        fp = holder.get("fingerprint")
        if fp is not None:
            st.session_state.last_ingested_fingerprint = fp
        if data.get("ok"):
            total = data.get("total_chunks", 0)
            n_files = len(data.get("files", []))
            summary = f"Ingested {total} chunks from {n_files} file(s)."
            file_details = [
                {"name": item.get("filename", "?"), "n": item.get("chunks_added", 0), "error": item.get("error")}
                for item in data.get("files", [])
            ]
            st.session_state.last_ingested_result = {"summary": summary, "file_details": file_details}
        else:
            st.session_state.last_ingested_result = None
        holder.clear()

    if files:
        fingerprint = tuple((f.name, len(f.getvalue())) for f in sorted(files, key=lambda x: x.name))
        if fingerprint != st.session_state.last_ingested_fingerprint:
            if not st.session_state.ingest_in_progress:
                # Start background ingest
                file_tuples = [(f.name, f.getvalue()) for f in files]
                req_headers = {"X-Session-ID": st.session_state.session_id}
                st.session_state._ingest_result_holder["fingerprint"] = fingerprint
                thread = threading.Thread(
                    target=_run_ingest_in_thread,
                    args=(
                        st.session_state._ingest_result_holder,
                        file_tuples,
                        req_headers,
                        int(st.session_state.chunk_size),
                        int(st.session_state.chunk_overlap),
                        st.session_state.chunk_by_words,
                    ),
                )
                thread.daemon = True
                thread.start()
                st.session_state.ingest_thread = thread
                st.session_state.ingest_in_progress = True
                st.rerun()

        if st.session_state.ingest_in_progress:
            st.info("Ingesting in background... You can ask a question below; it will run after ingest completes.")
        elif st.session_state.last_ingested_result:
            res = st.session_state.last_ingested_result
            st.success(res["summary"])
            for fd in res["file_details"]:
                if fd.get("error"):
                    st.caption(f"{fd['name']}: error - {fd['error']}")
                else:
                    st.caption(f"{fd['name']}: {fd['n']} chunks")
        else:
            st.info("Documents already ingested. Ask a question below or change the file selection to re-ingest")


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
    # Wait for background ingest to finish if still running
    if st.session_state.ingest_in_progress and st.session_state.ingest_thread is not None:
        if st.session_state.ingest_thread.is_alive():
            with st.spinner("Waiting for ingest to complete..."):
                st.session_state.ingest_thread.join(timeout=120.0)
        # Sync holder into session state so last_ingested_fingerprint is up to date
        holder = st.session_state._ingest_result_holder
        if holder.get("done"):
            st.session_state.ingest_in_progress = False
            st.session_state.ingest_thread = None
            data = holder.get("data", {})
            fp = holder.get("fingerprint")
            if fp is not None:
                st.session_state.last_ingested_fingerprint = fp
            if data.get("ok"):
                total = data.get("total_chunks", 0)
                n_files = len(data.get("files", []))
                summary = f"Ingested {total} chunks from {n_files} file(s)."
                file_details = [
                    {"name": item.get("filename", "?"), "n": item.get("chunks_added", 0), "error": item.get("error")}
                    for item in data.get("files", [])
                ]
                st.session_state.last_ingested_result = {"summary": summary, "file_details": file_details}
            else:
                st.session_state.last_ingested_result = None
            holder.clear()

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