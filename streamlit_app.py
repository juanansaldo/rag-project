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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

headers = {"X-Session-ID": st.session_state.session_id}

st.set_page_config(page_title="RAG Chat", layout="centered")
st.title("RAG Q&A")
st.caption(f"Session: {st.session_state.session_id[:8]}...")

# Advanced options panel
with st.expander("Advanced options"):
    # Chunk size
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

# Session reset
if st.button("Start new session"):
    try:
        with httpx.Client(timeout=20.0) as client:
            client.delete(f"{API_BASE}/session", headers=headers)
    except Exception:
        pass
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.rerun()

headers = {"X-Session-ID": st.session_state.session_id}

# File upload for ingest
with st.expander("Upload document (PDF, TXT, MD)"):
    file = st.file_uploader("Choose a file", type=["pdf", "txt", "md"])
    if file is not None and st.button("Ingest"):
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                f"{API_BASE}/ingest/file",
                headers=headers,
                files={"file": (file.name, file.getvalue())},
                data={
                    "chunk_size": str(int(st.session_state.chunk_size)),
                    "chunk_overlap": str(int(st.session_state.chunk_overlap)),
                },
            )
        data = r.json()
        if data.get("ok"):
            st.success(f"Ingested: {data.get('chunks_added', 0)} chunks added.")
        else:
            st.error(data.get("error", "Ingest failed."))

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