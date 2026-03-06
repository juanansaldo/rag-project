import uuid
import streamlit as st
import httpx

API_BASE = "http://127.0.0.1:8000"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

headers = {"X-Session-ID": st.session_state.session_id}

st.set_page_config(page_title="RAG Chat", layout="centered")
st.title("RAG Q&A")
st.caption(f"Session: {st.session_state.session_id[:8]}...")

if st.button("Start new session"):
    try:
        with httpx.Client(timeout=20.0) as client:
            client.delete(f"{API_BASE}/session", headers=headers)
    except Exception:
        pass
    st.session_state.session_id = str(uuid.uuid4())
    st.rerun()

# File upload for ingest
with st.expander("Upload document (PDF, TXT, MD)"):
    file = st.file_uploader("Choose a file", type=["pdf", "txt", "md"])
    if file is not None and st.button("Ingest"):
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                f"{API_BASE}/ingest/file",
                headers=headers,
                files={"file": (file.name, file.getvalue())},
            )
        data = r.json()
        if data.get("ok"):
            st.success(f"Ingested: {data.get('chunks_added', 0)} chunks added.")
        else:
            st.error(data.get("error", "Ingest failed."))

    
# Question and answer
question = st.text_input("Ask a question", placeholder="What is in the documents?")
if question and st.button("Ask"):
    with httpx.Client(timeout=60.0) as client:
        r = client.post(f"{API_BASE}/query", headers=headers, json={"question": question})
    data = r.json()
    if "error" in data:
        st.error(data["error"])
    else:
        st.subheader("Answer")
        st.write(data.get("answer", ""))
        if data.get("sources"):
            st.subheader("Sources")
            for i, src in enumerate(data["sources"], 1):
                with st.expander(f"Source {i}: {src.get('metadata', {}).get('source', '-')}"):
                    st.write(src.get("document", ""))