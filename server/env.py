"""Core SQL Review Environment — state management and step logic.

Implements the OpenEnv interface:
  - reset() → observation
  - step(action) → (observation, reward, done, info)
  - state() → full internal state dict
"""

from typing import Dict, List, Optional, Tuple
from .models import SQLQuery, SQLQueryPublic, SQLObservation, SQLAction
from .data import get_queries_for_task
from .tasks import (
    get_task, TASK_DEFINITIONS,
    compute_step_reward_single,
    compute_step_reward_batch,
    compute_step_reward_pipeline,
    grade_single_review,
    grade_batch_review,
    grade_pipeline_review,
)


class SQLReviewEnv:
    """OpenEnv-compliant SQL Review Environment."""

    def __init__(self, task_id: str = "single_review"):
        self.task_id = task_id
        task_def = get_task(task_id)
        if task_def is None:
            task_def = get_task("single_review")
            self.task_id = "single_review"
        self.max_steps = task_def.max_steps
        self.current_step = 0
        self.queries: Dict[str, SQLQuery] = {}
        self.reviewed_ids: set = set()
        self.skipped_ids: set = set()
        self.action_history: List[Dict] = []
        self.review_order: List[str] = []
        self.actions_by_query: Dict[str, SQLAction] = {}
        self.session_stats = {"correct": 0, "wrong": 0, "skipped": 0, "total_reward": 0.0}
        self.last_action_result = "Environment initialized"
        self.done = False
        self._batch_index = 0  # For pipeline_review batched delivery

    def reset(self) -> SQLObservation:
        """Full clean state reset. Returns initial observation."""
        self.current_step = 0
        self.reviewed_ids = set()
        self.skipped_ids = set()
        self.action_history = []
        self.review_order = []
        self.actions_by_query = {}
        self.session_stats = {"correct": 0, "wrong": 0, "skipped": 0, "total_reward": 0.0}
        self.last_action_result = "Environment reset. Begin reviewing queries."
        self.done = False
        self._batch_index = 0

        # Load queries for this task
        query_list = get_queries_for_task(self.task_id)
        self.queries = {q.query_id: q for q in query_list}

        return self._get_observation()

    def step(self, action: SQLAction) -> Tuple[SQLObservation, float, bool, dict]:
        """Process one agent action. Returns (observation, reward, done, info)."""
        info: dict = {}

        if self.done:
            return self._get_observation(), 0.0, True, {"error": "Episode already done"}

        self.current_step += 1

        # Validate query_id
        if action.query_id not in self.queries:
            self.last_action_result = f"Query {action.query_id} not found"
            reward = 0.0
            info["error"] = "query not found"
            self.done = self._check_done()
            return self._get_observation(), reward, self.done, info

        query = self.queries[action.query_id]

        # Validate action_type
        valid_actions = {"review", "approve", "reject", "request_changes", "skip"}
        if action.action_type not in valid_actions:
            self.last_action_result = f"Invalid action type: {action.action_type}"
            info["error"] = "invalid action"
            self.done = self._check_done()
            return self._get_observation(), 0.0, self.done, info

        # Record action
        self.action_history.append({
            "step": self.current_step,
            "query_id": action.query_id,
            "action_type": action.action_type,
            "verdict": action.verdict,
        })

        # Compute step reward based on task
        reward = self._compute_reward(action, query)
        self.session_stats["total_reward"] += reward

        # Handle skip
        if action.action_type == "skip":
            self.skipped_ids.add(action.query_id)
            self.session_stats["skipped"] += 1
            self.last_action_result = f"Skipped query {action.query_id}"
        else:
            # Determine effective verdict
            verdict = action.verdict
            if verdict is None and action.action_type in ("approve", "reject"):
                verdict = action.action_type

            # Track review
            if action.query_id not in self.reviewed_ids:
                self.reviewed_ids.add(action.query_id)
                self.review_order.append(action.query_id)

            # Store the action for final grading
            self.actions_by_query[action.query_id] = action

            # Track correctness
            if verdict == query.correct_verdict:
                self.session_stats["correct"] += 1
                self.last_action_result = f"Reviewed {action.query_id}: verdict={verdict} (recorded)"
            elif verdict is not None:
                self.session_stats["wrong"] += 1
                self.last_action_result = f"Reviewed {action.query_id}: verdict={verdict} (recorded)"
            else:
                self.last_action_result = f"Action on {action.query_id}: {action.action_type} (no verdict)"

        # Check done
        self.done = self._check_done()

        # If done, compute final grade info
        if self.done:
            final_grade = self._compute_final_grade()
            info["final_grade"] = final_grade
            info["episode_complete"] = True

        info["step"] = self.current_step
        info["reviewed"] = len(self.reviewed_ids)
        info["pending"] = len(self.queries) - len(self.reviewed_ids)

        return self._get_observation(), reward, self.done, info

    def state(self) -> dict:
        """Full internal state including ground truth (for /state endpoint)."""
        return {
            "task_id": self.task_id,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "done": self.done,
            "queries": {qid: q.model_dump() for qid, q in self.queries.items()},
            "reviewed_ids": list(self.reviewed_ids),
            "skipped_ids": list(self.skipped_ids),
            "review_order": self.review_order,
            "action_history": self.action_history,
            "session_stats": self.session_stats,
            "last_action_result": self.last_action_result,
        }

    def _compute_reward(self, action: SQLAction, query: SQLQuery) -> float:
        """Compute dense per-step reward based on task type."""
        try:
            if self.task_id == "single_review":
                return compute_step_reward_single(action, query)
            elif self.task_id == "batch_review":
                return compute_step_reward_batch(
                    action, query, self.reviewed_ids,
                    len(self.queries), self.current_step, self.max_steps
                )
            elif self.task_id == "pipeline_review":
                return compute_step_reward_pipeline(
                    action, query, self.reviewed_ids,
                    self.review_order, self.queries
                )
            else:
                return compute_step_reward_single(action, query)
        except Exception:
            return 0.0

    def _check_done(self) -> bool:
        """Episode ends when all queries reviewed OR max_steps reached."""
        if self.current_step >= self.max_steps:
            return True
        if len(self.reviewed_ids) + len(self.skipped_ids) >= len(self.queries):
            return True
        return False

    def _get_observation(self) -> SQLObservation:
        """Build observation with ground truth stripped."""
        # For pipeline_review, deliver queries in batches
        if self.task_id == "pipeline_review":
            visible_queries = self._get_pipeline_batch()
        else:
            visible_queries = list(self.queries.values())

        public_queries = [
            SQLQueryPublic(
                query_id=q.query_id,
                sql=q.sql,
                submitted_by=q.submitted_by,
                database=q.database,
                query_type=q.query_type,
                is_urgent=q.is_urgent,
            )
            for q in visible_queries
        ]

        return SQLObservation(
            queries=public_queries,
            current_step=self.current_step,
            task_id=self.task_id,
            reviewed_count=len(self.reviewed_ids),
            pending_count=len(self.queries) - len(self.reviewed_ids),
            last_action_result=self.last_action_result,
            session_stats=self.session_stats,
            done=self.done,
        )

    def _get_pipeline_batch(self) -> List[SQLQuery]:
        """For pipeline_review: deliver queries in batches of 5."""
        all_q = list(self.queries.values())
        batch_size = 5
        # Determine which batch to show based on reviewed count
        reviewed = len(self.reviewed_ids) + len(self.skipped_ids)
        if reviewed < 5:
            return all_q[:5]
        elif reviewed < 10:
            return all_q[:10]
        else:
            return all_q  # All 15 visible

    def _compute_final_grade(self) -> dict:
        """Compute final episode grade."""
        try:
            if self.task_id == "single_review":
                if self.actions_by_query:
                    qid = list(self.queries.keys())[0]
                    if qid in self.actions_by_query:
                        result = grade_single_review(self.actions_by_query[qid], self.queries[qid])
                        return result.model_dump()
                return {"value": 0.0, "reason": "No review performed"}

            elif self.task_id == "batch_review":
                result = grade_batch_review(
                    self.actions_by_query, self.queries,
                    self.reviewed_ids, self.current_step, self.max_steps
                )
                return result.model_dump()

            elif self.task_id == "pipeline_review":
                result = grade_pipeline_review(
                    self.actions_by_query, self.queries,
                    self.reviewed_ids, self.review_order, self.skipped_ids
                )
                return result.model_dump()

            return {"value": 0.0, "reason": "Unknown task"}
        except Exception as e:
            return {"value": 0.0, "reason": f"Grading error: {str(e)}"}
