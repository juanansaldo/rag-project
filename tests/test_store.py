from app.store import add, search


def test_store_add_and_search():
    add("t1", "The capital of France is Paris")
    add("t2", "Python is a programming language")
    hits = search("What is the capital of France?", top_k=2)
    assert len(hits) >= 1
    assert "Paris" in hits[0]["document"]
    print("OK")