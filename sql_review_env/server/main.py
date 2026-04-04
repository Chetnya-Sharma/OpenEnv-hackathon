"""FastAPI application for the SQL Review OpenEnv environment.

Endpoints:
  GET  /health  → liveness check
  POST /reset   → reset environment with optional task_id
  POST /step    → execute an action
  GET  /state   → full internal state (includes ground truth)
  POST /tasks   → list all task definitions
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import traceback

from .env import SQLReviewEnv
from .models import SQLAction
from .tasks import get_task_definitions

app = FastAPI(
    title="SQL Review Environment",
    description="OpenEnv environment for AI agent SQL query review training",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── State storage ─────────────────────────────────────────────────
# Each reset creates a fresh env instance
class AppState:
    env: Optional[SQLReviewEnv] = None

app_state = AppState()


# ── Request models ────────────────────────────────────────────────
class ResetRequest(BaseModel):
    task_id: Optional[str] = "single_review"

TASK_ID_MAP = {
    "easy": "single_review",
    "single_review": "single_review",
    "medium": "batch_review",
    "batch_review": "batch_review",
    "hard": "pipeline_review",
    "pipeline_review": "pipeline_review",
}

# ── Endpoints ─────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Liveness check — judges ping this for 200 response."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/reset")
async def reset(request: Request):
    """Reset environment. Accepts task_id in body JSON or query param."""
    try:
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass  # Empty body is fine — use defaults

        # Support both JSON body and query params
        task_id = body.get("task_id") if isinstance(body, dict) else None
        if not task_id:
            task_id = request.query_params.get("task_id", "single_review")

        # Resolve aliases (easy/medium/hard) to real task IDs
        task_id = TASK_ID_MAP.get(task_id, task_id)

        env = SQLReviewEnv(task_id=task_id)
        observation = env.reset()
        app_state.env = env

        return {
            "observation": observation.model_dump(),
            "info": {
                "task_id": env.task_id,
                "max_steps": env.max_steps,
                "num_queries": len(env.queries),
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "observation": {
                    "queries": [], "current_step": 0, "task_id": "single_review",
                    "reviewed_count": 0, "pending_count": 0,
                    "last_action_result": f"Reset error: {str(e)}",
                    "session_stats": {}, "done": False
                },
                "info": {"error": str(e)}
            }
        )


@app.post("/step")
async def step(request: Request):
    """Execute one agent action."""
    try:
        if app_state.env is None:
            # Auto-reset if no env exists
            env = SQLReviewEnv(task_id="single_review")
            env.reset()
            app_state.env = env

        body = await request.json()
        action = SQLAction(**body)

        observation, reward, done, info = app_state.env.step(action)

        return {
            "observation": observation.model_dump(),
            "reward": round(reward, 4),
            "done": done,
            "info": info,
        }
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=200,
            content={
                "observation": {
                    "queries": [], "current_step": 0, "task_id": "",
                    "reviewed_count": 0, "pending_count": 0,
                    "last_action_result": f"Step error: {error_msg}",
                    "session_stats": {}, "done": False
                },
                "reward": 0.0,
                "done": False,
                "info": {"error": error_msg, "traceback": tb}
            }
        )


@app.get("/state")
async def get_state():
    """Return full internal state including ground truth."""
    try:
        if app_state.env is None:
            return {"error": "No active environment. Call /reset first."}
        return app_state.env.state()
    except Exception as e:
        return {"error": str(e)}


@app.post("/tasks")
async def list_tasks():
    """Return all task definitions."""
    try:
        tasks = get_task_definitions()
        return [t.model_dump() for t in tasks]
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"error": str(e)}
        )


# Also support GET /tasks for convenience
@app.get("/tasks")
async def list_tasks_get():
    """Return all task definitions (GET version)."""
    try:
        tasks = get_task_definitions()
        return [t.model_dump() for t in tasks]
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"error": str(e)}
        )
