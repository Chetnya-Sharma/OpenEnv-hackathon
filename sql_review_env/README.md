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
  - security
app_port: 7860
---

# SQL Review Environment

An OpenEnv-compliant environment for training and evaluating AI agents on real-world SQL query review tasks. Agents must identify security vulnerabilities, performance bottlenecks, and logic bugs in SQL queries — a task data engineers perform daily in production.

## Why SQL Review?

- **Real-world impact**: SQL injection remains the #1 web application vulnerability (OWASP Top 10). The average cost of a data breach involving injection is $4.45M (IBM, 2023).
- **Multi-dimensional reasoning**: Agents evaluate security, performance, and correctness simultaneously — the same multi-axis analysis human reviewers perform.
- **Adversarial challenge**: Includes tricky queries designed to fool LLMs — parameterized queries with misleading comments, string literals containing SQL keywords, and subtle bugs that pass superficial review.
- **Information-gathering tradeoff**: In medium/hard tasks, agents must decide whether to spend steps requesting schema and context information or review directly — creating a genuine exploration vs exploitation dynamic.
- **Dense reward signals**: Every action gets immediate feedback across multiple quality dimensions.
- **RL-ready**: Compatible with TRL's GRPOTrainer via the standard rollout_func interface.

## Action Space

| Field | Type | Required | Valid Values | Description |
|-------|------|----------|-------------|-------------|
| `action_type` | string | Yes | `review`, `approve`, `reject`, `request_changes`, `skip`, `request_schema`, `request_context` | Type of action |
| `query_id` | string | Yes | Any valid query ID | Target query identifier |
| `verdict` | string | No | `approve`, `reject` | Final verdict |
| `issues_found` | array | No | `sql_injection`, `performance`, `logic_bug`, `missing_index`, `n_plus_one`, `no_issues` | Issues identified |
| `reasoning` | string | No | Any text | Agent's explanation for its decision |
| `suggested_fix` | string | No | Any SQL string | Suggested rewrite |
| `confidence` | float | No | 0.0 - 1.0 | Agent's confidence |

### Information-Gathering Actions
- `request_schema(query_id)` — Reveals table schema (costs 1 step)
- `request_context(query_id)` — Reveals production context (costs 1 step)

In easy mode, context and schema are shown automatically. In medium/hard, the agent must decide whether to spend steps gathering information.

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `queries` | array[SQLQuery] | SQL queries with `context` and `schema_hint` (may be empty until requested) |
| `current_step` | integer | Current step number |
| `task_id` | string | Active task identifier |
| `reviewed_count` | integer | Queries already reviewed |
| `pending_count` | integer | Queries remaining |
| `last_action_result` | string | Result of most recent action |
| `session_stats` | object | Running statistics |
| `review_history` | array | Previous reviews this episode |
| `done` | boolean | Whether episode has ended |

## Tasks

| Task ID | Difficulty | Steps | Queries | Key Scoring |
|---------|-----------|-------|---------|-------------|
| `single_review` | Easy | 5 | 1 | 50% verdict + 30% issues + 10% reasoning + 10% fix |
| `batch_review` | Medium | 25 | 8 | 40% verdict + 25% issues + 10% reasoning + 15% fix + 10% efficiency |
| `pipeline_review` | Hard | 50 | 15 | 30% verdict + 20% issues + 10% reasoning + 15% fix + 15% priority + 10% efficiency - penalties |

## Query Categories (62 total)

- **Safe queries** (15): Parameterized, efficient, well-structured
- **Injection queries** (12): f-string interpolation, string concatenation, dynamic SQL
- **Performance queries** (12): SELECT *, functions on indexed columns, cartesian products, N+1 patterns
- **Logic bug queries** (12): DELETE without WHERE, race conditions, impossible conditions, mass updates
- **Multi-issue queries** (5): Injection + performance, injection + logic bugs, etc.
- **Adversarial queries** (6): Safe queries that look dangerous, and dangerous queries that look safe

## Setup

```bash
# Docker
docker build -t sql-review-env .
docker run -p 7860:7860 sql-review-env

# Local
pip install -r requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 7860
```

## API Usage

```bash
# Health check
curl http://localhost:7860/health

# Reset
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d '{"task_id": "single_review"}'

# Review a query
curl -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{
  "action_type": "review", "query_id": "inj-001", "verdict": "reject",
  "issues_found": ["sql_injection"],
  "reasoning": "Uses f-string interpolation for username/password_hash. Should use parameterized queries.",
  "suggested_fix": "SELECT id, name, email FROM users WHERE username = $1 AND password_hash = $2;",
  "confidence": 0.95
}'

# Request schema (costs 1 step, medium/hard tasks)
curl -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type": "request_schema", "query_id": "inj-001"}'

# Full state (includes ground truth)
curl http://localhost:7860/state

# List tasks
curl -X POST http://localhost:7860/tasks
```

## Running the Baseline Inference

```bash
export HF_TOKEN="your-huggingface-token"
export ENV_BASE_URL="http://localhost:7860"
python inference.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | LLM API endpoint | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | Model identifier | `Qwen/Qwen2.5-72B-Instruct` |
| `HF_TOKEN` | HuggingFace API token | Required |
| `ENV_BASE_URL` | Environment server URL | `http://localhost:7860` |

## License

MIT
