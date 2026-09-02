"""Interview management service.

Provides deterministic interview question selection and answer evaluation.
This module works without AI dependencies for MVP free-first deployment.
"""

import re
import uuid

from app.schemas.interview import (
    InterviewResponse,
)

INTERVIEW_QUESTIONS = {
    "general": [
        "Tell me about yourself and your background.",
        "Why are you interested in this role?",
        "What are your greatest strengths?",
        "Where do you see yourself in 5 years?",
        "Describe a challenging situation you handled successfully.",
    ],
    "hr": [
        "Why did you leave your previous position?",
        "How do you handle conflicts with coworkers?",
        "What motivates you at work?",
        "Describe your ideal work environment.",
        "How do you prioritize work under pressure?",
    ],
    "technical": [
        "Explain a technical project you worked on recently.",
        "How do you debug a complex problem in your work?",
        "What is your experience with version control?",
        "Describe your approach to learning new technologies.",
        "How do you ensure code quality in your projects?",
    ],
    "role_specific": [
        "What relevant experience do you have for this role?",
        "Describe a time you used your expertise to solve a problem.",
        "How do you stay current with industry trends?",
        "What unique value would you bring to this position?",
        "Tell me about a project that demonstrates your skills.",
    ],
}


def start_interview(
    interview_type: str,
    question: str | None = None,
) -> InterviewResponse:
    """Start an interview session and return the first question."""
    interview_id = str(uuid.uuid4())

    if question:
        selected_question = question
    else:
        questions = INTERVIEW_QUESTIONS.get(
            interview_type, INTERVIEW_QUESTIONS["general"]
        )
        idx = abs(hash(interview_id)) % len(questions)
        selected_question = questions[idx]

    # Normalize unknown type to "general" so the response category is valid
    normalized_type = (
        interview_type
        if interview_type in INTERVIEW_QUESTIONS
        else "general"
    )

    tips = [
        "Structure your answer using the STAR method",
        "Be specific with examples from your experience",
        "Keep your answer concise (1-2 minutes when spoken)",
        "Show confidence and authenticity",
    ]

    return InterviewResponse(
        interview_id=interview_id,
        question=selected_question,
        category=normalized_type,
        tips=tips,
    )


def evaluate_answer(
    interview_id: str,
    answer: str,
    context: str = "",
) -> dict:
    """Evaluate user's interview answer using deterministic scoring."""
    if not answer or len(answer.strip()) < 10:
        return {
            "score": 0,
            "feedback": "Answer is too short. Please provide a substantive response.",
            "dimensions": [],
        }

    word_count = len(answer.split())
    if word_count >= 30:
        length_score = min(30, word_count - 30)
    else:
        length_score = word_count // 2

    has_numbers = bool(re.search(r"\d+", answer))
    has_examples = any(kw in answer.lower() for kw in ["for example", "such as", "instance", "when"])
    specificity_score = 0
    if has_numbers:
        specificity_score += 15
    if has_examples:
        specificity_score += 10

    paragraphs = [p for p in answer.split("\n\n") if p.strip()]
    structure_score = min(20, len(paragraphs) * 7)

    sentences = [s for s in re.split(r"[.!?]+", answer) if s.strip()]
    if sentences:
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if 10 <= avg_length <= 20:
            clarity_score = 15
        elif 5 <= avg_length <= 25:
            clarity_score = 10
        else:
            clarity_score = 5
    else:
        clarity_score = 0

    if context:
        context_words = set(re.findall(r"\b\w+\b", context.lower()))
        answer_words = set(re.findall(r"\b\w+\b", answer.lower()))
        overlap = len(context_words & answer_words)
        relevance_score = min(10, overlap)
    else:
        relevance_score = 5

    total_score = (
        length_score
        + specificity_score
        + structure_score
        + clarity_score
        + relevance_score
    )

    dimensions = [
        {
            "name": "Relevance",
            "score": relevance_score * 10,
            "feedback": "Good relevance." if relevance_score >= 7 else "Stay focused on the question.",
        },
        {
            "name": "Clarity",
            "score": clarity_score * 100 // 15,
            "feedback": "Clear and well-articulated." if clarity_score >= 10 else "Use shorter sentences.",
        },
        {
            "name": "Specificity",
            "score": specificity_score * 100 // 25,
            "feedback": "Strong use of examples." if specificity_score >= 15 else "Add specific examples.",
        },
        {
            "name": "Structure",
            "score": structure_score * 100 // 20,
            "feedback": "Well-structured response." if structure_score >= 15 else "Organize into clear sections.",
        },
    ]

    feedback_parts = []
    if total_score >= 80:
        feedback_parts.append("Excellent answer demonstrating strong communication skills.")
    elif total_score >= 60:
        feedback_parts.append("Good answer with room for improvement.")
    else:
        feedback_parts.append("Answer needs improvement.")
    if not has_examples:
        feedback_parts.append("Add specific examples to strengthen your answer.")
    if word_count < 50:
        feedback_parts.append("Provide more detail.")

    return {
        "interview_id": interview_id,
        "score": total_score,
        "feedback": " ".join(feedback_parts),
        "dimensions": dimensions,
        "improvements": [
            "Use the STAR method (Situation, Task, Action, Result)",
            "Include specific examples and metrics",
            "Keep your answer between 60-120 seconds",
            "Practice and be authentic",
        ],
    }
