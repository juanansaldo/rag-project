from pathlib import Path

from app.loaders import load_text_file, load_document, load_directory


def test_load_text_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("Hello from test file.")
    result = load_text_file(f)
    assert len(result) == 1
    assert result[0]["text"] == "Hello from test file."
    assert result[0]["source"] == "sample.txt"
    assert result[0]["page"] == 0


def test_load_text_file_missing_returns_empty():
    assert load_text_file(Path("/nonexistent/path.txt")) == []


def test_load_document_txt(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("Content here.")
    result = load_document(f)
    assert len(result) == 1
    assert "Content here." in result[0]["text"]
    assert result[0]["source"] == "doc.txt"


def test_load_document_md(tmp_path):
    f = tmp_path / "readme.md"
    f.write_text("# Title\n\nSome markdown.")
    result = load_document(f)
    assert len(result) == 1
    assert "Title" in result[0]["text"]


def test_load_directory(tmp_path):
    (tmp_path / "a.txt").write_text("File A")
    (tmp_path / "b.txt").write_text("File B")
    result = load_directory(tmp_path)
    assert len(result) == 2
    texts = [r["text"] for r in result]
    assert "File A" in texts
    assert "File B" in texts


def test_load_directory_nonexistent_returns():
    assert load_directory(Path("/nonexistent/dir")) == []