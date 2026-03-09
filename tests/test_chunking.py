from app.chunking import chunk_text


def test_chunk_text_returns_list_of_dicts():
    text = "Hello world. " * 50
    chunks = chunk_text(text, source="test.txt")
    assert len(chunks) >= 1
    for c in chunks:
        assert "text" in c
        assert "source" in c
        assert "index" in c
        assert c["source"] == "test.txt"

    
def test_chunk_text_empty_returns_empty():
    assert chunk_text("") == []
    assert chunk_text("  ") == []


def test_chunk_text_short_returns_one_chunk():
    chunks = chunk_text("Short text.", source="a.txt")
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Short text."
    assert chunks[0]["index"] == 0


def test_chunk_text_uses_override_params():
    text = "x" * 100
    chunks = chunk_text(text, source="s.txt", chunk_size=20, chunk_overlap=5)

    assert len(chunks) > 1

    for c in chunks:
        assert len(c["text"]) <= 20
        assert c["source"] == "s.txt"