"""FastAPI backend serving the SQL Review OpenEnv environment.

Exposes the OpenEnv API at /api/env/* and also serves a dashboard API.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path for sql_review_env imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import logging
import traceback

from sql_review_env.server.env import SQLReviewEnv
from sql_review_env.server.models import SQLAction
from sql_review_env.server.tasks import get_task_definitions
from sql_review_env.server.data import get_all_queries

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI(title="SQL Review Environment Dashboard")

api_router = APIRouter(prefix="/api")

# ── State ─────────────────────────────────────────────────
class AppState:
    env = None

app_state = AppState()


# ── Health ────────────────────────────────────────────────
@api_router.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ── OpenEnv Endpoints ─────────────────────────────────────

@api_router.post("/env/reset")
async def env_reset(request: Request):
    """Reset environment with optional task_id."""
    try:
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass
        task_id = body.get("task_id", "single_review") if isinstance(body, dict) else "single_review"
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
        return JSONResponse(status_code=200, content={"error": str(e)})


@api_router.post("/env/step")
async def env_step(request: Request):
    """Execute one agent action."""
    try:
        if app_state.env is None:
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
        return JSONResponse(status_code=200, content={
            "observation": {"queries": [], "current_step": 0, "task_id": "",
                           "reviewed_count": 0, "pending_count": 0,
                           "last_action_result": f"Error: {str(e)}",
                           "session_stats": {}, "done": False},
            "reward": 0.0, "done": False, "info": {"error": str(e)}
        })


@api_router.get("/env/state")
async def env_state():
    """Full internal state including ground truth."""
    if app_state.env is None:
        return {"error": "No active environment. Call /env/reset first."}
    return app_state.env.state()


@api_router.get("/env/tasks")
async def env_tasks():
    """List all task definitions."""
    return [t.model_dump() for t in get_task_definitions()]


@api_router.get("/env/queries")
async def env_queries():
    """List all queries in the pool (for dashboard display)."""
    queries = get_all_queries()
    return {
        "total": len(queries),
        "categories": {
            "safe": len([q for q in queries if q.correct_verdict == "approve"]),
            "injection": len([q for q in queries if q.has_injection_risk]),
            "performance": len([q for q in queries if q.has_performance_issue]),
            "logic_bug": len([q for q in queries if q.has_logic_bug]),
        }
    }


# ── Include router ────────────────────────────────────────
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
