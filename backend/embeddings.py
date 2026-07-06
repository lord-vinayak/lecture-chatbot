from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
from typing import List, Tuple

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
MODEL_CACHE = {}

def get_embedding_model():
    """Lazy-load embedding model"""
    global MODEL_CACHE
    if "embedding_model" not in MODEL_CACHE:
        MODEL_CACHE["embedding_model"] = SentenceTransformer(EMBEDDING_MODEL)
    return MODEL_CACHE["embedding_model"]

def chunk_transcript(transcript: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split transcript into chunks with overlap for context.
    chunk_size and overlap are measured in approximate tokens.
    """
    # Simple word-based chunking (rough token estimate: 1 word ~= 1.3 tokens)
    words = transcript.split()
    chunks = []

    i = 0
    while i < len(words):
        # Calculate word count for this chunk
        chunk_words = words[i:i + int(chunk_size / 1.3)]
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)

        # Move forward by (chunk_size - overlap)
        i += int((chunk_size - overlap) / 1.3)

    return chunks

def embed_text(text: str) -> List[float]:
    """Embed single text string to vector"""
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts efficiently in batch"""
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()

def find_similar_chunks(
    question_embedding: List[float],
    chunk_embeddings: List[Tuple[str, List[float]]],
    top_k: int = 3
) -> List[str]:
    """
    Find top-k most similar chunks to question using cosine similarity.

    Args:
        question_embedding: Vector from embed_text(question)
        chunk_embeddings: List of (chunk_text, embedding_vector) tuples
        top_k: Number of results to return

    Returns:
        List of top-k similar chunk texts, sorted by relevance
    """
    import numpy as np

    if not chunk_embeddings:
        return []

    # Convert question embedding to numpy
    q_vec = np.array(question_embedding)

    # Calculate cosine similarity with all chunks
    similarities = []
    for chunk_text, chunk_vec in chunk_embeddings:
        chunk_vec = np.array(chunk_vec)
        # Cosine similarity
        similarity = np.dot(q_vec, chunk_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(chunk_vec))
        similarities.append((chunk_text, similarity))

    # Sort by similarity descending and return top-k
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [text for text, _ in similarities[:top_k]]
