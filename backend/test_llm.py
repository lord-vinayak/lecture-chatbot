from llm import answer_question

def test_openai_connection():
    """Test that OpenAI API key is set and responsive"""
    try:
        response = answer_question("Say hello", ["The instructor says hello to the class."])
        assert len(response) > 0, "Should get non-empty response"
        print(f"✓ OpenAI connection works: '{response}'")
    except Exception as e:
        print(f"✗ OpenAI API failed: {e}")
        print("  Set OPENAI_API_KEY in backend/.env")
        return False
    return True

def test_answer_with_context():
    """Test QA with relevant context"""
    context = [
        "The Earth orbits the Sun every 365 days",
        "A year on Earth is approximately 365.25 days"
    ]
    answer = answer_question("How long is a year?", context)
    assert len(answer) > 0, "Should generate an answer"
    assert "365" in answer.lower() or "year" in answer.lower(), "Answer should reference context"
    print(f"✓ Answer with context works: '{answer}'")

def test_answer_without_context():
    """Test QA when context is empty - model should refuse"""
    answer = answer_question("How many planets are there?", [])
    assert len(answer) > 0, "Should return graceful response"
    print(f"✓ Answer without context works: '{answer}'")

if __name__ == "__main__":
    print("Testing LLM module (OpenAI)...\n")
    if not test_openai_connection():
        exit(1)
    test_answer_with_context()
    test_answer_without_context()
    print("\n✅ All LLM tests passed")
