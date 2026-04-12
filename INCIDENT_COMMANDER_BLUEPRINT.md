# Incident Commander — Project Blueprint

> **Team:** Alpha Pair (Rana + Chetnya)  
> **Hackathon:** OpenEnv Round 1  
> **Deadline:** 8 April 2025, 11:59 PM  
> **HF Space:** Ranakun-7/SQL-Review-ENV (will be updated)  
> **Branch:** `incident-commander` (to be created)

---

## Table of Contents

1. [What's Already Done](#1-whats-already-done)
2. [Why We're Pivoting](#2-why-were-pivoting)
3. [What We're Building](#3-what-were-building)
4. [How It Works — The Full Picture](#4-how-it-works--the-full-picture)
5. [What Stays vs. What Changes](#5-what-stays-vs-what-changes)
6. [Detailed File-by-File Plan](#6-detailed-file-by-file-plan)
7. [The 12 Incident Scenarios](#7-the-12-incident-scenarios)
8. [The 3 Tasks & How They're Graded](#8-the-3-tasks--how-theyre-graded)
9. [Reward Design — Step by Step](#9-reward-design--step-by-step)
10. [Inference Script Strategy](#10-inference-script-strategy)
11. [Implementation Order & Timeline](#11-implementation-order--timeline)
12. [Testing & Validation Checklist](#12-testing--validation-checklist)
13. [Deployment Steps](#13-deployment-steps)
14. [Risk Register](#14-risk-register)

---

## 1. What's Already Done

We have a **fully working, deployed** SQL Review Environment:

### Current Codebase (`sql_review_env/`)

```
sql_review_env/
├── server/
│   ├── __init__.py          # Empty init
│   ├── main.py              # FastAPI app — 5 endpoints (health, reset, step, state, tasks)
│   ├── env.py               # SQLReviewEnv class — reset()/step()/state() interface
│   ├── models.py            # Pydantic v2 models — SQLQuery, SQLAction, SQLObservation, SQLReward
│   ├── tasks.py             # 3 task definitions + 3 step reward functions + 3 final graders
│   └── data.py              # 56 synthetic SQL queries across 5 categories, seeded random
├── openenv.yaml             # OpenEnv spec file — action/observation schemas, task list
├── Dockerfile               # python:3.11-slim, uvicorn on port 7860, healthcheck
├── inference.py             # Baseline agent — OpenAI client, [START]/[STEP]/[END] logs
├── requirements.txt         # fastapi, uvicorn, pydantic, openai, httpx, python-dotenv
└── README.md                # Full docs with HF frontmatter
```

### What Works Today
- `/health` returns 200
- `/reset` with `task_id` loads queries, returns observation
- `/step` with action returns (observation, reward, done, info)
- `/state` returns full internal state with ground truth
- `/tasks` returns 3 task definitions
- Dockerfile builds and runs
- inference.py runs all 3 tasks with correct log format
- Deployed to HuggingFace Spaces
- Deterministic grading (seed=42, no randomness)

### Current Tasks
| Task ID | Difficulty | What Agent Does |
|---------|-----------|-----------------|
| `single_review` | Easy | Review 1 SQL query, 5 steps |
| `batch_review` | Medium | Review 8 queries, 25 steps |
| `pipeline_review` | Hard | Review 15 queries in batches, 50 steps |

### Estimated Rubric Score: ~72/100
Solid but not winning material. The domain (SQL review) is real but narrow, and the mechanics (approve/reject) are too close to a linter.

---

## 2. Why We're Pivoting

### The Scoring Rubric (what judges care about)

| Criteria | Weight | SQL Review Score | Incident Commander Score |
|----------|--------|-----------------|------------------------|
| **Real-world utility** | **30%** | ~20/30 (real but narrow) | **28-30/30** (every engineer does this) |
| **Task & grader quality** | **25%** | ~18/25 (decent) | **22-25/25** (natural difficulty curve) |
| **Environment design** | **20%** | ~16/20 (clean but simple) | **18-20/20** (novel info-gathering mechanic) |
| **Code quality & spec** | **15%** | ~13/15 (strong) | **13-15/15** (same architecture) |
| **Creativity & novelty** | **10%** | ~5/10 (SQL review isn't new) | **9-10/10** (nobody builds this) |
| **TOTAL** | **100%** | **~72** | **~90-95** |

### Why Incident Commander Wins

1. **Judges are Meta and HuggingFace engineers.** They've all been on-call. They'll *feel* this environment's value in their bones.

2. **The information-gathering mechanic is genuinely novel.** In every other OpenEnv submission, the agent sees everything upfront. In ours, the agent must *choose* what to investigate. This creates a real exploration vs. exploitation tradeoff — which is what RL research actually needs.

3. **Nobody else is building this.** Guaranteed differentiation on the creativity score.

4. **Production incident response is a $2B+ market** (PagerDuty, OpsGenie, Datadog). Judges will immediately see commercial value.

---

## 3. What We're Building

### The Concept

An AI agent plays the role of an **on-call engineer** at a tech company. A production incident fires. The agent must:

```
ALERT FIRES
    │
    ▼
TRIAGE — What's the severity? What's affected?
    │
    ▼
INVESTIGATE — Check logs, metrics, dependencies
    │          (each check costs a step — be efficient!)
    ▼
DIAGNOSE — What's the root cause?
    │
    ▼
FIX — Apply the correct remediation
    │
    ▼
COMMUNICATE — Post status updates (hard task only)
```

### The System Being Simulated

A microservice architecture with **8 services**:

```
                    ┌─────────────────┐
                    │   api-gateway    │  (entry point — routes all traffic)
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
        ┌──────────┐  ┌───────────┐  ┌───────────┐
        │user-svc  │  │order-svc  │  │payment-svc│
        └────┬─────┘  └─────┬─────┘  └─────┬─────┘
             │              │               │
             ▼              ▼               ▼
        ┌──────────┐  ┌───────────┐  ┌───────────┐
        │postgres- │  │redis-cache│  │task-queue │
        │primary   │  └───────────┘  └───────────┘
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │postgres- │
        │replica   │
        └──────────┘
```

Each service has:
- A health status (healthy / degraded / down / unknown)
- Pre-computed log entries (ERROR, WARN, INFO lines)
- Pre-computed metrics (CPU, memory, error rate, latency, connections)
- A dependency graph (what it calls, what calls it)

### The Killer Feature: Information Gathering

**What makes us unique across ALL of OpenEnv:**

When the episode starts, the agent sees:
- The alert(s) that fired
- High-level service statuses (healthy/degraded/down)
- A summary of the incident

The agent does **NOT** see:
- Actual log contents
- Actual metric values
- Dependency graphs
- What the root cause is

To learn more, the agent must **take investigation actions**:
- `investigate_logs("user-service")` → Returns that service's log entries
- `investigate_metrics("order-service")` → Returns CPU, memory, error rate, latency
- `investigate_deps("api-gateway")` → Returns what it depends on and what depends on it

**Each investigation costs 1 step.** There's an SLA timer ticking. Smart agents investigate the right things quickly. Dumb agents waste steps checking irrelevant services.

This creates a **genuine strategic choice** that's interesting for RL training — exactly what judges are looking for.

---

## 4. How It Works — The Full Picture

### Agent-Environment Interaction Loop

```
Agent                              Environment
  │                                     │
  │──── POST /reset ───────────────────▶│
  │     {task_id: "triage_and_fix"}     │
  │                                     │  Load scenario, init state
  │◀──── observation ──────────────────│
  │      (alerts, service statuses,     │
  │       incident summary)             │
  │                                     │
  │──── POST /step ────────────────────▶│
  │     {action_type:                   │
  │      "investigate_logs",            │
  │      target_service:                │  Look up pre-computed logs,
  │      "user-service"}                │  add to observation, compute reward
  │                                     │
  │◀──── (observation, reward,         │
  │       done, info) ─────────────────│
  │      observation now includes       │
  │      user-service logs!             │
  │                                     │
  │──── POST /step ────────────────────▶│
  │     {action_type: "diagnose",       │
  │      diagnosis: "user-service       │  Check diagnosis against ground truth,
  │      OOM crash"}                    │  compute reward
  │                                     │
  │◀──── (observation, reward,         │
  │       done, info) ─────────────────│
  │                                     │
  │──── POST /step ────────────────────▶│
  │     {action_type: "apply_fix",      │
  │      target_service:                │  Check if correct fix on correct service,
  │      "user-service",                │  if yes → mark resolved, compute final grade
  │      fix_type:                      │
  │      "restart_service"}             │
  │                                     │
  │◀──── (observation, reward=0.30,    │
  │       done=true,                    │
  │       info={final_grade: 0.92})    │
```

### What the Observation Looks Like (JSON)

**After reset (initial):**
```json
{
  "incident_id": "direct-001",
  "severity": "P1",
  "title": "API Gateway returning 502 errors",
  "summary": "Multiple customers reporting 502 errors. Error rate spike detected at 14:32 UTC.",
  "affected_services": [
    {"service_id": "api-gateway", "name": "API Gateway", "status": "degraded", "service_type": "web"},
    {"service_id": "user-service", "name": "User Service", "status": "down", "service_type": "api"},
    {"service_id": "order-service", "name": "Order Service", "status": "degraded", "service_type": "api"},
    {"service_id": "postgres-primary", "name": "PostgreSQL Primary", "status": "healthy", "service_type": "database"},
    {"service_id": "redis-cache", "name": "Redis Cache", "status": "healthy", "service_type": "cache"}
  ],
  "alerts": [
    {"alert_id": "alert-1", "severity": "critical", "service_id": "api-gateway",
     "title": "Error rate > 5%", "message": "api-gateway error rate at 23.4%, threshold 5%", "timestamp": "3 min ago"},
    {"alert_id": "alert-2", "severity": "critical", "service_id": "user-service",
     "title": "Health check failing", "message": "user-service /health returning 503 for 2 minutes", "timestamp": "2 min ago"}
  ],
  "logs_gathered": {},
  "metrics_gathered": {},
  "dependencies_gathered": {},
  "diagnosis_submitted": null,
  "fixes_applied": [],
  "status_updates_posted": [],
  "current_step": 0,
  "task_id": "triage_and_fix",
  "sla_deadline": 8,
  "steps_remaining": 10,
  "done": false,
  "session_stats": {"investigations": 0, "total_reward": 0.0},
  "last_action_result": "Incident assigned. Begin investigation."
}
```

**After investigating logs of user-service (step 1):**
```json
{
  "...same as above, plus...",
  "logs_gathered": {
    "user-service": [
      {"timestamp": "14:30:12", "level": "WARN", "message": "GC overhead limit approaching - heap usage at 89%"},
      {"timestamp": "14:31:45", "level": "ERROR", "message": "java.lang.OutOfMemoryError: Java heap space"},
      {"timestamp": "14:31:46", "level": "ERROR", "message": "Service unhealthy - failing readiness probe"},
      {"timestamp": "14:32:01", "level": "ERROR", "message": "Connection refused on port 8080"}
    ]
  },
  "current_step": 1,
  "steps_remaining": 9,
  "last_action_result": "Retrieved 4 log entries from user-service"
}
```

### What the Action Space Looks Like

```json
{
  "action_type": "investigate_logs | investigate_metrics | investigate_deps | diagnose | apply_fix | update_status | escalate",
  "target_service": "service-id (for investigate/fix actions)",
  "diagnosis": "free-text root cause analysis (for diagnose action)",
  "fix_type": "restart_service | rollback_deploy | scale_up | failover_database | clear_cache | fix_config | increase_rate_limit | kill_query | flush_queue",
  "status_message": "free-text status update (for update_status action)",
  "reasoning": "agent's reasoning for this action (optional, for grading insight)"
}
```

---

## 5. What Stays vs. What Changes

### Identical / Reused (the skeleton — ~40% of code)

| Component | Why It Stays |
|-----------|-------------|
| **FastAPI endpoints** (`main.py`) | Same 5 endpoints: `/health`, `/reset`, `/step`, `/state`, `/tasks`. Just swap the model types. |
| **Env class interface** (`env.py`) | Same `reset()` → obs, `step(action)` → (obs, reward, done, info), `state()` → dict. Different internal logic. |
| **Grading architecture** (`tasks.py`) | Same pattern: dense per-step rewards + final episode graders. Different formulas. |
| **Pydantic model pattern** (`models.py`) | Same approach: typed request/response models. Different fields. |
| **Dockerfile** | Literally copy-paste. Same base image, same port, same healthcheck. |
| **requirements.txt** | Identical dependencies: fastapi, uvicorn, pydantic, openai, httpx, python-dotenv. |
| **inference.py structure** | Same: OpenAI client → loop steps → `[START]`/`[STEP]`/`[END]` logs. Different prompts and action logic. |
| **HF Space config** | Same `sdk: docker`, `app_port: 7860`. New title and tags. |

### Completely New (the substance — ~60% of code)

| Component | What Changes |
|-----------|-------------|
| **models.py** | All new models: `ServiceInfo`, `Alert`, `LogEntry`, `MetricSnapshot`, `DependencyInfo`, `IncidentObservation`, `IncidentAction`, `IncidentReward` |
| **data.py** | All new: 8-service architecture + 12 incident scenarios with pre-computed logs, metrics, dependency health per service |
| **tasks.py** | All new: 3 task definitions, 3 step reward functions, 3 final graders — all with incident-specific scoring logic |
| **env.py internal logic** | New state machine: investigation accumulation, diagnosis tracking, fix verification, SLA tracking, communication logging |
| **inference.py prompts** | New system prompt (on-call engineer), new action selection logic (investigate → diagnose → fix) |
| **openenv.yaml** | New name, description, tags, action space schema, observation space schema |
| **README.md** | Entirely new documentation |

### Mental Model

```
SQL Review Env                    Incident Commander
─────────────                    ──────────────────
SQLQuery model         →         ServiceInfo, Alert, LogEntry, MetricSnapshot
SQLAction model        →         IncidentAction (7 action types vs 5)
SQLObservation model   →         IncidentObservation (accumulates investigation data)
56 SQL queries         →         12 incident scenarios (with logs/metrics/deps each)
approve/reject         →         investigate/diagnose/fix/communicate
verdict accuracy       →         diagnosis + fix + efficiency + communication
All data visible       →         Data revealed through investigation (NOVEL)
```

---

## 6. Detailed File-by-File Plan

### `server/models.py` — Complete Rewrite

**Current:** SQLQuery, SQLQueryPublic, SQLObservation, SQLAction, SQLReward, TaskDefinition  
**New:** All incident models listed below

```python
# Service representation
class ServiceInfo(BaseModel):        # Public view (agent sees this)
class ServiceInfoFull(ServiceInfo):  # Ground truth (hidden from agent)

# Alert/page
class Alert(BaseModel):             # Fired alerts with severity + message

# Investigation data (returned when agent investigates)
class LogEntry(BaseModel):           # timestamp, level, message, service_id
class MetricSnapshot(BaseModel):     # cpu, memory, error_rate, latency, connections
class DependencyInfo(BaseModel):     # depends_on, depended_by, health_summary

# Core OpenEnv models
class IncidentObservation(BaseModel):  # Everything the agent sees
class IncidentAction(BaseModel):       # Everything the agent can do
class IncidentReward(BaseModel):       # Reward breakdown

# Task definition (same pattern as before)
class TaskDefinition(BaseModel):       # id, name, difficulty, max_steps, etc.
```

Estimated: **~120 lines**

---

### `server/data.py` — Complete Rewrite (LARGEST FILE)

**Current:** 56 SQL queries generated with seed=42  
**New:** 8-service architecture + 12 incident scenarios

**Structure:**

```python
# 1. Service architecture definition
SERVICES = {
    "api-gateway": { name, type, depends_on, baseline_metrics, ... },
    "user-service": { ... },
    "order-service": { ... },
    "payment-svc": { ... },
    "postgres-primary": { ... },
    "postgres-replica": { ... },
    "redis-cache": { ... },
    "task-queue": { ... },
}

# 2. Dependency graph
DEPENDENCY_GRAPH = {
    "api-gateway": {"depends_on": ["user-service", "order-service"], "depended_by": []},
    "user-service": {"depends_on": ["postgres-primary", "redis-cache"], "depended_by": ["api-gateway"]},
    # ... etc
}

# 3. Scenario definitions (12 total)
SCENARIOS = {
    "direct-001": {
        "title": "API Gateway returning 502 errors",
        "severity": "P1",
        "summary": "...",
        "root_cause_service": "user-service",
        "root_cause_detail": "Out of memory - Java heap space exhausted",
        "correct_fixes": [{"service": "user-service", "fix_type": "restart_service"}],
        "affected_services": {"user-service": "down", "api-gateway": "degraded", ...},
        "red_herring_services": [],
        "alerts": [...],
        "logs": {"user-service": [...], "api-gateway": [...], ...},
        "metrics": {"user-service": {...}, "api-gateway": {...}, ...},
        "dependencies_health": {"user-service": "postgres-primary: healthy, redis-cache: healthy", ...},
    },
    # ... 11 more scenarios
}

# 4. Task-to-scenario mapping (deterministic, seed=42)
def get_scenario_for_task(task_id: str, seed: int = 42) -> dict
```

Estimated: **~700-900 lines** (most of this is scenario data — logs, metrics, alerts)

---

### `server/tasks.py` — Complete Rewrite

**Current:** 3 SQL tasks + 3 step reward fns + 3 final graders  
**New:** 3 incident tasks + 3 step reward fns + 3 final graders

```python
# Task definitions
TASK_DEFINITIONS = {
    "triage_and_fix": TaskDefinition(difficulty="easy", max_steps=10, ...),
    "cascade_diagnosis": TaskDefinition(difficulty="medium", max_steps=20, ...),
    "incident_commander": TaskDefinition(difficulty="hard", max_steps=30, ...),
}

# Dense step rewards (called every step)
def compute_step_reward_triage(action, scenario, env_state) -> float
def compute_step_reward_cascade(action, scenario, env_state) -> float
def compute_step_reward_commander(action, scenario, env_state) -> float

# Final episode graders (called when done=True)
def grade_triage(env_state, scenario) -> IncidentReward        # 0.0-1.0
def grade_cascade(env_state, scenario) -> IncidentReward       # 0.0-1.0
def grade_commander(env_state, scenario) -> IncidentReward     # 0.0-1.0
```

Estimated: **~350 lines**

---

### `server/env.py` — Major Rewrite (Same Interface)

**Current:** SQLReviewEnv with query tracking  
**New:** IncidentEnv with investigation accumulation

```python
class IncidentEnv:
    def __init__(self, task_id):
        # Load scenario, init state

    def reset(self) -> IncidentObservation:
        # Clean state, load scenario, return initial observation

    def step(self, action: IncidentAction) -> Tuple[IncidentObservation, float, bool, dict]:
        # Route by action_type:
        #   investigate_logs → look up pre-computed logs, add to observation
        #   investigate_metrics → look up pre-computed metrics, add to observation
        #   investigate_deps → look up dependency info, add to observation
        #   diagnose → record diagnosis text, check against ground truth
        #   apply_fix → check fix against ground truth, resolve if correct
        #   update_status → record message
        #   escalate → record escalation
        # Compute step reward
        # Check done (resolved OR max_steps)

    def state(self) -> dict:
        # Full internal state including ground truth
```

Key internal state tracked:
- `logs_gathered: Dict[str, List]` — which services' logs the agent has seen
- `metrics_gathered: Dict[str, Dict]` — which services' metrics the agent has seen
- `deps_gathered: Dict[str, Dict]` — which dependencies the agent has checked
- `diagnosis: Optional[str]` — agent's submitted diagnosis
- `fixes_applied: List[Dict]` — fixes the agent has attempted
- `status_updates: List[str]` — status messages posted
- `resolved: bool` — whether the correct fix was applied
- `investigated_services: Dict[str, Set[str]]` — tracks service+type combos to detect repeats

Estimated: **~250 lines**

---

### `server/main.py` — Minor Updates

**Changes:**
- Line 6: `from .env import SQLReviewEnv` → `from .env import IncidentEnv`
- Line 7: `from .models import SQLAction` → `from .models import IncidentAction`
- Line 23-25: Update title/description
- Line 39: `env: Optional[SQLReviewEnv]` → `env: Optional[IncidentEnv]`
- Line 49-56: Update `TASK_ID_MAP` keys
- Line 101: `SQLReviewEnv(task_id=task_id)` → `IncidentEnv(task_id=task_id)`
- Line 139: `SQLAction(**body)` → `IncidentAction(**body)`

Everything else stays identical. Estimated: **~20 lines changed**

---

### `inference.py` — Major Rewrite (Same Structure)

**Same:** OpenAI client, httpx async calls, `[START]`/`[STEP]`/`[END]` log format, env var handling  
**New:** System prompt, user prompt, action parsing logic

```python
SYSTEM_PROMPT = """You are a senior on-call engineer responding to a production incident.
You have access to these actions:
1. investigate_logs(service_id) — View recent logs
2. investigate_metrics(service_id) — View CPU, memory, error rate, latency
3. investigate_deps(service_id) — View dependency graph
4. diagnose(text) — Submit root cause analysis
5. apply_fix(service_id, fix_type) — Apply remediation
6. update_status(message) — Post status update
7. escalate(reasoning) — Escalate to another team
..."""

def get_agent_action(client, observation, history) -> dict:
    # Build user prompt from current observation state
    # Include: alerts, any gathered logs/metrics, diagnosis state
    # Call LLM, parse JSON response
    # Return action dict
```

Estimated: **~220 lines**

---

### `openenv.yaml` — Complete Rewrite

```yaml
name: incident-commander
version: "1.0.0"
description: "AI agent environment for production incident response..."
tags: [openenv, incident-response, devops, sre, on-call]
tasks:
  - id: triage_and_fix (easy, 10 steps)
  - id: cascade_diagnosis (medium, 20 steps)
  - id: incident_commander (hard, 30 steps)
action_space: { action_type, target_service, diagnosis, fix_type, status_message, reasoning }
observation_space: { incident_id, severity, title, alerts, affected_services, logs_gathered, ... }
```

---

### `README.md` — Complete Rewrite

New documentation covering:
- Why incident response? (motivation)
- The 8-service architecture diagram
- Action space table
- Observation space table
- 3 tasks with scoring breakdowns
- Setup instructions (Docker + local)
- API usage examples
- Baseline scores
- Environment variables

---

### `Dockerfile` — NO CHANGES

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
```

### `requirements.txt` — NO CHANGES

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
openai>=1.0.0
python-dotenv>=1.0.0
httpx>=0.25.0
```

---

## 7. The 12 Incident Scenarios

### Category 1: Direct Failures (Easy Task Pool)

Root cause is obvious from logs. Agent just needs to investigate the right service.

#### `direct-001` — API Gateway 502 Errors
- **Alert:** api-gateway error rate at 23.4%
- **Root cause:** user-service crashed with `java.lang.OutOfMemoryError`
- **Clue in logs:** `"java.lang.OutOfMemoryError: Java heap space"` in user-service
- **Correct fix:** `restart_service` on `user-service`
- **Services involved:** api-gateway (degraded, symptom), user-service (down, root cause), order-service (degraded, symptom)

#### `direct-002` — Database Connection Pool Exhausted
- **Alert:** postgres-primary connection count at 198/200
- **Root cause:** Long-running analytics query holding 150 connections
- **Clue in logs:** `"FATAL: too many connections"` and `"query running for 47 minutes: SELECT ... FROM large_table"` in postgres-primary
- **Correct fix:** `kill_query` on `postgres-primary`
- **Services involved:** postgres-primary (degraded, root cause), user-service (degraded, symptom), order-service (degraded, symptom)

#### `direct-003` — Redis Cache Unavailable
- **Alert:** redis-cache health check failing
- **Root cause:** Redis OOM, maxmemory exceeded, all eviction failed
- **Clue in logs:** `"OOM command not allowed when used memory > 'maxmemory'"` in redis-cache
- **Correct fix:** `restart_service` on `redis-cache`
- **Services involved:** redis-cache (down, root cause), user-service (degraded, symptom), order-service (degraded, symptom)

#### `direct-004` — Payment Processing Failures
- **Alert:** payment-svc error rate spike to 45%
- **Root cause:** Bad deployment — new version has a bug in payment validation
- **Clue in logs:** `"TypeError: cannot read property 'amount' of undefined"` and `"Deployment v2.3.1 activated 5 minutes ago"` in payment-svc
- **Correct fix:** `rollback_deploy` on `payment-svc`
- **Services involved:** payment-svc (degraded, root cause), order-service (degraded, symptom)

---

### Category 2: Cascading Failures (Medium Task Pool)

Root cause is upstream. Symptoms appear in downstream services. Agent must trace the dependency chain.

#### `cascade-001` — Order Creation Timeouts
- **Alerts:** order-service timeouts, api-gateway elevated latency
- **Root cause:** postgres-replica replication lag — disk 98% full, WAL files piling up
- **Misleading signal:** order-service logs show timeout errors (but it's not the source)
- **Dependency chain:** postgres-replica → order-service reads lag → api-gateway timeouts
- **Correct fix:** `fix_config` on `postgres-replica` (disk cleanup, WAL archival)

#### `cascade-002` — Intermittent 500s on All API Endpoints
- **Alerts:** 500 errors across user-service, order-service; postgres-primary elevated load
- **Root cause:** redis-cache memory pressure → mass evictions → cache stampede → all services hit DB directly → DB overloaded
- **Dependency chain:** redis-cache evictions → all services bypass cache → postgres-primary overwhelmed
- **Correct fix:** `scale_up` on `redis-cache` + `increase_rate_limit` on `api-gateway`

#### `cascade-003` — User Login Failures
- **Alerts:** user-service 401 errors, api-gateway reporting auth failures
- **Root cause:** Bad config push to user-service — auth0 endpoint URL was changed to wrong value
- **Misleading signal:** api-gateway shows auth errors (but it's just forwarding user-service failures)
- **Correct fix:** `fix_config` on `user-service`

#### `cascade-004` — Background Job Queue Growing Unbounded
- **Alerts:** task-queue length at 50k+ messages, payment-svc delayed processing
- **Root cause:** task-queue consumer process crashed (segfault), messages piling up
- **Dependency chain:** task-queue consumers dead → payments not processed → order-service retries → queue grows faster
- **Correct fix:** `restart_service` on `task-queue`

---

### Category 3: Complex / Red Herring Incidents (Hard Task Pool)

Multiple alerts fire. Some are relevant, some are misleading. Agent must distinguish signal from noise.

#### `complex-001` — Multiple Services Degraded After Deploy
- **Alerts:** 6 alerts across api-gateway, user-service, order-service, redis-cache, postgres-replica
- **Root cause:** api-gateway config change set rate limit to 10 req/s (was 10,000) — throttling everything
- **Red herrings:** redis-cache slightly elevated memory (normal GC cycle), postgres-replica replication lag (scheduled maintenance, unrelated)
- **Correct fix:** `fix_config` on `api-gateway` (restore rate limit)

#### `complex-002` — Slow API Responses, Customer Complaints
- **Alerts:** api-gateway high latency, postgres-primary elevated connections, order-service high memory
- **Root cause:** Memory leak in order-service — gradual over 6 hours, now at 94% memory, GC pauses causing latency spikes
- **Red herrings:** postgres-primary elevated connections (caused by order-service retries, not a DB issue), api-gateway latency (symptom of order-service slowness)
- **Correct fix:** `restart_service` on `order-service`

#### `complex-003` — Data Inconsistency Alerts Firing
- **Alerts:** Data mismatch alerts, user-service elevated errors, redis-cache stale data warnings
- **Root cause:** postgres-primary had brief network partition → writes went to replica → split-brain state
- **Red herrings:** user-service errors (retries from inconsistent reads, not a service bug), redis-cache stale data (symptom of DB inconsistency)
- **Correct fix:** `failover_database` (promote consistent replica, reconcile)

#### `complex-004` — Alert Storm: 15 Alerts in 2 Minutes
- **Alerts:** 8-12 alerts firing across nearly every service
- **Root cause:** DDoS attack on api-gateway exhausting connection pool, cascading everywhere
- **Red herrings:** Every downstream service shows degraded metrics (symptoms, not causes), payment-svc appears to be failing (just slow under load)
- **Correct fix:** `increase_rate_limit` on `api-gateway` + `scale_up` on `api-gateway`

---

## 8. The 3 Tasks & How They're Graded

### Task 1: `triage_and_fix` (Easy)

| Property | Value |
|----------|-------|
| Difficulty | Easy |
| Max steps | 10 |
| SLA deadline | Step 8 |
| Scenario pool | Direct failures (4 scenarios) |
| What agent must do | Investigate → Diagnose → Fix |

**Final Grade Formula:**
```
diagnosis_score (40%):
  1.0 = correct root cause service + correct issue
  0.5 = correct service, vague issue
  0.0 = wrong

fix_score (40%):
  1.0 = correct fix_type on correct service
  0.5 = partial match
  0.0 = wrong

efficiency_score (20%):
  1.0 = resolved in 1-4 steps
  0.75 = 5-6 steps
  0.5 = 7-8 steps (near SLA)
  0.25 = 9-10 steps (SLA breach)
  0.0 = not resolved

FINAL = diagnosis * 0.40 + fix * 0.40 + efficiency * 0.20
```

**Expected baseline score:** ~0.80-0.90 (most LLMs can identify obvious OOM/crash from logs)

---

### Task 2: `cascade_diagnosis` (Medium)

| Property | Value |
|----------|-------|
| Difficulty | Medium |
| Max steps | 20 |
| SLA deadline | Step 15 |
| Scenario pool | Cascading failures (4 scenarios) |
| What agent must do | Investigate chain → Trace root cause → Diagnose → Fix |

**Final Grade Formula:**
```
diagnosis_score (35%):
  1.0 = correct root cause service + mechanism
  0.6 = correct root cause service, vague mechanism
  0.3 = identified affected service but not root
  0.0 = wrong

fix_score (30%):
  1.0 = correct fix on correct service
  0.5 = right service wrong fix, or right fix wrong service
  0.0 = wrong

investigation_quality (20%):
  = (useful investigations) / (total investigations)
  "useful" = investigated a service that is affected or root cause

efficiency_score (15%):
  1.0 = resolved in 1-8 steps
  0.75 = 9-12 steps
  0.5 = 13-15 steps (near SLA)
  0.25 = 16-20 steps (SLA breach)
  0.0 = not resolved

FINAL = diagnosis * 0.35 + fix * 0.30 + investigation * 0.20 + efficiency * 0.15
```

**Expected baseline score:** ~0.65-0.75 (LLMs often mistake symptoms for root cause)

---

### Task 3: `incident_commander` (Hard)

| Property | Value |
|----------|-------|
| Difficulty | Hard |
| Max steps | 30 |
| SLA deadline | Step 20 |
| Scenario pool | Complex/red herring incidents (4 scenarios) |
| What agent must do | Triage → Investigate efficiently → Diagnose → Fix (maybe 2 fixes) → Communicate |

**Final Grade Formula:**
```
diagnosis_score (25%):
  1.0 = correct root cause + mechanism + distinguishes from red herrings
  0.6 = correct root cause service + mentions mechanism
  0.3 = partially correct
  0.0 = wrong or diagnosed red herring as cause

fix_score (25%):
  Average across all required fixes:
    1.0 = correct fix_type on correct service
    0.5 = partial match
    0.0 = wrong

investigation_quality (20%):
  focused_ratio = (relevant investigations) / (total investigations)
  dep_check_bonus = +0.1 if checked 2+ dependency graphs
  Score = min(1.0, focused_ratio + dep_check_bonus)

communication_score (15%):
  1.0 = 2+ meaningful status updates (>30 chars)
  0.5 = 1 meaningful status update
  0.0 = no updates

efficiency_score (15%):
  1.0 = resolved in 1-12 steps
  0.75 = 13-16 steps
  0.5 = 17-20 steps (SLA boundary)
  0.25 = 21-30 steps (SLA breach)
  0.0 = not resolved

penalties:
  -0.10 per fix applied to red herring service
  -0.08 per unnecessary escalation
  -0.12 if root cause diagnosis names a red herring

FINAL = clamp(diagnosis*0.25 + fix*0.25 + investigation*0.20 + communication*0.15 + efficiency*0.15 - penalties, 0.0, 1.0)
```

**Expected baseline score:** ~0.50-0.65 (red herrings genuinely trip up even frontier models)

---

## 9. Reward Design — Step by Step

### Why Dense Rewards Matter

Binary (sparse) rewards: "You got 0.7 at the end" — useless for RL training.  
Dense rewards: "This investigation was useful (+0.10), this one was wasteful (-0.03)" — actual training signal.

Our environment gives **per-step rewards** that tell the agent:
- "Good, you're investigating the right thing"
- "Bad, you're wasting time on an irrelevant service"
- "Great, your diagnosis is correct"
- "Careful, you're fixing a symptom not the cause"

### Step Reward Tables

#### Easy Task (`triage_and_fix`)

| Action | Condition | Reward |
|--------|-----------|--------|
| `investigate_logs` | Root cause service | +0.15 |
| `investigate_logs` | Affected (not root cause) service | +0.05 |
| `investigate_logs` | Healthy/irrelevant service | +0.00 |
| `investigate_metrics` | Root cause service | +0.10 |
| `investigate_metrics` | Other service | +0.03 |
| `investigate_deps` | Any service | +0.05 |
| `diagnose` | Correct root cause | +0.25 |
| `diagnose` | Wrong root cause | -0.10 |
| `apply_fix` | Correct fix + correct service | +0.30 |
| `apply_fix` | Wrong fix or wrong service | -0.15 |
| Any repeated investigation | Same service + same type | -0.05 |

#### Medium Task (`cascade_diagnosis`)

| Action | Condition | Reward |
|--------|-----------|--------|
| `investigate_*` | Root cause service | +0.12 |
| `investigate_*` | Affected service | +0.08 |
| `investigate_deps` | Any (critical for chain tracing) | +0.10 |
| `diagnose` | Correct root cause | +0.20 |
| `diagnose` | Symptom-as-cause (common mistake) | -0.05 |
| `apply_fix` | Correct | +0.25 |
| `apply_fix` | On symptom service | -0.10 |
| `update_status` | Meaningful (>30 chars) | +0.05 |
| Repeated investigation | Same service + type | -0.05 |

#### Hard Task (`incident_commander`)

| Action | Condition | Reward |
|--------|-----------|--------|
| `investigate_*` | Root cause service | +0.10 |
| `investigate_*` | Truly affected service | +0.06 |
| `investigate_*` | Red herring service | -0.03 |
| `investigate_deps` | Any (architecture understanding) | +0.05 min |
| `diagnose` | Correct | +0.15 |
| `diagnose` | Wrong (symptom/red herring as cause) | -0.08 |
| `apply_fix` | Correct on root cause | +0.20 |
| `apply_fix` | Correct secondary fix | +0.10 |
| `apply_fix` | On red herring service | -0.15 |
| `update_status` | First meaningful update | +0.08 |
| `update_status` | Subsequent updates | +0.05 |
| `escalate` | Unnecessary | -0.10 |
| Repeated investigation | Same service + type | -0.05 |

---

## 10. Inference Script Strategy

The inference script (`inference.py`) is what the judges actually run. It must:
- Use `OpenAI` client (mandatory)
- Read `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` from env vars
- Emit `[START]`, `[STEP]`, `[END]` logs in exact format
- Complete all 3 tasks
- Run in < 20 minutes
- Run on vcpu=2, memory=8gb

### Agent Strategy (simple but effective)

```
For each task:
  1. Reset environment with task_id
  2. Read alerts from observation → identify top 2 suspicious services
  3. investigate_logs on most suspicious service
  4. investigate_metrics on most suspicious service
  5. investigate_deps on most suspicious service (understand architecture)
  6. If medium/hard: investigate_logs on 2nd suspicious service
  7. diagnose based on gathered evidence
  8. apply_fix based on diagnosis
  9. If hard task: post update_status
  10. If hard task and 2 fixes needed: apply second fix
```

### LLM Prompt Design

The system prompt tells the LLM it's an on-call engineer. The user prompt includes:
- Current alerts
- Service statuses
- Any gathered investigation data (logs, metrics, deps)
- Current diagnosis state
- Steps remaining and SLA countdown

The LLM responds with a JSON action. We parse it and send to `/step`.

---

## 11. Implementation Order & Timeline

### The Order (dependency-aware)

```
models.py  ──────┐
                  ├──▶  env.py  ──▶  main.py  ──▶  Local test
data.py   ───────┤                                       │
                  │                                       ▼
tasks.py  ────────┘                inference.py  ──▶  Full test
                                                         │
                                   openenv.yaml          ▼
                                   README.md        Docker test
                                                         │
                                                         ▼
                                                    Deploy to HF
```

### Time Estimates

| Phase | Task | Duration | Running Total |
|-------|------|----------|--------------|
| **1** | models.py | 45 min | 0:45 |
| **1** | data.py — service architecture | 45 min | 1:30 |
| **1** | data.py — 4 direct failure scenarios | 1 hour | 2:30 |
| **1** | data.py — 4 cascade failure scenarios | 1 hour | 3:30 |
| **1** | data.py — 4 complex scenarios | 1 hour | 4:30 |
| **2** | tasks.py — definitions + step rewards | 1.5 hours | 6:00 |
| **2** | tasks.py — final graders | 1 hour | 7:00 |
| **2** | env.py | 1 hour | 8:00 |
| **3** | main.py updates | 20 min | 8:20 |
| **3** | inference.py | 1 hour | 9:20 |
| **3** | openenv.yaml + README.md | 40 min | 10:00 |
| **4** | Local testing + bug fixes | 2 hours | 12:00 |
| **4** | Docker build + test | 30 min | 12:30 |
| **5** | Deploy to HF + validate | 1 hour | 13:30 |
| **-** | Buffer for issues | 1.5 hours | **15:00** |

---

## 12. Testing & Validation Checklist

### Local Server Tests (must all pass)

```
[ ] uvicorn server.main:app starts without errors
[ ] GET  /health → {"status": "ok"}
[ ] GET  / → returns endpoint list
[ ] POST /reset {"task_id": "triage_and_fix"} → valid observation with alerts
[ ] POST /reset {"task_id": "cascade_diagnosis"} → valid observation
[ ] POST /reset {"task_id": "incident_commander"} → valid observation
[ ] POST /reset {} → defaults to easy task
[ ] GET  /tasks → returns exactly 3 tasks
[ ] POST /step investigate_logs → logs appear in observation
[ ] POST /step investigate_metrics → metrics appear in observation
[ ] POST /step investigate_deps → deps appear in observation
[ ] POST /step diagnose → diagnosis recorded
[ ] POST /step apply_fix (correct) → done=true, final_grade in info
[ ] POST /step apply_fix (wrong) → done=false, negative reward
[ ] POST /step with invalid service → graceful error
[ ] POST /step after done → returns done=true
[ ] GET  /state → includes ground truth fields
[ ] Duplicate investigation → penalty applied (-0.05)
[ ] Full easy episode → final grade between 0.0-1.0
[ ] Full medium episode → final grade between 0.0-1.0
[ ] Full hard episode → final grade between 0.0-1.0
```

### Docker Tests

```
[ ] docker build -t incident-commander . → succeeds
[ ] docker run -p 7860:7860 incident-commander → starts cleanly
[ ] All local server tests pass against Docker container
[ ] Container uses < 8GB memory
```

### Inference Script Tests

```
[ ] python inference.py completes without errors
[ ] [START] log format is correct
[ ] [STEP] log format is correct
[ ] [END] log format is correct
[ ] All 3 tasks produce scores > 0.0
[ ] At least easy task scores > 0.5
[ ] Total runtime < 20 minutes
[ ] Runs on vcpu=2, memory=8gb
```

### Pre-Submission Validation

```
[ ] openenv.yaml matches actual implementation
[ ] README.md is accurate and complete
[ ] HF Space deploys and responds to /health
[ ] Validation script passes (if available)
[ ] inference.py works against deployed HF Space
```

---

## 13. Deployment Steps

### Step 1: Create Branch
```bash
git checkout -b incident-commander
```

### Step 2: Implement All Changes
(Follow implementation order from Section 11)

### Step 3: Test Locally
```bash
cd sql_review_env
pip install -r requirements.txt
uvicorn server.main:app --port 7860
# Run all tests from Section 12
```

### Step 4: Test Docker
```bash
cd sql_review_env
docker build -t incident-commander .
docker run -p 7860:7860 incident-commander
# Run all tests
```

### Step 5: Test Inference
```bash
export HF_TOKEN="your-token"
export ENV_BASE_URL="http://localhost:7860"
python inference.py
# Verify log format and scores
```

### Step 6: Deploy to HuggingFace Spaces
```bash
# Option A: Update existing space
# Option B: Create new space
# Push sql_review_env/ contents to HF Space repo
```

### Step 7: Validate Deployment
```bash
curl https://your-space.hf.space/health
# Should return {"status": "ok"}
```

### Step 8: Submit
- Go to hackathon portal
- Submit HF Space URL
- Verify submission confirmation

---

## 14. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Scenarios feel artificial/unrealistic | Medium | High | Write logs from real incident experience. Use actual error messages from real services (Java OOM, Postgres connection errors, Redis OOM, etc.) |
| Grader bugs give wrong scores | Medium | High | Unit test each grader with known inputs before integration. Test edge cases (no diagnosis, no fix, all wrong, all right). |
| Inference script fails on judge's infra | Low | Critical | Keep fallback actions. Test with multiple models. Ensure graceful error handling. |
| Docker build fails on judge's infra | Low | Critical | Keep Dockerfile simple (identical to current working one). No unusual dependencies. |
| Time runs out before all 3 tasks done | Medium | Medium | Implement easy task FIRST (minimum viable). Each task is independent — even 2 well-done tasks > 3 rushed tasks. |
| LLM can't parse JSON response correctly | Medium | Low | Strip markdown fences, handle parse errors, return safe fallback action. |
| HF Space deployment issues | Low | Medium | Deploy early, iterate. Keep previous working version as backup. |
| Diagnosis grading too strict / too lenient | Medium | Medium | Use keyword matching, not exact string match. Check if diagnosis *contains* root cause service ID and key terms. |
| Agent gets stuck in investigation loop | Low | Low | Max steps enforced. Investigation repeats penalized. Episode always terminates. |

---

## Summary

**What we have:** A working SQL Review environment scoring ~72/100.

**What we're building:** An Incident Commander environment targeting ~90-95/100.

**The key insight:** Same kitchen, different (much better) menu. We reuse 40% of the code (the FastAPI/Pydantic/Docker infrastructure) and replace 60% (the domain, scenarios, grading logic).

**The winning mechanic:** Information gathering as actions — genuinely novel in OpenEnv, creates real strategic choices for RL agents, and maps perfectly to how actual incident response works.

**Timeline:** ~15 hours of focused implementation, fitting within the deadline with buffer.

**Fallback:** If time runs out, even a polished easy + medium task submission will score higher than the current SQL Review env, because the domain and mechanics are fundamentally more impressive.
