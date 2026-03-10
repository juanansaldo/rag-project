from html.parser import HTMLParser
from pathlib import Path
import csv
import re


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


def _strip_html_tags(html: str) -> str:
    """Extract text from HTML, strip tags."""
    class _HTMLTextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = []

        def handle_data(self, data: str) -> None:
            self.text.append(data)

        def get_text(self) -> str:
            return " ".join(self.text)

    parser = _HTMLTextExtractor()
    try:
        parser.feed(html)
        return re.sub(r"\s+", " ", parser.get_text()).strip()
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)

    
def load_html(path: str | Path) -> list[dict]:
    """Load HTML file; extract text and return one {text, source, page}."""
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = _strip_html_tags(raw)
    if not text:
        return []
    return [{"text": text, "source": path.name, "page": 0}]


def load_csv(path: str | Path) -> list[dict]:
    """Load CSV; flatten rows to one text block. Returns one {text, source, page}."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
    except Exception:
        return []
    if not rows:
        return []
    lines = [", ".join(str(c) for c in row) for row in rows]
    text = "\n".join(lines)
    return [{"text": text, "source": path.name, "page": 0}]


def load_docx(path: str | Path) -> list[dict]:
    """Load DOCX; concatenate paragraph text. Returns one {text, source, page}."""
    try:
        from docx import Document
    except ImportError:
        return []
    path = Path(path)
    if not path.exists():
        return []
    try:
        doc = Document(path)
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(parts)
        if not text:
            return []
        return [{"text": text, "source": path.name, "page": 0}]
    except Exception:
        return []


def load_document(path: str | Path) -> list[dict]:
    """Dispatch by extension: .pdf, .html, .csv, .docx have dedicated loaders; else -> load_text_file."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix == ".html":
        return load_html(path)
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".docx":
        return load_docx(path)
    return load_text_file(path)


def load_directory(dir_path: str | Path) -> list[dict]:
    """Load all .txt, .md, .pdf, .html, .csv, .docx files from a directory. Returns flat list of {text, source, page}."""
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        return []
    out = []
    for ext in ("*.txt", "*.md", "*.pdf", "*.html", "*.csv", "*.docx"):
        for f in dir_path.glob(ext):
            out.extend(load_document(f))
    return out