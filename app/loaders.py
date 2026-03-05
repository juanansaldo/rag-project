from pathlib import Path


def load_text_file(path: str | Path) -> list[dict]:
    """Load a plain text or markdown file. Returns the list of {text, source, page} (page=0)."""
    path = Path(path)
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [{"text": text, "source": path.name, "page": 0}]


def load_pdf(path: str | Path) -> list[dict]:
    """Load a PDF; each page becomes one item: {text, source, page}."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return []
    path = Path(path)
    if not path.exists():
        return []
    reader = PdfReader(path)
    out = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            out.append({"text": text, "source": path.name, "page": i})
    return out


def load_document(path: str | Path) -> list[dict]:
    """Dispatch by extension: .pdf -> load_pdf, else load_text_file."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    return load_text_file(path)


def load_directory(dir_path: str | Path) -> list[dict]:
    """Load all .txt, .md, .pdf files from a directory. Returns flat list of {text, source, page}."""
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        return []
    out = []
    for ext in ("*.txt", "*.md", "*.pdf"):
        for f in dir_path.glob(ext):
            out.extend(load_document(f))
    return out