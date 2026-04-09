# Job Seeker Agent

## Pattern: Plan-and-Execute with Application Pipeline

This agent uses the **Plan-and-Execute** pattern (like `agent_planner.py`) specialized for job searching and application automation. It demonstrates how to build a multi-tool pipeline that could connect to real job boards.

## What It Does

| Capability | How |
|---|---|
| Search jobs | Keyword, location, and experience-level filtering |
| Evaluate fit | Score resume against job postings (keyword + skills match) |
| Generate cover letters | AI-tailored cover letters per job posting |
| Track applications | Full pipeline: saved → applied → interview → offer/rejected |
| Add job postings | Manually add jobs found on LinkedIn/Indeed to the local DB |
| Interactive browsing | Quick-command mode for exploring jobs without full planning |

## Architecture

```
User Task
    │
    ▼
┌──────────────────────┐
│  Phase 1: PLANNING    │──► LLM creates a step-by-step strategy
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Phase 2: EXECUTION   │──► For each step:
│  (step-by-step loop)  │     LLM uses tools → mark_step_done
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────────────┐
│  Tools:               │     │  Data Storage:           │
│  • search_jobs        │     │  .job_search/            │
│  • get_job_details    │     │    jobs_database.json    │
│  • score_job_fit      │     │    applications.json     │
│  • generate_cover_letter│   │    cover_letters/        │
│  • track_application  │     └─────────────────────────┘
│  • view_pipeline      │
│  • read_file          │
│  • add_job            │
└──────────────────────┘
```

## Tools

| Tool | Purpose |
|---|---|
| `search_jobs` | Search local job DB by keywords, location, experience level |
| `get_job_details` | Full details of a specific job posting |
| `score_job_fit` | Keyword + skills match scoring (resume vs. job) |
| `generate_cover_letter` | LLM-generated tailored cover letter (saved to disk) |
| `track_application` | Create/update application status in the tracker |
| `view_pipeline` | View all applications grouped by status |
| `read_file` | Read resume, cover letter, or other files |
| `add_job` | Add a new job posting to the local database |

## Usage Examples

```bash
# Interactive mode — browse and manage jobs manually
python agent_job_seeker.py
python agent_job_seeker.py --interactive --resume-file my_resume.md

# Plan-and-execute mode — give it a task
python agent_job_seeker.py --task "Find remote Python developer jobs"
python agent_job_seeker.py --task "Score my fit for JOB-001 and JOB-003" --resume-file resume.md
python agent_job_seeker.py --task "Apply to JOB-003 with a cover letter" --resume-file resume.md
python agent_job_seeker.py --task "Show my application pipeline status"

# Verbose mode
python agent_job_seeker.py --task "Find ML engineer roles" --verbose
```

## Interactive Commands

| Command | Action |
|---|---|
| `search <keywords>` | Search the job database |
| `details <job-id>` | View full job details |
| `score <job-id>` | Score resume fit (needs `--resume-file`) |
| `apply <job-id>` | Score + cover letter + track application |
| `pipeline` | View application pipeline |
| `add` | Manually add a job posting |
| `exit` | Quit |

## Sample Job Database

The agent ships with 6 sample jobs for demonstration:

| ID | Title | Company | Location |
|---|---|---|---|
| JOB-001 | Senior Python Developer | TechCorp Inc. | Remote |
| JOB-002 | Full Stack Engineer | StartupXYZ | San Francisco (Hybrid) |
| JOB-003 | Machine Learning Engineer | AI Solutions Ltd. | Remote (US) |
| JOB-004 | DevOps Engineer | CloudFirst Systems | Austin, TX |
| JOB-005 | Data Analyst | DataDriven Corp. | New York (Hybrid) |
| JOB-006 | Frontend Developer | DesignHub Agency | Remote |

Add your own jobs with the `add_job` tool or the `add` interactive command.

## Application Pipeline Statuses

```
saved → applied → interview → offer
                           ↘ rejected
                 ↘ withdrawn
```

Each transition is timestamped and logged in the application history.

## Key Learning Points

1. **Plan-and-Execute for pipelines**: Job searching is a natural fit for this pattern — search, evaluate, apply is inherently sequential with clear steps.

2. **Local database as API mock**: The JSON-based job database demonstrates the adapter pattern. In production, swap `search_jobs()` with API calls to Indeed/LinkedIn.

3. **LLM + deterministic tools**: `score_job_fit` uses keyword matching (deterministic), while `generate_cover_letter` calls the LLM. Mixing AI and non-AI tools is a common agent pattern.

4. **Dual modes**: The agent supports both automated (plan-and-execute) and manual (interactive) modes, showing how to build flexible agent interfaces.

5. **State management**: Applications are tracked in a persistent JSON file with status history, demonstrating how agents can maintain long-running state.

## Connecting to Real Job APIs

To connect to real job boards, replace the `search_jobs` function:

```python
# Example: Indeed API adapter (pseudo-code)
def search_jobs_indeed(keywords: str, location: str = "") -> str:
    response = requests.get(
        "https://api.indeed.com/v2/search",
        params={"q": keywords, "l": location, "api_key": os.getenv("INDEED_API_KEY")},
    )
    jobs = response.json()["results"]
    # Transform to our schema and save to local DB
    for job in jobs:
        add_job(title=job["title"], company=job["company"], ...)
    return json.dumps(jobs, indent=2)
```

Similarly for LinkedIn (requires OAuth 2.0) or other job board APIs.

## Data Files

All data is stored in `.job_search/`:
- `jobs_database.json` — All job postings (sample + user-added)
- `applications.json` — Application tracker with status history
- `cover_letters/` — Generated cover letters (one per job)
