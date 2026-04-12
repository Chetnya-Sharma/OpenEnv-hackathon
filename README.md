---
title: SQL Review Env
emoji: 🛢️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - sql
  - code-review
app_port: 7860
---

# SQL Review Environment

An OpenEnv-compliant environment for training and evaluating AI agents on real-world SQL query review tasks. Agents must identify security vulnerabilities, performance bottlenecks, and logic bugs in SQL queries — a task data engineers perform daily.

## Why SQL Review?

- **Real-world utility**: Data engineers review SQL queries every day before they hit production
- **Novel domain**: Not seen in existing OpenEnv submissions
- **Rich reward signals**: Multiple quality dimensions (correctness, security, performance, logic)
- **Naturally hard**: Requires multi-dimensional reasoning about code semantics
- **Immediately valuable**: Can train code-reviewing agents for production use

## Action Space

| Field | Type | Required | Valid Values | Description |
|-------|------|----------|-------------|-------------|
| `action_type` | string | Yes | `review`, `approve`, `reject`, `request_changes`, `skip` | Type of action to take |
| `query_id` | string | Yes | Any valid query ID | Target query identifier |
| `verdict` | string | No | `approve`, `reject` | Final verdict on the query |
| `issues_found` | array[string] | No | `sql_injection`, `performance`, `logic_bug`, `missing_index`, `n_plus_one`, `no_issues` | Issues identified in the query |
| `suggested_fix` | string | No | Any SQL string | Suggested rewrite for problematic queries |
| `confidence` | float | No | 0.0 - 1.0 | Agent's confidence in its assessment |

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `queries` | array[SQLQuery] | List of SQL queries to review (ground truth hidden) |
| `current_step` | integer | Current step number in the episode |
| `task_id` | string | Active task identifier |
| `reviewed_count` | integer | Number of queries already reviewed |
| `pending_count` | integer | Number of queries remaining |
| `last_action_result` | string | Result of the most recent action |
| `session_stats` | object | Running statistics (correct, wrong, skipped, total_reward) |
| `done` | boolean | Whether the episode has ended |

Each query in `queries` contains: `query_id`, `sql`, `submitted_by`, `database`, `query_type`, `is_urgent`

## Tasks

| Task ID | Difficulty | Max Steps | Objective | Scoring |
|---------|-----------|-----------|-----------|---------|
| `single_review` | Easy | 5 | Review 1 SQL query for issues | 60% verdict accuracy + 40% issue detection |
| `batch_review` | Medium | 25 | Review 8 mixed SQL queries | 50% verdict + 30% issue detection + 20% fix quality |
| `pipeline_review` | Hard | 50 | Review 15 queries in 3 batches with priority handling | 35% verdict + 25% issues + 20% fixes + 20% priority |

### Task Details

**single_review** (Easy): Agent receives 1 SQL query and must identify issues, give a verdict, and optionally suggest a fix. Dense rewards for correct verdicts (+0.30), correct issue identification (+0.15 each), and quality fixes (+0.10).

**batch_review** (Medium): Agent receives 8 queries of mixed types (safe, injection, performance, logic bugs). Must efficiently review all within the step budget. Penalties for skipping (-0.10) and repeated reviews (-0.05). Completion bonus (+0.15) for reviewing all queries within budget.

**pipeline_review** (Hard): Agent reviews 15 queries arriving in 3 batches of 5. Some queries are marked urgent and must be prioritized. Heavy penalties for approving urgent queries with critical issues (-0.20), skipping queries (-0.10), and empty fixes on rejections (-0.15).

## Setup

### Docker Build & Run

```bash
docker build -t sql-review-env .
docker run -p 7860:7860 sql-review-env
```

### Local Development

```bash
pip install -r requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 7860
```

## API Usage

### Health Check
```bash
curl http://localhost:7860/health
# {"status":"ok","version":"1.0.0"}
```

### Reset Environment
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "single_review"}'
```

### Take a Step
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "review",
    "query_id": "inj-001",
    "verdict": "reject",
    "issues_found": ["sql_injection"],
    "suggested_fix": "Use parameterized queries: SELECT * FROM users WHERE username = ? AND password = ?",
    "confidence": 0.95
  }'
```

### Get Full State (includes ground truth)
```bash
curl http://localhost:7860/state
```

### List Tasks
```bash
curl -X POST http://localhost:7860/tasks
```

## Baseline Scores

| Task | Score | Steps | Notes |
|------|-------|-------|-------|
| `single_review` | ~0.87 | 1-2 | Most LLMs detect obvious issues |
| `batch_review` | ~0.85 | 8-15 | Requires consistent multi-query review |
| `pipeline_review` | ~0.83 | 15-30 | Priority handling and fix quality are challenging |

## Running the Baseline Inference

```bash
export HF_TOKEN="your-huggingface-token"
export ENV_BASE_URL="http://localhost:7860"
python inference.py
```

## Validation

```bash
openenv validate
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | LLM API endpoint | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | Model identifier for inference | `Qwen/Qwen2.5-72B-Instruct` |
| `HF_TOKEN` | HuggingFace API token | Required for inference |
| `ENV_BASE_URL` | Environment server URL | `http://localhost:7860` |

## Query Categories

The environment generates 56 unique SQL queries across these categories:

- **Safe queries** (15): Well-written, parameterized, efficient SQL that should be approved
- **Injection queries** (12): String concatenation, UNION attacks, comment bypasses
- **Performance queries** (12): SELECT *, function on indexed columns, cartesian products, N+1 patterns
- **Logic bug queries** (12): DELETE without WHERE, impossible conditions, wrong data types
- **Multi-issue queries** (5): Combinations of injection + performance, injection + logic bugs, etc.

## License

MIT
