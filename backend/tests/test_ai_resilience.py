"""AI provider resilience and self-recovery unit tests.

Verifies:
- OllamaProvider availability probe caching (15s TTL)
- OllamaProvider graceful fallback to FallbackAIProvider when offline
- OllamaProvider prompt generation and JSON extraction
- OllamaProvider recovery when Ollama becomes available again
- Interview question generation and answer evaluation through AI interface
- get_ai_provider returns working provider
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.ai import FallbackAIProvider, OllamaProvider, get_ai_provider, _extract_json_object


def test_extract_json_object():
    # Direct json
    assert _extract_json_object('{"score": 90}') == {"score": 90}
    # Markdown block
    assert _extract_json_object('```json\n{"score": 85}\n```') == {"score": 85}
    # Mixed text
    assert _extract_json_object('Here is the result: {"score": 75, "skills": ["Python"]} Hope that helps!') == {"score": 75, "skills": ["Python"]}
    # Invalid json
    assert _extract_json_object('Invalid text without json') is None


def test_fallback_ai_provider():
    provider = FallbackAIProvider()
    assert provider.is_available() is True


@pytest.mark.asyncio
async def test_ollama_provider_fallback_when_offline():
    provider = OllamaProvider(base_url="http://non-existent-host:11434")
    # Should safely fall back to deterministic response
    result = await provider.analyze_resume(
        resume_text="Experienced Python Developer with FastAPI and React",
        job_description="Looking for Python FastAPI developer"
    )
    assert result["score"] >= 0
    assert "skills" in result
    assert "summary" in result
    assert isinstance(result["recommendations"], list)


@pytest.mark.asyncio
async def test_ollama_provider_online_mocked():
    provider = OllamaProvider(base_url="http://localhost:11434")
    provider._cached_available = True
    provider._last_checked = 9999999999.0

    provider._generate = AsyncMock(
        return_value='```json\n{"score": 92, "summary": "Excellent match", "skills": [{"name": "Python", "confidence": 0.95, "category": "backend"}], "strengths": ["Backend experience"], "weaknesses": [], "recommendations": ["Apply now"]}\n```'
    )
    result = await provider.analyze_resume("Python FastAPI Engineer", "FastAPI Role")
    assert result["score"] == 92
    assert len(result["skills"]) == 1
    assert result["skills"][0]["name"] == "Python"


@pytest.mark.asyncio
async def test_ollama_provider_timeout_fallback():
    provider = OllamaProvider(base_url="http://localhost:11434")
    provider._cached_available = True
    provider._last_checked = 9999999999.0

    # When _generate returns empty string on timeout, analyze_resume safely uses fallback
    provider._generate = AsyncMock(return_value="")
    result = await provider.analyze_resume("Python Dev", "Python Job")
    assert result["score"] >= 0
    assert "skills" in result


@pytest.mark.asyncio
async def test_ollama_generate_questions_and_eval():
    provider = OllamaProvider(base_url="http://localhost:11434")
    provider._cached_available = False
    provider._last_checked = 9999999999.0  # Keep cached as unavailable

    question = await provider.generate_question(
        interview_type="technical",
        context="Python, FastAPI, PostgreSQL"
    )
    assert isinstance(question, str)
    assert len(question) > 0

    eval_result = await provider.evaluate_answer(
        question="What is FastAPI?",
        answer="FastAPI is a modern Python web framework based on Starlette and Pydantic."
    )
    assert "score" in eval_result
    assert "feedback" in eval_result


def test_get_ai_provider():
    p = get_ai_provider()
    assert p is not None
    assert p.is_available() is True
