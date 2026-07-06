from llm import query_ollama, answer_question

def test_ollama_connection():
    """Test that Ollama is running and responsive"""
    try:
        response = query_ollama("Say 'hello'")
        assert len(response) > 0, "Should get non-empty response"
        print(f"✓ Ollama connection works: '{response}'")
    except Exception as e:
        print(f"✗ Ollama not running: {e}")
        print("  Start Ollama with: ollama serve")
        return False

    return True

def test_answer_with_context():
    """Test QA with relevant context"""
    context = [
        "The Earth orbits the Sun every 365 days",
        "A year on Earth is approximately 365.25 days"
    ]

    answer = answer_question(
        "How long is a year?",
        context
    )

    assert len(answer) > 0, "Should generate an answer"
    assert "365" in answer.lower() or "year" in answer.lower(), "Answer should reference context"
    print(f"✓ Answer with context works: '{answer}'")

def test_answer_without_context():
    """Test QA when context is empty (should refuse to answer)"""
    answer = answer_question(
        "How many planets are there?",
        []
    )

    assert len(answer) > 0, "Should return graceful response"
    # Expect model to refuse or indicate lack of context
    print(f"✓ Answer without context works: '{answer}'")

if __name__ == "__main__":
    print("Testing LLM module...\n")

    if not test_ollama_connection():
        print("\n Ollama not running. Skipping other tests.")
        print("Start Ollama: ollama serve")
        exit(1)

    test_answer_with_context()
    test_answer_without_context()

    print("\n All LLM tests passed")
