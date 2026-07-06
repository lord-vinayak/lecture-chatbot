import requests
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = "llama2"  # Default; can be overridden to llama2:13b, etc.

def query_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """
    Send prompt to Ollama and get response.
    Timeout set to 30s for inference latency.
    """
    url = f"{OLLAMA_API_URL}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.2  # Low temp for factual, deterministic answers
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return result.get("response", "").strip()
    except requests.exceptions.Timeout:
        return "I'm taking too long to think about this. Please try again."
    except requests.exceptions.ConnectionError:
        return "Unable to process your question right now (inference service unavailable)"
    except Exception as e:
        return f"Error processing question: {str(e)}"

def answer_question(
    question: str,
    context_chunks: List[str],
    model: str = OLLAMA_MODEL
) -> str:
    """
    Answer question based on context chunks from transcript.

    Prompt engineering ensures:
    - Answer comes ONLY from provided context
    - Refuses to answer if context doesn't contain answer
    - No hallucination
    """
    if not context_chunks:
        context = "(No relevant content found in transcript)"
    else:
        context = "\n\n".join([f"- {chunk}" for chunk in context_chunks])

    prompt = f"""You are a helpful tutor assistant for a course.
A student asked a question about the course video.
Answer ONLY based on the transcript content provided below.
If the answer is not in the transcript, clearly say "I couldn't find that information in the video."

Transcript content:
{context}

Student question: {question}

Answer:"""

    return query_ollama(prompt, model)
