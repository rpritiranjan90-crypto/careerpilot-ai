"""AI service abstraction layer.

Pluggable AI providers (Ollama local, optional cloud providers later).
The provider is selected dynamically; if Ollama is unavailable or fails, callers
automatically and transparently get deterministic fallback results so the app keeps working.
All LLM outputs are validated against Pydantic schemas before use.
"""

from __future__ import annotations

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import ValidationError

from app.schemas.ai import (
    AIJobMatch,
    AIResumeAnalysis,
    AIInterviewEvaluation,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def analyze_resume(
        self, resume_text: str, job_description: str | None = None
    ) -> dict[str, Any]:
        """Analyze a resume and return structured insights."""

    @abstractmethod
    async def match_job(self, resume_text: str, job_description: str) -> dict[str, Any]:
        """Compare resume with job description."""

    @abstractmethod
    async def generate_question(self, interview_type: str, context: str = "") -> str:
        """Generate an interview question."""

    @abstractmethod
    async def evaluate_answer(self, question: str, answer: str) -> dict[str, Any]:
        """Evaluate an interview answer."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider can serve requests right now."""


# ---------------------------------------------------------------------------
# Deterministic fallback (no AI)
# ---------------------------------------------------------------------------


class FallbackAIProvider(AIProvider):
    """Rule-based fallback used when no AI provider is reachable.

    This is intentionally always-available so the app degrades gracefully.
    """

    async def analyze_resume(
        self, resume_text: str, job_description: str | None = None
    ) -> dict[str, Any]:
        from app.services.resume_service import analyze_resume as fallback_analyze
        return fallback_analyze(resume_text, job_description).model_dump()

    async def match_job(self, resume_text: str, job_description: str) -> dict[str, Any]:
        from app.services.job_service import calculate_match
        from app.services.resume_service import extract_skills
        skills = [s.name for s in extract_skills(resume_text)]
        return calculate_match(skills, job_description).model_dump()

    async def generate_question(self, interview_type: str, context: str = "") -> str:
        from app.services.interview_service import start_interview
        return start_interview(interview_type, None).question

    async def evaluate_answer(self, question: str, answer: str) -> dict[str, Any]:
        from app.services.interview_service import evaluate_answer
        return evaluate_answer("fallback", answer, question)

    def is_available(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Ollama local provider
# ---------------------------------------------------------------------------


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """Find the first top-level JSON object in a model response."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = _JSON_OBJECT_RE.search(cleaned)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return None
    return None


class OllamaProvider(AIProvider):
    """Local Ollama provider.

    Talks to Ollama's HTTP API at /api/generate. Falls back to the
    deterministic provider on any error so the app keeps working.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:3b",
        timeout: int = 120,
        cache_ttl_seconds: float = 15.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.cache_ttl = cache_ttl_seconds
        self._cached_available: bool = False
        self._last_checked: float = 0.0
        self._fallback = FallbackAIProvider()

    def is_available(self) -> bool:
        now = time.monotonic()
        if self._last_checked > 0 and (now - self._last_checked) < self.cache_ttl:
            return self._cached_available

        self._last_checked = now
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
            self._cached_available = (resp.status_code == 200)
        except Exception as exc:
            logger.debug("Ollama not reachable at %s: %s", self.base_url, exc)
            self._cached_available = False
        return self._cached_available

    async def _generate(self, prompt: str) -> str:
        """Call Ollama /api/generate and return the response text."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 1024,
                        },
                    },
                )
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("response")
            return response_text.strip() if isinstance(response_text, str) else ""
        except httpx.HTTPError as exc:
            logger.warning("Ollama request failed: %s", exc)
            self._cached_available = False
            self._last_checked = time.monotonic()
            return ""
        except Exception as exc:
            logger.exception("Unexpected error calling Ollama: %s", exc)
            return ""

    async def analyze_resume(
        self, resume_text: str, job_description: str | None = None
    ) -> dict[str, Any]:
        if not self.is_available():
            return await self._fallback.analyze_resume(resume_text, job_description)

        prompt = (
            "You are a resume reviewer. Return a JSON object with keys: "
            "score (0-100 integer), summary, strengths (list of strings), "
            "weaknesses (list of strings), recommendations (list of strings), "
            "skills (list of {name, confidence, category}).\n\n"
            f"Resume:\n{resume_text[:4000]}"
        )
        if job_description:
            prompt += f"\n\nJob description:\n{job_description[:2000]}"

        response = await self._generate(prompt)
        parsed = _extract_json_object(response)
        if parsed:
            try:
                validated = AIResumeAnalysis.model_validate(parsed)
                return validated.model_dump()
            except ValidationError as exc:
                logger.warning(
                    "Ollama resume analysis failed schema validation (%s fields rejected); using fallback",
                    len(exc.errors()),
                )
        else:
            logger.info("Ollama response did not contain valid JSON; using fallback")
        return await self._fallback.analyze_resume(resume_text, job_description)

    async def match_job(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if not self.is_available():
            return await self._fallback.match_job(resume_text, job_description)

        prompt = (
            "Compare a resume with a job description. Return a JSON object with keys: "
            "match_score (0-100 integer), matched_skills "
            "(list of {skill, matched, priority}), missing_skills (list of strings), "
            "recommendations (list of strings), summary (one sentence).\n\n"
            f"Resume:\n{resume_text[:3000]}\n\n"
            f"Job description:\n{job_description[:2000]}"
        )

        response = await self._generate(prompt)
        parsed = _extract_json_object(response)
        if parsed:
            try:
                validated = AIJobMatch.model_validate(parsed)
                return validated.model_dump()
            except ValidationError:
                logger.warning("Ollama job match failed schema validation; using fallback")
        else:
            logger.info("Ollama response did not contain valid JSON; using fallback")
        return await self._fallback.match_job(resume_text, job_description)

    async def generate_question(self, interview_type: str, context: str = "") -> str:
        if not self.is_available():
            return await self._fallback.generate_question(interview_type, context)

        prompt = (
            f"Generate one interview question for a {interview_type} interview. "
            "Return only the question text, no preamble."
        )
        if context:
            prompt += f"\nContext: {context[:500]}"

        response = await self._generate(prompt)
        if response:
            for line in response.splitlines():
                line = line.strip().lstrip("0123456789.-) ").strip()
                if line and len(line) > 10:
                    return line
        return await self._fallback.generate_question(interview_type, context)

    async def evaluate_answer(self, question: str, answer: str) -> dict[str, Any]:
        if not self.is_available():
            return await self._fallback.evaluate_answer(question, answer)

        prompt = (
            "Evaluate an interview answer. Return a JSON object with keys: "
            "score (0-100 integer), feedback (one sentence), "
            "dimensions (list of {name, score, feedback}), improvements (list of strings).\n\n"
            f"Question: {question}\n\nAnswer: {answer[:2000]}"
        )

        response = await self._generate(prompt)
        parsed = _extract_json_object(response)
        if parsed:
            try:
                parsed.setdefault("interview_id", "ai-eval")
                validated = AIInterviewEvaluation.model_validate(parsed)
                return validated.model_dump()
            except ValidationError:
                logger.warning("Ollama evaluation failed schema validation; using fallback")
        else:
            logger.info("Ollama response did not contain valid JSON; using fallback")
        return await self._fallback.evaluate_answer(question, answer)


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------


_provider: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    """Get the configured AI provider.

    Returns an OllamaProvider instance that dynamically probes Ollama with TTL caching
    and transparently falls back to deterministic analysis when Ollama is offline.
    """
    global _provider
    if _provider is not None:
        return _provider

    from app.core.config import settings

    _provider = OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=settings.ollama_timeout,
    )
    return _provider


def use_fallback() -> None:
    """Force provider selection to deterministic fallback."""
    global _provider
    _provider = FallbackAIProvider()
