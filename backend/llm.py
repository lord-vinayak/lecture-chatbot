from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def answer_question(question: str, context_chunks: List[str]) -> str:
    """
    Answer question based on context chunks from transcript using OpenAI.
    Answers ONLY from provided context - refuses if answer isn't there.
    """
    if not context_chunks:
        context = "(No relevant content found in transcript)"
    else:
        context = "\n\n".join([f"- {chunk}" for chunk in context_chunks])

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful tutor assistant for a course. "
                        "Answer ONLY based on the transcript content provided. "
                        'If the answer is not in the transcript, say "I couldn\'t find that information in the video."'
                    ),
                },
                {
                    "role": "user",
                    "content": f"Transcript content:\n{context}\n\nStudent question: {question}",
                },
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Unable to process your question right now: {str(e)}"
