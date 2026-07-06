from embeddings import chunk_transcript, embed_text, embed_texts, find_similar_chunks

def test_chunking():
    transcript = "The earth rotates on its axis. " * 100  # Long text
    chunks = chunk_transcript(transcript, chunk_size=500, overlap=50)

    assert len(chunks) > 1, "Should produce multiple chunks"
    assert all(isinstance(c, str) for c in chunks), "All chunks should be strings"
    print(f"✓ Chunking works: {len(chunks)} chunks created")

def test_embedding():
    text = "The capital of France is Paris"
    embedding = embed_text(text)

    assert len(embedding) == 384, f"Embedding should be 384-dim, got {len(embedding)}"
    assert all(isinstance(x, float) for x in embedding), "Embedding should be floats"
    print(f"✓ Embedding works: {len(embedding)}-dimensional vector")

def test_batch_embedding():
    texts = ["Hello world", "Goodbye world", "The quick brown fox"]
    embeddings = embed_texts(texts)

    assert len(embeddings) == 3, "Should embed all 3 texts"
    assert all(len(e) == 384 for e in embeddings), "All embeddings should be 384-dim"
    print("✓ Batch embedding works")

def test_similarity_search():
    # Create sample chunks with their embeddings
    chunk_texts = [
        "Python is a programming language",
        "Dogs are popular pets",
        "Python is found in jungles"
    ]
    embeddings = embed_texts(chunk_texts)
    chunk_embeddings = list(zip(chunk_texts, embeddings))

    # Query about Python (programming)
    question = "What is Python?"
    question_embedding = embed_text(question)

    similar = find_similar_chunks(question_embedding, chunk_embeddings, top_k=2)

    assert len(similar) <= 2, "Should return at most top-k results"
    assert len(similar) > 0, "Should find at least one similar chunk"
    print(f"✓ Similarity search works: found {len(similar)} similar chunks")
    print(f"  Top result: {similar[0][:50]}...")

if __name__ == "__main__":
    test_chunking()
    test_embedding()
    test_batch_embedding()
    test_similarity_search()
    print("\n All embedding tests passed")
