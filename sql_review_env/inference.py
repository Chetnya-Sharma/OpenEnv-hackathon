"""Baseline inference script for SQL Review Environment.

Runs all 3 tasks against the environment using an LLM agent.
Uses exact [START]/[STEP]/[END] log format required by OpenEnv judges.

Environment variables (exact names required):
  API_BASE_URL  — LLM API endpoint (default: HF router)
  MODEL_NAME    — model identifier
  HF_TOKEN      — HuggingFace API key
  ENV_BASE_URL  — environment server URL
"""

import asyncio
import os
import json
import textwrap
from typing import List
from openai import OpenAI
import httpx

# ── env vars (EXACT names required by judges) ──────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK = "sql-review-env"

TASKS = [
    {"id": "single_review", "max_steps": 5, "max_reward": 1.5},
    {"id": "batch_review", "max_steps": 25, "max_reward": 10.0},
    {"id": "pipeline_review", "max_steps": 50, "max_reward": 18.0},
]


# ── EXACT log format — field names and order are evaluated by judges ──
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error) -> None:
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


SYSTEM_PROMPT = textwrap.dedent("""
    You are a senior data engineer reviewing SQL queries for a production database.
    For each query, you must:
    1. Identify any SQL injection risks, performance issues, or logic bugs
    2. Decide whether to approve or reject the query
    3. If rejecting, provide a specific suggested fix

    Respond ONLY with a valid JSON object in this exact format:
    {
      "action_type": "review",
      "query_id": "<id>",
      "verdict": "approve" or "reject",
      "issues_found": ["sql_injection", "performance", "logic_bug", "missing_index", "n_plus_one", "no_issues"],
      "suggested_fix": "<rewritten SQL or empty string>",
      "confidence": 0.0 to 1.0
    }
    Only include actual issues found in issues_found array.
    If no issues, use ["no_issues"].
""").strip()


async def call_env(method: str, path: str, body: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "POST":
            r = await client.post(f"{ENV_BASE_URL}{path}", json=body or {})
        else:
            r = await client.get(f"{ENV_BASE_URL}{path}")
        r.raise_for_status()
        return r.json()


def get_agent_action(client: OpenAI, observation: dict, history: List[str]) -> dict:
    """Use LLM to decide action for the next pending query."""
    queries = observation.get("queries", [])
    reviewed_qids = {h.split(":")[0] for h in history if ":" in h}
    pending_queries = [q for q in queries if q["query_id"] not in reviewed_qids]

    if not pending_queries:
        pending_queries = queries[:1]  # fallback

    query = pending_queries[0]
    urgent_flag = " [URGENT - PRIORITY]" if query.get("is_urgent", False) else ""

    user_prompt = f"""
Review this SQL query:{urgent_flag}
Query ID: {query['query_id']}
SQL: {query['sql']}
Database: {query['database']}
Query Type: {query['query_type']}
Step: {observation['current_step']}
Already reviewed: {observation.get('reviewed_count', 0)}
Pending: {observation.get('pending_count', 0)}

Analyze for SQL injection risks, performance issues, and logic bugs.
Respond with JSON action only.
"""
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt.strip()},
            ],
            temperature=0.1,
            max_tokens=300,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        # Strip markdown fences if present
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[DEBUG] LLM error: {e}", flush=True)
        # Safe fallback action
        return {
            "action_type": "review",
            "query_id": query["query_id"],
            "verdict": "reject",
            "issues_found": ["no_issues"],
            "suggested_fix": "",
            "confidence": 0.5,
        }


async def run_task(task: dict) -> float:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    task_id = task["id"]
    max_steps = task["max_steps"]
    max_reward = task["max_reward"]

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    history: List[str] = []

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await call_env("POST", "/reset", {"task_id": task_id})
        observation = result["observation"]

        for step in range(1, max_steps + 1):
            if observation.get("done", False):
                break

            action_dict = get_agent_action(client, observation, history)
            error = None

            try:
                step_result = await call_env("POST", "/step", action_dict)
                observation = step_result["observation"]
                reward = float(step_result.get("reward", 0.0))
                done = bool(step_result.get("done", False))
                error = step_result.get("info", {}).get("error")
            except Exception as e:
                reward = 0.0
                done = False
                error = str(e)

            rewards.append(reward)
            steps_taken = step
            action_str = f"{action_dict.get('action_type', 'review')}({action_dict.get('query_id', '')})"
            history.append(
                f"{action_dict.get('query_id', '')}:{action_dict.get('verdict', '')}"
            )

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            if done:
                break

        score = sum(rewards) / max_reward if max_reward > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= 0.5

    except Exception as e:
        print(f"[DEBUG] Task error: {e}", flush=True)
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def main() -> None:
    for task in TASKS:
        await run_task(task)
        await asyncio.sleep(2)  # brief pause between tasks


if __name__ == "__main__":
    asyncio.run(main())
