# SQL Review OpenEnv Environment — PRD

## Original Problem Statement
Build a complete, production-ready OpenEnv environment for a hackathon. SQL Query Review & Data Quality domain where an AI agent reviews incoming SQL queries for correctness, security, and performance.

## Architecture
- **Standalone Project**: `/app/sql_review_env/` — complete HuggingFace Spaces deployable project
  - FastAPI server on port 7860 with OpenEnv spec endpoints (/health, /reset, /step, /state, /tasks)
  - 56 synthetic SQL queries across 4 categories (safe, injection, performance, logic bugs)
  - 3 tasks with deterministic graders (easy/medium/hard)
  - Baseline inference script using OpenAI client
  - Dockerfile with HEALTHCHECK
  - openenv.yaml spec file
  - README.md with HF Space frontmatter

- **Web Dashboard**: React frontend + FastAPI backend (existing Emergent platform)
  - Task selection screen with 3 difficulty levels
  - Interactive SQL review panel with syntax highlighting
  - Action buttons (approve/reject/request_changes/skip)
  - Real-time reward and score display
  - Session statistics and step history

## User Personas
- Hackathon participants building AI agent environments
- Data engineers reviewing SQL queries
- ML/RL researchers training code-review agents

## Core Requirements (Static)
- [x] OpenEnv spec compliance (step/reset/state endpoints)
- [x] 3 tasks with increasing difficulty
- [x] Deterministic graders producing varied scores 0.0-1.0
- [x] 50+ synthetic SQL queries with seeded random
- [x] Ground truth hidden from agent observations
- [x] Baseline inference script with exact log format
- [x] Dockerfile builds and runs
- [x] README with HF Space frontmatter

## What's Been Implemented (2026-04-02)
- Complete standalone OpenEnv project (11 files)
- Web dashboard with task selection and interactive review
- All API endpoints tested and working
- Grader variance verified across all tasks
- SQL syntax highlighting in frontend

## Prioritized Backlog
### P0 (Critical)
- All done

### P1 (Important)
- Deploy to HuggingFace Spaces
- Run `openenv validate` to confirm spec compliance
- Test inference.py with actual HF_TOKEN

### P2 (Nice to Have)
- Add more query templates to expand pool beyond 56
- Add difficulty-adaptive query selection
- Add a leaderboard to track agent performance
- Add export functionality for session data

## Next Tasks
1. Deploy to HuggingFace Spaces
2. Replace "your-hf-username" in openenv.yaml with actual HF username
3. Run `openenv validate` pre-submission check
4. Test inference.py end-to-end with HF_TOKEN
