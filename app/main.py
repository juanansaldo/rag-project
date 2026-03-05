from fastapi import FastAPI

app = FastAPI(title="RAG API")

@app.get("/health")
def health():
    return {"status": "ok"}