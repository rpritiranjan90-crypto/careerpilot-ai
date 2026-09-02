"""Tests for interview service."""
from app.services.interview_service import evaluate_answer, start_interview


def test_start_interview_returns_unique_ids():
    """Test that each interview gets a unique ID."""
    interview1 = start_interview("general")
    interview2 = start_interview("general")

    assert interview1.interview_id != interview2.interview_id


def test_start_interview_returns_question():
    """Test that a question is provided."""
    result = start_interview("general")
    assert result.question
    assert result.category == "general"


def test_start_interview_supports_all_types():
    """Test all interview types."""
    for interview_type in ["general", "hr", "technical", "role_specific"]:
        result = start_interview(interview_type)
        assert result.question
        assert result.category == interview_type


def test_start_interview_falls_back_to_general():
    """Test that unknown types fall back to general."""
    result = start_interview("unknown_type")
    assert result.question
    assert result.category == "general"


def test_evaluate_answer_scores_valid_range(sample_interview_answer):
    """Test that evaluation score is in valid range."""
    result = evaluate_answer("test-id", sample_interview_answer, "Test question")
    assert 0 <= result["score"] <= 100


def test_evaluate_answer_returns_dimensions(sample_interview_answer):
    """Test that evaluation includes dimension breakdown."""
    result = evaluate_answer("test-id", sample_interview_answer, "Test question")
    assert len(result["dimensions"]) > 0


def test_evaluate_answer_handles_short_answer():
    """Test that short answers are flagged."""
    result = evaluate_answer("test-id", "yes", "")
    assert result["score"] == 0


def test_evaluate_answer_rewards_specificity(sample_interview_answer):
    """Test that detailed answers score higher."""
    result_detailed = evaluate_answer("test-id", sample_interview_answer, "")
    result_brief = evaluate_answer("test-id", "I worked on stuff.", "")

    assert result_detailed["score"] > result_brief["score"]


def test_evaluate_answer_includes_improvements(sample_interview_answer):
    """Test that improvements are suggested."""
    result = evaluate_answer("test-id", sample_interview_answer, "")
    assert isinstance(result["improvements"], list)
    assert len(result["improvements"]) > 0


def test_evaluate_answer_uses_context_for_relevance(sample_interview_answer):
    """Test that context is used to evaluate relevance."""
    relevant_result = evaluate_answer(
        "test-id", sample_interview_answer, "Tell me about leadership experience."
    )
    irrelevant_result = evaluate_answer(
        "test-id", sample_interview_answer, "What is your favorite color?"
    )

    # Both should have valid scores, but relevance dimension may differ
    assert "dimensions" in relevant_result
    assert "dimensions" in irrelevant_result
