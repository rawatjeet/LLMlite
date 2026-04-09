"""
Job Seeker Agent (Plan-and-Execute with Application Pipeline)

An automated job-seeking agent that searches for jobs, evaluates fit, generates
tailored cover letters, and manages an application tracking pipeline. Uses the
Plan-and-Execute pattern:

  Phase 1 (Plan)    -> LLM creates a search-and-apply strategy
  Phase 2 (Execute) -> LLM works through each step using tools

The agent manages a local JSON-based "job board" and application tracker,
demonstrating how to build automation pipelines that could connect to real
job APIs (Indeed, LinkedIn, etc.) via adapter functions.

Features:
  - Search jobs by keywords, location, experience level (local DB + simulated)
  - Score job-resume fit using keyword analysis
  - Generate tailored cover letters for specific postings
  - Track application status (saved -> applied -> interview -> offer -> rejected)
  - Maintain a persistent job search database

Usage:
    python agent_job_seeker.py
    python agent_job_seeker.py --task "Find Python developer jobs in remote positions"
    python agent_job_seeker.py --task "Apply to job JOB-003 with my resume" --resume-file resume.md
    python agent_job_seeker.py --task "Show my application pipeline status"
    python agent_job_seeker.py --verbose
"""

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError(
        "Missing dependency: python-dotenv\n"
        "Install it by running: pip install -r requirements.txt"
    )

import os
import json
import sys
import re
import argparse
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
JOBS_DB_PATH = Path(os.getenv("JOBS_DB_PATH", ".job_search/jobs_database.json"))
APPLICATIONS_PATH = Path(os.getenv("APPLICATIONS_PATH", ".job_search/applications.json"))
COVER_LETTERS_DIR = Path(os.getenv("COVER_LETTERS_DIR", ".job_search/cover_letters"))


# ---------------------------------------------------------------------------
# Job database and application tracker
# ---------------------------------------------------------------------------

def _ensure_dirs() -> None:
    JOBS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    COVER_LETTERS_DIR.mkdir(parents=True, exist_ok=True)


def _load_jobs_db() -> List[Dict]:
    if JOBS_DB_PATH.exists():
        return json.loads(JOBS_DB_PATH.read_text(encoding="utf-8"))
    return _seed_sample_jobs()


def _save_jobs_db(jobs: List[Dict]) -> None:
    _ensure_dirs()
    JOBS_DB_PATH.write_text(json.dumps(jobs, indent=2), encoding="utf-8")


def _load_applications() -> List[Dict]:
    if APPLICATIONS_PATH.exists():
        return json.loads(APPLICATIONS_PATH.read_text(encoding="utf-8"))
    return []


def _save_applications(apps: List[Dict]) -> None:
    _ensure_dirs()
    APPLICATIONS_PATH.write_text(json.dumps(apps, indent=2), encoding="utf-8")


def _seed_sample_jobs() -> List[Dict]:
    """Seed the database with sample job listings for demonstration."""
    sample_jobs = [
        {
            "id": "JOB-001",
            "title": "Senior Python Developer",
            "company": "TechCorp Inc.",
            "location": "Remote",
            "salary_range": "$120,000 - $160,000",
            "experience_level": "Senior",
            "posted_date": "2026-04-01",
            "source": "linkedin",
            "url": "https://example.com/jobs/001",
            "description": (
                "We are looking for a Senior Python Developer to join our backend team. "
                "You will design and build scalable microservices using Python, FastAPI, and PostgreSQL. "
                "Requirements: 5+ years Python experience, REST API design, Docker, Kubernetes, "
                "CI/CD pipelines, AWS or GCP. Strong knowledge of SQL databases, Redis caching, "
                "and message queues (RabbitMQ/Kafka). Experience with agile methodologies and "
                "test-driven development. Nice to have: Machine learning experience, GraphQL."
            ),
            "skills_required": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "AWS", "CI/CD"],
        },
        {
            "id": "JOB-002",
            "title": "Full Stack Engineer",
            "company": "StartupXYZ",
            "location": "San Francisco, CA (Hybrid)",
            "salary_range": "$130,000 - $170,000",
            "experience_level": "Mid-Senior",
            "posted_date": "2026-04-03",
            "source": "indeed",
            "url": "https://example.com/jobs/002",
            "description": (
                "Join our fast-growing startup as a Full Stack Engineer. Build features end-to-end "
                "using React, TypeScript, Node.js, and Python. Work with our AI/ML team to integrate "
                "intelligent features. Requirements: 3+ years full stack, React/TypeScript, Python, "
                "REST APIs, SQL and NoSQL databases, Git. Bonus: LLM/AI integration, startup experience."
            ),
            "skills_required": ["React", "TypeScript", "Node.js", "Python", "SQL", "NoSQL", "Git"],
        },
        {
            "id": "JOB-003",
            "title": "Machine Learning Engineer",
            "company": "AI Solutions Ltd.",
            "location": "Remote (US)",
            "salary_range": "$140,000 - $190,000",
            "experience_level": "Mid-Senior",
            "posted_date": "2026-04-05",
            "source": "linkedin",
            "url": "https://example.com/jobs/003",
            "description": (
                "Design and deploy ML models at scale. Work on NLP, computer vision, and recommendation "
                "systems. Requirements: MS/PhD in CS or related field, 3+ years ML in production, "
                "Python, PyTorch or TensorFlow, scikit-learn, MLOps (MLflow, Kubeflow), "
                "cloud platforms (AWS SageMaker, GCP Vertex AI). Strong math/statistics background. "
                "Experience with LLMs, fine-tuning, and prompt engineering is a strong plus."
            ),
            "skills_required": ["Python", "PyTorch", "TensorFlow", "MLOps", "NLP", "AWS", "Statistics"],
        },
        {
            "id": "JOB-004",
            "title": "DevOps Engineer",
            "company": "CloudFirst Systems",
            "location": "Austin, TX (Remote OK)",
            "salary_range": "$115,000 - $150,000",
            "experience_level": "Mid",
            "posted_date": "2026-04-06",
            "source": "indeed",
            "url": "https://example.com/jobs/004",
            "description": (
                "Manage and optimize our cloud infrastructure. Build CI/CD pipelines, "
                "implement infrastructure as code, and ensure 99.9% uptime. "
                "Requirements: 3+ years DevOps/SRE, Terraform, Docker, Kubernetes, "
                "AWS (EC2, ECS, Lambda, RDS), monitoring (Datadog, Prometheus), "
                "scripting (Python, Bash), Linux administration. On-call rotation required."
            ),
            "skills_required": ["Terraform", "Docker", "Kubernetes", "AWS", "Python", "Bash", "Linux"],
        },
        {
            "id": "JOB-005",
            "title": "Data Analyst",
            "company": "DataDriven Corp.",
            "location": "New York, NY (Hybrid)",
            "salary_range": "$85,000 - $110,000",
            "experience_level": "Junior-Mid",
            "posted_date": "2026-04-07",
            "source": "linkedin",
            "url": "https://example.com/jobs/005",
            "description": (
                "Analyze business data and create actionable insights. Build dashboards, "
                "run A/B tests, and support product decisions with data. "
                "Requirements: SQL proficiency, Python (pandas, matplotlib), "
                "BI tools (Tableau or Power BI), statistics fundamentals, "
                "Excel/Google Sheets. Experience with data warehousing (Snowflake, BigQuery) preferred."
            ),
            "skills_required": ["SQL", "Python", "Tableau", "Statistics", "Excel", "Pandas"],
        },
        {
            "id": "JOB-006",
            "title": "Frontend Developer",
            "company": "DesignHub Agency",
            "location": "Remote",
            "salary_range": "$95,000 - $130,000",
            "experience_level": "Mid",
            "posted_date": "2026-04-04",
            "source": "indeed",
            "url": "https://example.com/jobs/006",
            "description": (
                "Build beautiful, responsive web interfaces for our agency clients. "
                "Work closely with designers to implement pixel-perfect UIs. "
                "Requirements: 3+ years frontend, React, TypeScript, CSS/Tailwind, "
                "responsive design, accessibility (WCAG), testing (Jest, Cypress). "
                "Portfolio of shipped products required."
            ),
            "skills_required": ["React", "TypeScript", "CSS", "Tailwind", "Jest", "Cypress"],
        },
    ]
    _save_jobs_db(sample_jobs)
    return sample_jobs


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def search_jobs(keywords: str, location: str = "", experience_level: str = "") -> str:
    """Search the job database by keywords, location, and experience level.

    Args:
        keywords: Space-separated search terms to match against title, description, skills.
        location: Filter by location (partial match).
        experience_level: Filter by level (Junior, Mid, Senior, etc.).

    Returns:
        JSON array of matching job summaries.
    """
    jobs = _load_jobs_db()
    kw_list = [w.lower() for w in keywords.split() if w]
    results = []

    for job in jobs:
        searchable = f"{job['title']} {job['description']} {' '.join(job.get('skills_required', []))}".lower()
        if kw_list and not any(kw in searchable for kw in kw_list):
            continue
        if location and location.lower() not in job.get("location", "").lower():
            continue
        if experience_level and experience_level.lower() not in job.get("experience_level", "").lower():
            continue

        results.append({
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "salary_range": job.get("salary_range", "Not listed"),
            "experience_level": job.get("experience_level", ""),
            "posted_date": job.get("posted_date", ""),
            "source": job.get("source", ""),
        })

    if not results:
        return "No jobs found matching your criteria. Try broader keywords."
    return json.dumps(results, indent=2)


def get_job_details(job_id: str) -> str:
    """Get full details of a specific job posting.

    Args:
        job_id: The job ID (e.g. 'JOB-001').

    Returns:
        Full job details as JSON, or error message.
    """
    jobs = _load_jobs_db()
    for job in jobs:
        if job["id"].upper() == job_id.upper():
            return json.dumps(job, indent=2)
    return f"Error: Job '{job_id}' not found."


def score_job_fit(job_id: str, resume_text: str) -> str:
    """Score how well a resume matches a specific job posting.

    Args:
        job_id: The job ID to score against.
        resume_text: The resume content to evaluate.

    Returns:
        JSON with fit score, matched/missing keywords, and recommendation.
    """
    jobs = _load_jobs_db()
    job = next((j for j in jobs if j["id"].upper() == job_id.upper()), None)
    if not job:
        return f"Error: Job '{job_id}' not found."

    jd_text = f"{job['description']} {' '.join(job.get('skills_required', []))}"
    jd_lower = jd_text.lower()
    resume_lower = resume_text.lower()

    jd_words = set(re.findall(r'\b[a-z]{3,}\b', jd_lower))
    resume_words = set(re.findall(r'\b[a-z]{3,}\b', resume_lower))

    stop_words = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can",
        "had", "her", "was", "one", "our", "out", "has", "have", "been",
        "will", "with", "this", "that", "from", "they", "were", "which",
        "their", "about", "would", "there", "should", "could",
    }
    jd_keywords = jd_words - stop_words
    matched = jd_keywords & resume_words
    missing = jd_keywords - resume_words

    required_skills = [s.lower() for s in job.get("skills_required", [])]
    skills_matched = [s for s in required_skills if s in resume_lower]
    skills_missing = [s for s in required_skills if s not in resume_lower]

    score = round(len(matched) / max(len(jd_keywords), 1) * 100, 1)
    skills_score = round(len(skills_matched) / max(len(required_skills), 1) * 100, 1)

    return json.dumps({
        "job_id": job["id"],
        "job_title": job["title"],
        "company": job["company"],
        "keyword_match_score": score,
        "skills_match_score": skills_score,
        "required_skills_matched": skills_matched,
        "required_skills_missing": skills_missing,
        "top_missing_keywords": sorted(missing)[:15],
        "recommendation": (
            "Strong match — apply with confidence!"
            if score >= 70 and skills_score >= 70
            else "Decent match — tailor resume to fill gaps before applying."
            if score >= 45 or skills_score >= 50
            else "Weak match — consider upskilling or targeting different roles."
        ),
    }, indent=2)


def generate_cover_letter(job_id: str, resume_text: str, tone: str = "professional") -> str:
    """Generate a tailored cover letter for a specific job using the LLM.

    Args:
        job_id: The job to write a cover letter for.
        resume_text: The applicant's resume text.
        tone: Writing tone — professional, enthusiastic, or concise.

    Returns:
        The generated cover letter text.
    """
    jobs = _load_jobs_db()
    job = next((j for j in jobs if j["id"].upper() == job_id.upper()), None)
    if not job:
        return f"Error: Job '{job_id}' not found."

    prompt = f"""Write a {tone} cover letter for this job posting.

JOB DETAILS:
- Title: {job['title']}
- Company: {job['company']}
- Description: {job['description']}
- Required Skills: {', '.join(job.get('skills_required', []))}

APPLICANT'S RESUME:
{resume_text[:3000]}

Write a compelling, personalized cover letter (300-400 words) that:
1. Opens with enthusiasm for the specific role and company
2. Highlights 2-3 relevant experiences from the resume that match the job
3. Addresses key requirements from the job description
4. Closes with a call to action

Output ONLY the cover letter text, no commentary."""

    try:
        resp = completion(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        letter = resp.choices[0].message.content.strip()

        out_file = COVER_LETTERS_DIR / f"cover_letter_{job_id.lower()}.md"
        _ensure_dirs()
        out_file.write_text(letter, encoding="utf-8")

        return f"{letter}\n\n---\nCover letter saved to: {out_file}"
    except Exception as e:
        return f"Error generating cover letter: {e}"


def track_application(job_id: str, status: str, notes: str = "") -> str:
    """Create or update a job application in the tracker.

    Args:
        job_id: The job ID being applied to.
        status: One of: saved, applied, interview, offer, rejected, withdrawn.
        notes: Optional notes about this application.

    Returns:
        Confirmation message.
    """
    valid_statuses = {"saved", "applied", "interview", "offer", "rejected", "withdrawn"}
    if status.lower() not in valid_statuses:
        return f"Error: Invalid status '{status}'. Use one of: {', '.join(sorted(valid_statuses))}"

    apps = _load_applications()
    jobs = _load_jobs_db()
    job = next((j for j in jobs if j["id"].upper() == job_id.upper()), None)

    existing = next((a for a in apps if a["job_id"].upper() == job_id.upper()), None)

    if existing:
        existing["status"] = status.lower()
        existing["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if notes:
            existing["notes"] = existing.get("notes", "") + f"\n[{time.strftime('%m/%d')}] {notes}"
        existing.setdefault("history", []).append({
            "status": status.lower(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        _save_applications(apps)
        return f"Updated application for {job_id}: status -> {status}"
    else:
        app = {
            "job_id": job_id.upper(),
            "job_title": job["title"] if job else "Unknown",
            "company": job["company"] if job else "Unknown",
            "status": status.lower(),
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "notes": notes,
            "history": [{"status": status.lower(), "date": time.strftime("%Y-%m-%d %H:%M:%S")}],
        }
        apps.append(app)
        _save_applications(apps)
        return f"Created application tracker for {job_id} ({app['job_title']} at {app['company']}): {status}"


def view_pipeline(status_filter: str = "") -> str:
    """View the application pipeline, optionally filtered by status.

    Args:
        status_filter: Optional status to filter by (saved, applied, interview, etc.).

    Returns:
        Formatted pipeline view.
    """
    apps = _load_applications()
    if not apps:
        return "No applications tracked yet. Use track_application to start tracking."

    if status_filter:
        apps = [a for a in apps if a["status"] == status_filter.lower()]
        if not apps:
            return f"No applications with status '{status_filter}'."

    pipeline: Dict[str, List] = {}
    for app in apps:
        status = app["status"]
        pipeline.setdefault(status, []).append(app)

    order = ["saved", "applied", "interview", "offer", "rejected", "withdrawn"]
    lines = ["APPLICATION PIPELINE", "=" * 50]

    for status in order:
        if status not in pipeline:
            continue
        lines.append(f"\n[{status.upper()}] ({len(pipeline[status])} applications)")
        lines.append("-" * 40)
        for app in pipeline[status]:
            lines.append(f"  {app['job_id']}: {app.get('job_title', '?')} @ {app.get('company', '?')}")
            lines.append(f"    Updated: {app.get('updated', '?')}")
            if app.get("notes"):
                lines.append(f"    Notes: {app['notes'][:100]}")

    total = sum(len(v) for v in pipeline.values())
    lines.append(f"\nTotal: {total} applications tracked")
    return "\n".join(lines)


def read_file(file_name: str) -> str:
    """Read a file from disk (resume, cover letter, etc.)."""
    try:
        p = Path(file_name)
        if not p.is_file():
            return f"Error: '{file_name}' not found."
        if p.stat().st_size > 100_000:
            return f"Error: File too large."
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error: {e}"


def add_job(title: str, company: str, location: str, description: str,
            salary_range: str = "", experience_level: str = "",
            url: str = "", source: str = "manual") -> str:
    """Add a new job posting to the local database.

    Args:
        title: Job title.
        company: Company name.
        location: Job location.
        description: Full job description.
        salary_range: Salary range if known.
        experience_level: Required experience level.
        url: Link to the original posting.
        source: Where the job was found.

    Returns:
        Confirmation with the new job ID.
    """
    jobs = _load_jobs_db()
    max_num = 0
    for j in jobs:
        match = re.search(r'JOB-(\d+)', j["id"])
        if match:
            max_num = max(max_num, int(match.group(1)))

    new_id = f"JOB-{max_num + 1:03d}"
    new_job = {
        "id": new_id,
        "title": title,
        "company": company,
        "location": location,
        "salary_range": salary_range,
        "experience_level": experience_level,
        "posted_date": time.strftime("%Y-%m-%d"),
        "source": source,
        "url": url,
        "description": description,
        "skills_required": [],
    }
    jobs.append(new_job)
    _save_jobs_db(jobs)
    return f"Added job {new_id}: {title} at {company}"


TOOL_FUNCTIONS: Dict[str, Callable] = {
    "search_jobs": search_jobs,
    "get_job_details": get_job_details,
    "score_job_fit": score_job_fit,
    "generate_cover_letter": generate_cover_letter,
    "track_application": track_application,
    "view_pipeline": view_pipeline,
    "read_file": read_file,
    "add_job": add_job,
}

TOOLS_SPEC: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": "Search the job database by keywords, location, and experience level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "Space-separated search terms"},
                    "location": {"type": "string", "description": "Location filter (partial match)"},
                    "experience_level": {"type": "string", "description": "Level filter: Junior, Mid, Senior"},
                },
                "required": ["keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_job_details",
            "description": "Get full details of a specific job posting by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "Job ID (e.g. 'JOB-001')"},
                },
                "required": ["job_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_job_fit",
            "description": (
                "Score how well a resume matches a specific job posting. "
                "Returns keyword match %, skills match %, and missing items."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "Job ID to score against"},
                    "resume_text": {"type": "string", "description": "Full resume text"},
                },
                "required": ["job_id", "resume_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_cover_letter",
            "description": (
                "Generate a tailored cover letter for a specific job using AI. "
                "Saves the letter to disk automatically."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "Job ID to write cover letter for"},
                    "resume_text": {"type": "string", "description": "Applicant's resume text"},
                    "tone": {
                        "type": "string",
                        "description": "Tone: professional, enthusiastic, or concise",
                    },
                },
                "required": ["job_id", "resume_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "track_application",
            "description": (
                "Create or update a job application in the tracker. "
                "Statuses: saved, applied, interview, offer, rejected, withdrawn."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "Job ID being applied to"},
                    "status": {
                        "type": "string",
                        "description": "Application status",
                        "enum": ["saved", "applied", "interview", "offer", "rejected", "withdrawn"],
                    },
                    "notes": {"type": "string", "description": "Optional notes about this application"},
                },
                "required": ["job_id", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_pipeline",
            "description": "View the full application pipeline grouped by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "description": "Optional: filter by status (saved, applied, interview, etc.)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from disk (resume, cover letter, job description, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "Path to the file to read"},
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_job",
            "description": (
                "Add a new job posting to the local database manually. "
                "Use when the user pastes a job they found on LinkedIn/Indeed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Job title"},
                    "company": {"type": "string", "description": "Company name"},
                    "location": {"type": "string", "description": "Job location"},
                    "description": {"type": "string", "description": "Full job description text"},
                    "salary_range": {"type": "string", "description": "Salary range if known"},
                    "experience_level": {"type": "string", "description": "Required experience level"},
                    "url": {"type": "string", "description": "Link to original posting"},
                    "source": {"type": "string", "description": "Where found: linkedin, indeed, manual, etc."},
                },
                "required": ["title", "company", "location", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mark_step_done",
            "description": "Mark the current plan step as done and provide a brief result summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "step_result": {"type": "string", "description": "What was accomplished"},
                },
                "required": ["step_result"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Declare the overall task complete and provide the final answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string", "description": "Comprehensive final answer"},
                },
                "required": ["answer"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Phase 1: Planning
# ---------------------------------------------------------------------------

PLAN_SYSTEM_PROMPT = """You are a job search strategist. Given a user's task, create a \
clear numbered plan for their job search activities.

Available tools: search_jobs, get_job_details, score_job_fit, generate_cover_letter, \
track_application, view_pipeline, read_file, add_job.

Rules:
1. Break the task into 3-8 concrete, actionable steps.
2. Each step should use one or more of the available tools.
3. If the user wants to apply, always score fit before generating a cover letter.
4. The last step should summarize findings or confirm actions taken.
5. Output ONLY a JSON array of step strings. No commentary.

Example plans:
- Search task: ["Search for matching jobs", "Get details of top matches", \
"Score resume fit for each", "Summarize results with recommendations"]
- Apply task: ["Read the user's resume", "Get job details", "Score resume-job fit", \
"Generate tailored cover letter", "Track application as applied", "Confirm actions"]
"""


def generate_plan(task: str, model: str, verbose: bool = False) -> List[str]:
    """Ask the LLM to produce a step-by-step job search plan."""
    messages = [
        {"role": "system", "content": PLAN_SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    resp = completion(model=model, messages=messages, max_tokens=1024)
    raw = resp.choices[0].message.content.strip()

    if verbose:
        print(f"[Plan raw]\n{raw}\n")

    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        plan = json.loads(raw)
        if isinstance(plan, list) and all(isinstance(s, str) for s in plan):
            return plan
    except json.JSONDecodeError:
        pass

    steps = re.findall(r"\d+[.)]\s*(.+)", raw)
    return steps if steps else [f"Complete the task: {task}"]


# ---------------------------------------------------------------------------
# Phase 2: Execution
# ---------------------------------------------------------------------------

EXECUTE_SYSTEM_PROMPT = """You are a job search execution agent working through a plan.

Available tools (via function calling):
- search_jobs: Search by keywords, location, experience level
- get_job_details: Full details of a specific job
- score_job_fit: Score resume against a job posting
- generate_cover_letter: AI-generated tailored cover letter
- track_application: Track application status
- view_pipeline: View all tracked applications
- read_file: Read resume or other files
- add_job: Add a new job posting to the database
- mark_step_done: Mark current step complete
- finish: Declare the whole task done

Current plan (steps marked [DONE] are completed):
{plan_display}

Currently working on: Step {current_step}
"{step_description}"

Previous step results:
{step_results}

Use tools to accomplish this step, then call mark_step_done with what you found/did.
If all steps are complete, call finish with a comprehensive summary.
"""


def execute_step(
    step_idx: int,
    steps: List[str],
    step_results: List[str],
    memory: List[Dict],
    model: str,
    verbose: bool = False,
    max_tool_calls: int = 12,
) -> Optional[str]:
    """Execute a single plan step. Returns result, or None if agent called finish."""
    plan_display = ""
    for i, s in enumerate(steps):
        prefix = "[DONE]" if i < step_idx else "[TODO]" if i > step_idx else "[>>>]"
        plan_display += f"  {prefix} {i + 1}. {s}\n"

    results_display = ""
    for i, r in enumerate(step_results):
        results_display += f"  Step {i + 1}: {r}\n"
    if not results_display:
        results_display = "  (none yet)\n"

    system_content = EXECUTE_SYSTEM_PROMPT.format(
        plan_display=plan_display,
        current_step=step_idx + 1,
        step_description=steps[step_idx],
        step_results=results_display,
    )

    messages = [{"role": "system", "content": system_content}] + memory

    for call_num in range(max_tool_calls):
        resp = completion(model=model, messages=messages, tools=TOOLS_SPEC, max_tokens=DEFAULT_MAX_TOKENS)

        if not resp.choices[0].message.tool_calls:
            text = resp.choices[0].message.content or ""
            if verbose:
                print(f"  [Text response]: {text[:300]}")
            messages.append({"role": "assistant", "content": text})
            continue

        tool_call = resp.choices[0].message.tool_calls[0]
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        if verbose:
            print(f"  [Tool call #{call_num + 1}]: {fn_name}({json.dumps(fn_args)[:200]})")

        if fn_name == "finish":
            return None

        if fn_name == "mark_step_done":
            return fn_args.get("step_result", "Step completed.")

        if fn_name in TOOL_FUNCTIONS:
            try:
                result = TOOL_FUNCTIONS[fn_name](**fn_args)
            except Exception as e:
                result = f"Error: {e}"
        else:
            result = f"Unknown tool: {fn_name}"

        display = result[:500] + "..." if len(result) > 500 else result
        print(f"    -> {fn_name}: {display}")

        action_summary = json.dumps({"tool": fn_name, "args": fn_args})
        messages.append({"role": "assistant", "content": action_summary})
        messages.append({"role": "user", "content": f"Tool result:\n{result}"})

    return "Step reached max tool calls without completing."


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_job_seeker(
    task: str,
    model: str = DEFAULT_MODEL,
    resume_file: Optional[str] = None,
    verbose: bool = False,
) -> str:
    """Run the job seeker agent with plan-and-execute strategy."""
    print("\n" + "=" * 70)
    print("  JOB SEEKER AGENT")
    print("=" * 70)
    print(f"Task : {task}")
    print(f"Model: {model}")
    print(f"Jobs : {JOBS_DB_PATH}")
    print(f"Apps : {APPLICATIONS_PATH}")
    if resume_file:
        print(f"Resume: {resume_file}")
    print()

    full_task = task
    if resume_file:
        content = read_file(resume_file)
        if not content.startswith("Error"):
            full_task += f"\n\nMy resume:\n{content}"
        else:
            print(f"Warning: Could not read resume file: {content}")

    # Phase 1: Plan
    print("Phase 1: PLANNING")
    print("-" * 40)
    steps = generate_plan(full_task, model, verbose)
    for i, step in enumerate(steps):
        print(f"  {i + 1}. {step}")
    print()

    # Phase 2: Execute
    print("Phase 2: EXECUTION")
    print("-" * 40)

    step_results: List[str] = []
    memory: List[Dict] = [{"role": "user", "content": full_task}]
    final_answer = None

    for idx, step in enumerate(steps):
        print(f"\n>> Step {idx + 1}/{len(steps)}: {step}")

        result = execute_step(
            step_idx=idx,
            steps=steps,
            step_results=step_results,
            memory=memory,
            model=model,
            verbose=verbose,
        )

        if result is None:
            final_answer = step_results[-1] if step_results else "Task completed."
            break

        step_results.append(result)
        print(f"   Result: {result[:400]}")
        memory.append({"role": "assistant", "content": f"Completed step {idx + 1}: {result}"})

    if final_answer is None:
        print("\n>> Synthesizing final summary...")
        synthesis = (
            f"All steps done. Results:\n\n"
            + "\n".join(f"Step {i+1}: {r}" for i, r in enumerate(step_results))
            + f"\n\nOriginal task: {task}\n\n"
            "Provide a comprehensive summary of what was found and done."
        )
        resp = completion(
            model=model,
            messages=[{"role": "user", "content": synthesis}],
            max_tokens=DEFAULT_MAX_TOKENS,
        )
        final_answer = resp.choices[0].message.content.strip()

    print(f"\n{'=' * 70}")
    print("  TASK COMPLETE")
    print(f"{'=' * 70}")
    print(f"\n{final_answer}\n")
    return final_answer


# ---------------------------------------------------------------------------
# Interactive mode (for browsing jobs + manual actions)
# ---------------------------------------------------------------------------

def interactive_mode(model: str = DEFAULT_MODEL, resume_file: Optional[str] = None, verbose: bool = False) -> None:
    """Run an interactive job search session."""
    print("\n" + "=" * 70)
    print("  JOB SEEKER AGENT — Interactive Mode")
    print("=" * 70)
    print("\nCommands:")
    print("  search <keywords>      — Search for jobs")
    print("  details <job-id>       — View full job details")
    print("  score <job-id>         — Score resume fit (needs --resume-file)")
    print("  apply <job-id>         — Generate cover letter + track application")
    print("  pipeline               — View application pipeline")
    print("  add                    — Add a job posting manually")
    print("  <any other text>       — Run as a task with the plan-and-execute agent")
    print("  exit                   — Quit")
    print("=" * 70 + "\n")

    resume_text = ""
    if resume_file:
        resume_text = read_file(resume_file)
        if resume_text.startswith("Error"):
            print(f"Warning: {resume_text}")
            resume_text = ""
        else:
            print(f"Resume loaded: {resume_file} ({len(resume_text)} chars)\n")

    while True:
        try:
            user_input = input("job> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break

        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "search":
            kw = arg or input("  Keywords: ").strip()
            print(search_jobs(kw))
        elif cmd == "details":
            jid = arg or input("  Job ID: ").strip()
            print(get_job_details(jid))
        elif cmd == "score":
            if not resume_text:
                print("  No resume loaded. Use --resume-file or paste resume text.")
                continue
            jid = arg or input("  Job ID: ").strip()
            print(score_job_fit(jid, resume_text))
        elif cmd == "apply":
            jid = arg or input("  Job ID: ").strip()
            if not resume_text:
                print("  No resume loaded. Use --resume-file.")
                continue
            print("  Scoring fit...")
            print(score_job_fit(jid, resume_text))
            print("\n  Generating cover letter...")
            print(generate_cover_letter(jid, resume_text))
            print(track_application(jid, "applied", "Applied via job seeker agent"))
        elif cmd == "pipeline":
            print(view_pipeline(arg))
        elif cmd == "add":
            title = input("  Title: ").strip()
            company = input("  Company: ").strip()
            location = input("  Location: ").strip()
            print("  Description (end with blank line):")
            desc_lines = []
            while True:
                line = input()
                if not line:
                    break
                desc_lines.append(line)
            desc = "\n".join(desc_lines)
            print(add_job(title, company, location, desc))
        else:
            run_job_seeker(user_input, model, resume_file, verbose)
        print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Job Seeker Agent — search, evaluate, and apply to jobs with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_job_seeker.py
  python agent_job_seeker.py --task "Find remote Python developer jobs"
  python agent_job_seeker.py --task "Score my fit for JOB-001" --resume-file resume.md
  python agent_job_seeker.py --task "Apply to JOB-003" --resume-file resume.md
  python agent_job_seeker.py --task "Show my application pipeline"
  python agent_job_seeker.py --interactive --resume-file resume.md
  python agent_job_seeker.py --verbose

Pattern explained:
  This agent uses Plan-and-Execute for structured tasks (searching, applying)
  and offers an interactive mode for quick lookups. It maintains a local job
  database and application tracker in .job_search/.

  The sample job database demonstrates the pattern — in production, swap
  search_jobs() with API calls to Indeed, LinkedIn, or other job boards.
""",
    )
    parser.add_argument("--task", type=str, help="Task for the agent (triggers plan-and-execute)")
    parser.add_argument("--resume-file", type=str, help="Path to your resume file (.md, .txt)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive browse mode")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in .env")
        return 1

    _ensure_dirs()

    try:
        if args.interactive or (not args.task):
            interactive_mode(args.model, args.resume_file, args.verbose)
        else:
            run_job_seeker(
                task=args.task,
                model=args.model,
                resume_file=args.resume_file,
                verbose=args.verbose,
            )
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
    except Exception as e:
        print(f"\nFailed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
