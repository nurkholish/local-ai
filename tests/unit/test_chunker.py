from local_ai.application.rag.chunker import chunk_text


def test_chunk_splits():
    text = "Sentence one. Sentence two. " * 20
    chunks = chunk_text(text, chunk_size=100, overlap=0)
    assert len(chunks) > 1