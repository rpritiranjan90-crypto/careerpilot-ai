"""Transparent career readiness scoring system.

Career Readiness Score (0-100) is calculated as a weighted average of:
- Resume Score: 30%
- Job Match Score: 25%
- Interview Score: 25%
- Skill Coverage: 20%

All components must be present for a complete score.
"""

from typing import Any


def calculate_career_readiness(
    resume_score: int | None = None,
    job_match_score: int | None = None,
    interview_score: int | None = None,
    skill_coverage: int | None = None,
) -> dict[str, Any]:
    """Calculate overall career readiness score.

    Returns a dictionary with the overall score, component breakdown,
    strongest area, and improvement recommendations.

    Args:
        resume_score: Resume quality score (0-100)
        job_match_score: Latest job match percentage (0-100)
        interview_score: Latest interview performance (0-100)
        skill_coverage: Percentage of target role skills covered (0-100)

    Returns:
        Dictionary with overall score and breakdown.
    """
    components = {
        "resume": {"score": resume_score or 0, "weight": 0.30},
        "job_match": {"score": job_match_score or 0, "weight": 0.25},
        "interview": {"score": interview_score or 0, "weight": 0.25},
        "skills": {"score": skill_coverage or 0, "weight": 0.20},
    }

    # Calculate weighted average
    total_weight = sum(c["weight"] for c in components.values())
    weighted_sum = sum(c["score"] * c["weight"] for c in components.values())

    overall_score = int(weighted_sum / total_weight)

    # Find strongest and weakest areas
    sorted_components = sorted(
        components.items(),
        key=lambda x: x[1]["score"],
        reverse=True,
    )

    strongest = sorted_components[0]
    weakest = sorted_components[-1]

    # Generate recommendation based on weakest area
    recommendations = {
        "resume": "Improve your resume by adding measurable achievements and project details.",
        "job_match": "Target roles that better match your current skills, or build missing skills.",
        "interview": "Practice more interview questions to improve clarity and structure.",
        "skills": "Identify and develop the key skills required for your target role.",
    }

    return {
        "overall_score": overall_score,
        "breakdown": {
            name: {"score": data["score"], "weight": data["weight"]}
            for name, data in components.items()
        },
        "strongest_area": {
            "name": strongest[0],
            "label": strongest[0].replace("_", " ").title(),
            "score": strongest[1]["score"],
        },
        "needs_improvement": {
            "name": weakest[0],
            "label": weakest[0].replace("_", " ").title(),
            "score": weakest[1]["score"],
        },
        "recommended_next_step": recommendations[weakest[0]],
    }
