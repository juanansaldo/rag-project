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


def test_chunk_text_by_words_uses_word_counts_and_indices():
    text = "one two three four five six seven eight nine ten"
    chunks = chunk_text(
        text,
        source="words.txt",
        chunk_size=3,
        chunk_overlap=1,
        by_words=True,
    )

    # We should get multiple chunks, all with the expected keys and source
    assert len(chunks) >= 2
    for i, c in enumerate(chunks):
        assert set(c.keys()) == {"text", "source", "index"}
        assert c["source"] == "words.txt"
        assert c["index"] == i # indices are sequential
        # Each chunk has at most 3 words
        words = c["text"].split()
        assert 1 < len(words) <= 3


def test_chunk_text_by_words_respects_overlap():
    text = "one two three four five six seven eight nine ten"
    size = 3
    overlap = 1
    chunks = chunk_text(
        text,
        source="overlap.txt",
        chunk_size=size,
        chunk_overlap=overlap,
        by_words=True,
    )

    # There should be at least two chunks to test overlap.
    assert len(chunks) >= 2

    for prev, curr in zip(chunks, chunks[1:]):
        prev_words = prev["text"].split()
        curr_words = curr["text"].split()
        # Last 'overlap' words of previous chunk should equal first 'overlap' of current
        assert prev_words[-overlap:] == curr_words[:overlap]