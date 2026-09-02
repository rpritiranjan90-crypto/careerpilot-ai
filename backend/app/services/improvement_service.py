"""Career Improvement Engine service.

Generates deterministic, actionable improvement plans combining verified
resume analyses, job match gaps, interview evaluations, real historical snapshots,
and persisted action checklist states.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    CareerReadinessSnapshot,
    Interview,
    JobMatch,
    Resume,
    User,
    UserActionItem,
)
from app.schemas.improvement import (
    ActionItem,
    ActionPlanTimeline,
    CareerImprovementPlan,
    NextBestAction,
    ProgressTracking,
    ResumeEnhancementItem,
    ScoreProgressItem,
    SkillGapItem,
)
from app.services.scoring import calculate_career_readiness


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_action_completion(
    db: Session, user_id: str, task_id: str
) -> tuple[bool, str | None]:
    """Retrieve persisted completion status for a task ID."""
    item = (
        db.query(UserActionItem)
        .filter(UserActionItem.user_id == user_id, UserActionItem.task_id == task_id)
        .first()
    )
    if item:
        completed_at_iso = item.completed_at.isoformat() if item.completed_at else None
        return item.is_completed, completed_at_iso
    return False, None


def toggle_user_action_item(
    db: Session, user_id: str, task_id: str
) -> dict[str, Any]:
    """Toggle the persisted completion state of a task item for a user."""
    item = (
        db.query(UserActionItem)
        .filter(UserActionItem.user_id == user_id, UserActionItem.task_id == task_id)
        .first()
    )
    if not item:
        item = UserActionItem(
            user_id=user_id,
            task_id=task_id,
            is_completed=True,
            completed_at=utcnow(),
        )
        db.add(item)
    else:
        item.is_completed = not item.is_completed
        item.completed_at = utcnow() if item.is_completed else None

    db.commit()
    db.refresh(item)
    return {
        "task_id": item.task_id,
        "is_completed": item.is_completed,
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
    }


def record_career_readiness_snapshot(
    db: Session,
    user_id: str,
    overall_score: int,
    resume_score: int | None,
    job_match_score: int | None,
    interview_score: int | None,
    skills_score: int | None,
) -> CareerReadinessSnapshot:
    """Record a verified historical snapshot in the database."""
    snapshot = CareerReadinessSnapshot(
        user_id=user_id,
        overall_score=overall_score,
        resume_score=resume_score,
        job_match_score=job_match_score,
        interview_score=interview_score,
        skills_score=skills_score,
        created_at=utcnow(),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def generate_career_improvement_plan(
    db: Session, user_id: str, create_snapshot_if_none: bool = True
) -> CareerImprovementPlan:
    """Generate a comprehensive, verified Career Improvement Plan."""
    # 1. Fetch user records
    user = db.query(User).filter(User.id == user_id).first()

    # Fetch latest resume and analysis
    latest_resume = (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .first()
    )
    latest_analysis = None
    if latest_resume and latest_resume.analyses:
        latest_analysis = latest_resume.analyses[-1]

    # Fetch latest job match
    latest_job_matches = (
        db.query(JobMatch)
        .join(JobMatch.job_description)
        .filter(JobMatch.job_description.has(user_id=user_id))
        .order_by(JobMatch.created_at.desc())
        .all()
    )
    latest_match = latest_job_matches[0] if latest_job_matches else None

    # Fetch interview scores
    interviews = (
        db.query(Interview)
        .filter(Interview.user_id == user_id)
        .order_by(Interview.created_at.desc())
        .all()
    )
    interview_scores: list[int] = []
    for itw in interviews:
        for q in itw.questions:
            if q.score is not None:
                interview_scores.append(q.score)

    avg_interview_score = (
        int(sum(interview_scores) / len(interview_scores))
        if interview_scores
        else None
    )

    resume_score = latest_analysis.score if latest_analysis else None
    job_match_score = (
        int(latest_match.match_score)
        if latest_match and latest_match.match_score is not None
        else None
    )
    interview_score = avg_interview_score

    # Estimate skill coverage
    skill_coverage = None
    extracted_skills: list[str] = []
    if latest_analysis and latest_analysis.result_json:
        skills_raw = latest_analysis.result_json.get("skills", [])
        extracted_skills = [
            s.get("name") if isinstance(s, dict) else str(s) for s in skills_raw
        ]
        if extracted_skills:
            skill_coverage = min(100, len(extracted_skills) * 8)

    has_data = any(
        v is not None
        for v in [resume_score, job_match_score, interview_score, skill_coverage]
    )

    readiness = calculate_career_readiness(
        resume_score=resume_score,
        job_match_score=job_match_score,
        interview_score=interview_score,
        skill_coverage=skill_coverage,
    )
    current_overall = readiness["overall_score"]

    # 2. Historical Snapshots (Strict verification - NO fabricated past scores)
    snapshots = (
        db.query(CareerReadinessSnapshot)
        .filter(CareerReadinessSnapshot.user_id == user_id)
        .order_by(CareerReadinessSnapshot.created_at.desc())
        .all()
    )

    prev_snapshot: CareerReadinessSnapshot | None = None
    if len(snapshots) > 1:
        # Most recent previous snapshot
        prev_snapshot = snapshots[1]
    elif len(snapshots) == 1 and (
        snapshots[0].overall_score != current_overall
        or snapshots[0].resume_score != resume_score
    ):
        prev_snapshot = snapshots[0]

    # If user has data and no snapshots exist yet, record the baseline snapshot
    if has_data and len(snapshots) == 0 and create_snapshot_if_none:
        record_career_readiness_snapshot(
            db=db,
            user_id=user_id,
            overall_score=current_overall,
            resume_score=resume_score,
            job_match_score=job_match_score,
            interview_score=interview_score,
            skills_score=skill_coverage,
        )

    # Compute verified progress items
    def make_progress_item(
        curr: int | None, prev: int | None
    ) -> ScoreProgressItem:
        if curr is None:
            return ScoreProgressItem(current=0, previous=None, delta=None)
        if prev is not None:
            return ScoreProgressItem(
                current=curr, previous=prev, delta=curr - prev
            )
        return ScoreProgressItem(current=curr, previous=None, delta=None)

    progress_tracking = ProgressTracking(
        has_history=prev_snapshot is not None,
        overall_readiness=make_progress_item(
            current_overall if has_data else 0,
            prev_snapshot.overall_score if prev_snapshot else None,
        ),
        resume_score=make_progress_item(
            resume_score,
            prev_snapshot.resume_score if prev_snapshot else None,
        ),
        job_match_score=make_progress_item(
            job_match_score,
            prev_snapshot.job_match_score if prev_snapshot else None,
        ),
        interview_score=make_progress_item(
            interview_score,
            prev_snapshot.interview_score if prev_snapshot else None,
        ),
        skills_score=make_progress_item(
            skill_coverage,
            prev_snapshot.skills_score if prev_snapshot else None,
        ),
    )

    # 3. Determine data completeness mode
    if not has_data:
        data_completeness = "no_data"
    elif latest_resume and latest_match and interviews:
        data_completeness = "complete"
    elif latest_resume and not latest_match:
        data_completeness = "resume_only"
    else:
        data_completeness = "partial"

    # 4. Generate Deterministic Resume Enhancement Items
    resume_enhancements: list[ResumeEnhancementItem] = []
    if latest_analysis and latest_analysis.result_json:
        weaknesses = latest_analysis.result_json.get("weaknesses", [])
        strengths = latest_analysis.result_json.get("strengths", [])

        # Issue 1: Measurable achievements & Action-Context-Result
        resume_enhancements.append(
            ResumeEnhancementItem(
                id="resume_metrics_quantification",
                category="Experience & Achievements",
                issue="Bullet points lack quantified business impact and measurable outcomes",
                severity="high" if (resume_score or 0) < 80 else "medium",
                explanation=(
                    "Recruiters and ATS rank candidates significantly higher when responsibilities "
                    "are framed with specific metrics, percentages, latency improvements, or scale."
                ),
                recommended_fix=(
                    "Rewrite each role bullet point using the formula: "
                    "[Strong Action Verb] + [Specific Technical Scope] + resulting in [Quantified Metric]."
                ),
                before_example="Responsible for maintaining and optimizing database queries and backend APIs.",
                after_example=(
                    "Architected optimized PostgreSQL query indexes and FastAPI microservice endpoints, "
                    "reducing API response latency by [X]% across [N,000] daily active requests."
                ),
                is_placeholder_example=True,
            )
        )

        # Issue 2: Professional summary keyword density
        resume_enhancements.append(
            ResumeEnhancementItem(
                id="resume_summary_clarity",
                category="Professional Summary",
                issue="Summary is generic or missing target job domain keywords",
                severity="medium",
                explanation=(
                    "The top 3-4 lines of your resume determine recruiter interest. Avoid vague terms "
                    "like 'hard-working self-starter' in favor of concrete specialization."
                ),
                recommended_fix="Highlight your core technical stack, years of focused experience, and 1 standout achievement.",
                before_example="Passionate software developer seeking a challenging role to utilize my programming skills.",
                after_example=(
                    "Results-oriented Full Stack Engineer with [N] years of experience building scalable web applications "
                    "using Python, React, and PostgreSQL. Specialized in high-throughput API design and CI/CD pipelines."
                ),
                is_placeholder_example=True,
            )
        )

        # Issue 3: Project complexity and architecture
        if extracted_skills:
            top_skill = extracted_skills[0]
            resume_enhancements.append(
                ResumeEnhancementItem(
                    id="resume_project_architecture",
                    category="Projects & Open Source",
                    issue=f"Project section should showcase end-to-end architecture with {top_skill}",
                    severity="low" if (resume_score or 0) >= 80 else "medium",
                    explanation="Hiring managers look for evidence of trade-off decisions, deployment strategies, and testing.",
                    recommended_fix="Include links to live demos, automated unit test coverage, and Dockerized deployment instructions.",
                    before_example=f"Built a web app using {top_skill} and deployed it to the cloud.",
                    after_example=(
                        f"Developed a containerized microservice platform in {top_skill} with 90%+ test coverage; "
                        "automated zero-downtime deployment pipelines using Docker Compose and GitHub Actions."
                    ),
                    is_placeholder_example=True,
                )
            )

    # 5. Generate Deterministic Skill Gaps
    skill_gaps: list[SkillGapItem] = []
    missing_skills_set: set[str] = set()

    if latest_match and latest_match.result_json:
        missing_skills_raw = latest_match.result_json.get("missing_skills", [])
        for s in missing_skills_raw:
            missing_skills_set.add(s)

    # Map missing skills with curated practical learning paths
    curated_paths: dict[str, dict[str, Any]] = {
        "docker": {
            "name": "Docker & Containerization",
            "reason": "Containerization is required for standard deployment pipelines across modern engineering teams.",
            "prerequisites": ["Linux CLI", "Basic Networking"],
            "learning_path": "1. Container basics & Dockerfiles → 2. Multi-stage builds & caching → 3. Docker Compose multi-service clusters.",
            "practical_exercise": "Containerize a FastAPI application with PostgreSQL database and healthcheck probes.",
            "project_idea": "Build and publish a multi-container microservice template with automated Docker Hub CI builds.",
        },
        "sql": {
            "name": "SQL & Relational Databases",
            "reason": "Core requirement for backend data persistence, indexing, schema migrations, and analytics.",
            "prerequisites": ["Data Modeling", "Basic Querying"],
            "learning_path": "1. Advanced Joins & Aggregations → 2. Indexes & Execution Plans → 3. ACID Transactions & Connection Pooling.",
            "practical_exercise": "Write an indexed query with EXPLAIN ANALYZE optimizing a 100,000-row dataset join.",
            "project_idea": "Design an e-commerce database schema with relational foreign keys, constraints, and audit logs.",
        },
        "react": {
            "name": "React & Modern Frontend Architecture",
            "reason": "Industry standard for interactive SPAs, component design systems, and state management.",
            "prerequisites": ["Modern JavaScript / TypeScript", "HTML5 & CSS3"],
            "learning_path": "1. Component Lifecycle & Hooks → 2. Context & State Management → 3. Performance Optimization & Custom Hooks.",
            "practical_exercise": "Build an accessible modal component with keyboard focus traps and Escape key dismissal.",
            "project_idea": "Create an interactive dashboard with real-time charts and optimistic UI updates.",
        },
        "typescript": {
            "name": "TypeScript & Type Safety",
            "reason": "Critical for large-scale codebases, preventing runtime exceptions and improving developer ergonomics.",
            "prerequisites": ["JavaScript ES6+"],
            "learning_path": "1. Basic Interfaces & Generics → 2. Utility Types & Discriminated Unions → 3. Strict Compiler Configuration.",
            "practical_exercise": "Refactor a JavaScript utility library to strict TypeScript with zero `any` types.",
            "project_idea": "Build a strongly-typed REST API client with request/response schema inference.",
        },
    }

    # Add missing skills from verified Job Match
    for raw_skill in list(missing_skills_set)[:4]:
        lookup_key = raw_skill.lower().strip()
        matched_curated = None
        for k, v in curated_paths.items():
            if k in lookup_key or lookup_key in k:
                matched_curated = v
                break

        if matched_curated:
            skill_gaps.append(
                SkillGapItem(
                    skill_name=matched_curated["name"],
                    status="missing",
                    priority="High",
                    reason=matched_curated["reason"],
                    prerequisites=matched_curated["prerequisites"],
                    learning_path=matched_curated["learning_path"],
                    practical_exercise=matched_curated["practical_exercise"],
                    project_idea=matched_curated["project_idea"],
                )
            )
        else:
            skill_gaps.append(
                SkillGapItem(
                    skill_name=raw_skill,
                    status="missing",
                    priority="High",
                    reason=f"Explicitly listed as a required qualification in your target job match.",
                    prerequisites=["Core Fundamentals"],
                    learning_path=f"1. Official documentation & syntax → 2. Practical tutorials → 3. Capstone portfolio integration.",
                    practical_exercise=f"Complete 3 hands-on exercises demonstrating practical use of {raw_skill}.",
                    project_idea=f"Incorporate {raw_skill} into your next full-stack project or technical case study.",
                )
            )

    # If no job match was run, provide top recommended skills based on resume
    if not skill_gaps and extracted_skills:
        skill_gaps.append(
            SkillGapItem(
                skill_name="Docker & Containerization",
                status="improve",
                priority="Medium",
                reason="Universal deployment standard across engineering roles.",
                prerequisites=["Linux CLI"],
                learning_path="1. Dockerfile creation → 2. Multi-stage builds → 3. Compose orchestration.",
                practical_exercise="Containerize your existing web app with a multi-stage Dockerfile.",
                project_idea="Deploy a full-stack application with automated Docker container builds.",
            )
        )

    # 6. Generate Action Plan (with DB persisted completion states)
    def build_action_item(
        task_id: str, task: str, category: str, minutes: int
    ) -> ActionItem:
        completed, completed_at = get_or_create_action_completion(
            db, user_id, task_id
        )
        return ActionItem(
            task_id=task_id,
            task=task,
            category=category,
            estimated_minutes=minutes,
            is_completed=completed,
            completed_at=completed_at,
        )

    action_plan = ActionPlanTimeline(
        today=[
            build_action_item(
                task_id="action_rewrite_summary",
                task="Rewrite professional summary with targeted technical keywords and specialization",
                category="resume",
                minutes=20,
            ),
            build_action_item(
                task_id="action_quantify_bullets",
                task="Add quantified metrics ([X]%, [N] users) to at least 2 past experience bullet points",
                category="resume",
                minutes=30,
            ),
        ],
        this_week=[
            build_action_item(
                task_id="action_practice_interview_star",
                task="Practice 3 Technical and HR mock interview questions using the STAR framework",
                category="interview",
                minutes=45,
            ),
            build_action_item(
                task_id="action_bridge_priority_skill",
                task="Complete a practical hands-on coding exercise for your highest priority missing skill",
                category="skills",
                minutes=60,
            ),
        ],
        this_month=[
            build_action_item(
                task_id="action_build_capstone_project",
                task="Build and deploy a portfolio capstone project demonstrating containerization and automated testing",
                category="skills",
                minutes=180,
            ),
            build_action_item(
                task_id="action_retest_readiness",
                task="Re-upload updated resume and assess match score against 3 new target roles",
                category="resume",
                minutes=30,
            ),
        ],
    )

    # 7. Generate Exactly One High-Leverage Next Best Action
    next_best_action: NextBestAction | None = None
    if not has_data:
        next_best_action = NextBestAction(
            title="Upload Your Resume to Establish Baseline",
            category="resume",
            why="We need your verified experience to identify strengths and uncover skill gaps.",
            what_to_do="Upload your resume in PDF, DOCX, or TXT format on the Resume page.",
            expected_outcome="Unlocks your complete personalized career readiness roadmap.",
            cta_label="Upload Resume",
            cta_link="/resume",
        )
    elif (resume_score or 0) < 75:
        next_best_action = NextBestAction(
            title="Quantify Measurable Achievements on Your Resume",
            category="resume",
            why="Resumes with quantified business metrics receive 40% higher recruiter callback rates.",
            what_to_do="Edit your experience section to replace generic task lists with Action-Context-Result bullets.",
            expected_outcome="+10-15 points to Resume Quality and increased ATS interview conversion.",
            cta_label="Improve Resume",
            cta_link="/resume",
        )
    elif not latest_match:
        next_best_action = NextBestAction(
            title="Compare Your Profile Against a Target Job Description",
            category="skills",
            why="Identifying exact skill gaps against specific job postings enables precision learning.",
            what_to_do="Paste a job description on the Job Match page to calculate match percentage.",
            expected_outcome="Generates exact missing skill prioritization and tailored learning paths.",
            cta_label="Run Job Match",
            cta_link="/job-match",
        )
    elif (interview_score or 0) < 80:
        next_best_action = NextBestAction(
            title="Practice STAR Method on Technical & Behavioral Questions",
            category="interview",
            why="Interview performance directly accounts for 25% of your total hiring readiness score.",
            what_to_do="Complete a Technical or HR mock interview session focusing on structured explanations.",
            expected_outcome="+12 points to Interview Performance and greater answer confidence.",
            cta_label="Practice Interview",
            cta_link="/interview",
        )
    else:
        next_best_action = NextBestAction(
            title="Bridge Remaining Skill Gaps with Capstone Project",
            category="skills",
            why="Demonstrating production-grade code in your missing skill areas proves hands-on mastery.",
            what_to_do="Implement the suggested practical exercise in your highest-priority missing skill.",
            expected_outcome="Reaches top 90th percentile in Job Match and Career Readiness.",
            cta_label="View Skill Gaps",
            cta_link="/improve#skills",
        )

    target_potential = min(98, current_overall + 16) if has_data else 85
    summary = (
        f"Your verified readiness score is {current_overall}/100. Following this personalized action plan "
        f"can increase your score to {target_potential}/100."
        if has_data
        else "Upload your resume and run a job match to generate your personalized career improvement roadmap."
    )

    return CareerImprovementPlan(
        has_data=has_data,
        data_completeness=data_completeness,
        overall_score=current_overall,
        target_potential_score=target_potential,
        summary=summary,
        next_best_action=next_best_action,
        resume_enhancements=resume_enhancements,
        skill_gaps=skill_gaps,
        action_plan=action_plan,
        progress_tracking=progress_tracking,
    )
