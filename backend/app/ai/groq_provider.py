"""Groq cloud AI provider (free tier).

Uses Groq's OpenAI-compatible API for fast LLM inference.
Free tier: https://console.groq.com (no credit card required).
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.ai import (
    AIProvider,
    FallbackAIProvider,
    _extract_json_object,
)
from app.schemas.ai import (
    AIJobMatch,
    AIInterviewEvaluation,
    AIResumeAnalysis,
)

logger = logging.getLogger(__name__)


class GroqProvider(AIProvider):
    """Groq cloud provider using OpenAI-compatible API.

    Falls back to deterministic analysis if Groq is unreachable or returns invalid output.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-8b-instant",
        base_url: str = "https://api.groq.com/openai/v1",
        timeout: int = 30,
    ):
        if not api_key:
            raise ValueError("Groq API key is required")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._fallback = FallbackAIProvider()
        self._cached_available: bool = False
        self._last_checked: float = 0.0
        self._cache_ttl: float = 30.0

    def is_available(self) -> bool:
        now = time.monotonic()
        if self._last_checked > 0 and (now - self._last_checked) < self._cache_ttl:
            return self._cached_available

        self._last_checked = now
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
            self._cached_available = (resp.status_code == 200)
        except Exception as exc:
            logger.debug("Groq not reachable: %s", exc)
            self._cached_available = False
        return self._cached_available

    async def _generate(self, prompt: str, system: str | None = None) -> str:
        """Call Groq's chat completions API and return the response text."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 1024,
                    },
                )
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()
            return ""
        except httpx.HTTPError as exc:
            logger.warning("Groq request failed: %s", exc)
            self._cached_available = False
            self._last_checked = time.monotonic()
            return ""
        except Exception as exc:
            logger.exception("Unexpected error calling Groq: %s", exc)
            return ""

    async def analyze_resume(
        self, resume_text: str, job_description: str | None = None
    ) -> dict[str, Any]:
        if not self.is_available():
            return await self._fallback.analyze_resume(resume_text, job_description)

        system = (
            "You are an expert resume reviewer. Always respond with valid JSON only, "
            "no markdown, no preamble."
        )
        prompt = (
            "Analyze this resume. Return a JSON object with keys: "
            "score (0-100 integer), summary (1-2 sentences), strengths (list of 3-5 strings), "
            "weaknesses (list of 3-5 strings), recommendations (list of 3-5 strings), "
            "skills (list of {name, confidence (0-1 float), category}).\n\n"
            f"Resume:\n{resume_text[:4000]}"
        )
        if job_description:
            prompt += f"\n\nTarget job description:\n{job_description[:2000]}"

        response = await self._generate(prompt, system)
        parsed = _extract_json_object(response)
        if parsed:
            try:
                validated = AIResumeAnalysis.model_validate(parsed)
                return validated.model_dump()
            except Exception as exc:
                logger.warning("Groq resume analysis validation failed: %s", exc)
        else:
            logger.info("Groq response did not contain valid JSON; using fallback")
        return await self._fallback.analyze_resume(resume_text, job_description)

    async def match_job(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if not self.is_available():
            return await self._fallback.match_job(resume_text, job_description)

        system = "You are a career coach. Respond with valid JSON only, no markdown."
        prompt = (
            "Compare this resume with the job description. Return a JSON object with keys: "
            "match_score (0-100 integer), matched_skills (list of {skill, matched (bool), priority (high|medium|low)}), "
            "missing_skills (list of strings), recommendations (list of 3-5 strings), summary (one sentence).\n\n"
            f"Resume:\n{resume_text[:3000]}\n\n"
            f"Job description:\n{job_description[:2000]}"
        )

        response = await self._generate(prompt, system)
        parsed = _extract_json_object(response)
        if parsed:
            try:
                validated = AIJobMatch.model_validate(parsed)
                return validated.model_dump()
            except Exception as exc:
                logger.warning("Groq job match validation failed: %s", exc)
        else:
            logger.info("Groq response did not contain valid JSON; using fallback")
        return await self._fallback.match_job(resume_text, job_description)

    async def generate_question(self, interview_type: str, context: str = "") -> str:
        if not self.is_available():
            return await self._fallback.generate_question(interview_type, context)

        system = "You are an experienced interviewer. Ask one clear question."
        prompt = (
            f"Generate one interview question for a {interview_type} interview. "
            "Return only the question text, no preamble, no numbering."
        )
        if context:
            prompt += f"\nContext: {context[:500]}"

        response = await self._generate(prompt, system)
        if response and len(response) > 10:
            return response.split("\n")[0].strip()
        return await self._fallback.generate_question(interview_type, context)

    async def evaluate_answer(self, question: str, answer: str) -> dict[str, Any]:
        if not self.is_available():
            return await self._fallback.evaluate_answer(question, answer)

        system = "You are an interview evaluator. Respond with valid JSON only."
        prompt = (
            "Evaluate this interview answer. Return a JSON object with keys: "
            "score (0-100 integer), feedback (1-2 sentences), "
            "dimensions (list of {name, score (0-100), feedback}), "
            "improvements (list of 2-4 strings).\n\n"
            f"Question: {question}\n\nAnswer: {answer[:2000]}"
        )

        response = await self._generate(prompt, system)
        parsed = _extract_json_object(response)
        if parsed:
            try:
                parsed.setdefault("interview_id", "ai-eval")
                validated = AIInterviewEvaluation.model_validate(parsed)
                return validated.model_dump()
            except Exception as exc:
                logger.warning("Groq evaluation validation failed: %s", exc)
        else:
            logger.info("Groq response did not contain valid JSON; using fallback")
        return await self._fallback.evaluate_answer(question, answer)
