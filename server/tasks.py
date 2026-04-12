"""Task definitions and deterministic graders for SQL Review Environment.

3 tasks with increasing difficulty:
  1. single_review (easy)  — 1 query, 5 steps
  2. batch_review (medium) — 8 queries, 25 steps
  3. pipeline_review (hard) — 15 queries (3 batches), 50 steps

All graders are 100% deterministic — no randomness, no LLM calls.
"""

from typing import Dict, List, Optional
from .models import SQLQuery, SQLAction, SQLReward, TaskDefinition


# ── Task Definitions ──────────────────────────────────────────────

TASK_DEFINITIONS: Dict[str, TaskDefinition] = {
    "single_review": TaskDefinition(
        id="single_review",
        name="Single Query Review",
        difficulty="easy",
        max_steps=5,
        description="Review one SQL query for correctness, security, and performance",
        num_queries=1,
        scoring_weights={"verdict": 0.6, "issue_detection": 0.4}
    ),
    "batch_review": TaskDefinition(
        id="batch_review",
        name="Batch Query Review",
        difficulty="medium",
        max_steps=25,
        description="Review 8 mixed SQL queries across all issue types",
        num_queries=8,
        scoring_weights={"verdict": 0.5, "issue_detection": 0.3, "fix_quality": 0.2}
    ),
    "pipeline_review": TaskDefinition(
        id="pipeline_review",
        name="Production Pipeline Review",
        difficulty="hard",
        max_steps=50,
        description="Review 15 queries with prioritization, urgent flags, and strict penalties",
        num_queries=15,
        scoring_weights={"verdict": 0.35, "issue_detection": 0.25, "fix_quality": 0.20, "priority_handling": 0.20}
    ),
}


def get_task_definitions() -> List[TaskDefinition]:
    """Return all task definitions."""
    return list(TASK_DEFINITIONS.values())


def get_task(task_id: str) -> Optional[TaskDefinition]:
    """Return a specific task definition."""
    return TASK_DEFINITIONS.get(task_id)


# ── Dense Step Reward Computation ─────────────────────────────────

def compute_step_reward_single(action: SQLAction, query: SQLQuery) -> float:
    """Dense step reward for single_review task."""
    reward = 0.0

    if action.action_type == "skip":
        return -0.05

    if action.action_type in ("review", "approve", "reject", "request_changes"):
        verdict = action.verdict
        if verdict is None and action.action_type in ("approve", "reject"):
            verdict = action.action_type

        # Verdict reward
        if verdict == query.correct_verdict:
            reward += 0.30
        elif verdict is not None:
            reward -= 0.10

        # Issue detection reward
        issues = action.issues_found or []
        if query.has_injection_risk and "sql_injection" in issues:
            reward += 0.15
        if query.has_performance_issue and "performance" in issues:
            reward += 0.15
        if query.has_logic_bug and "logic_bug" in issues:
            reward += 0.15

        # Penalty for claiming no issues when issues exist
        has_any_issue = query.has_injection_risk or query.has_performance_issue or query.has_logic_bug
        if has_any_issue and "no_issues" in issues:
            reward -= 0.05

        # Fix quality bonus
        if has_any_issue and action.suggested_fix and len(action.suggested_fix) > 20:
            reward += 0.10

    return reward


def compute_step_reward_batch(
    action: SQLAction,
    query: SQLQuery,
    reviewed_ids: set,
    total_queries: int,
    current_step: int,
    max_steps: int
) -> float:
    """Dense step reward for batch_review task."""
    reward = 0.0

    if action.action_type == "skip":
        return -0.10

    # Loop detection penalty
    if action.query_id in reviewed_ids:
        return -0.05

    if action.action_type in ("review", "approve", "reject", "request_changes"):
        verdict = action.verdict
        if verdict is None and action.action_type in ("approve", "reject"):
            verdict = action.action_type

        # Verdict reward
        if verdict == query.correct_verdict:
            reward += 0.15
        elif verdict is not None:
            reward -= 0.05

        # Issue detection
        issues = action.issues_found or []
        if query.has_injection_risk and "sql_injection" in issues:
            reward += 0.10
        if query.has_performance_issue and "performance" in issues:
            reward += 0.10
        if query.has_logic_bug and "logic_bug" in issues:
            reward += 0.10

        # Fix provided for rejected query
        if query.correct_verdict == "reject" and action.suggested_fix and len(action.suggested_fix) > 10:
            reward += 0.05

    return reward


def compute_step_reward_pipeline(
    action: SQLAction,
    query: SQLQuery,
    reviewed_ids: set,
    review_order: List[str],
    all_queries: Dict[str, SQLQuery],
) -> float:
    """Dense step reward for pipeline_review task."""
    reward = 0.0

    if action.action_type == "skip":
        return -0.10

    # Loop detection penalty
    if action.query_id in reviewed_ids:
        return -0.10

    if action.action_type in ("review", "approve", "reject", "request_changes"):
        verdict = action.verdict
        if verdict is None and action.action_type in ("approve", "reject"):
            verdict = action.action_type

        # Verdict reward
        if verdict == query.correct_verdict:
            reward += 0.15
        elif verdict is not None:
            reward -= 0.05

        # Issue detection
        issues = action.issues_found or []
        if query.has_injection_risk and "sql_injection" in issues:
            reward += 0.10
        if query.has_performance_issue and "performance" in issues:
            reward += 0.10
        if query.has_logic_bug and "logic_bug" in issues:
            reward += 0.10

        # Heavy penalty: approving urgent query with critical issues
        has_critical = query.has_injection_risk or query.has_logic_bug
        if query.is_urgent and has_critical and verdict == "approve":
            reward -= 0.20

        # Penalty: empty fix when rejecting
        if verdict == "reject" and (not action.suggested_fix or len(action.suggested_fix.strip()) == 0):
            reward -= 0.15

        # Fix quality bonus
        if verdict == "reject" and action.suggested_fix and len(action.suggested_fix) >= 30:
            reward += 0.05

    return reward


# ── Final Episode Graders ─────────────────────────────────────────

def grade_single_review(action: SQLAction, query: SQLQuery) -> SQLReward:
    """Final grader for single_review. Returns 0.0-1.0."""
    verdict = action.verdict
    if verdict is None and action.action_type in ("approve", "reject"):
        verdict = action.action_type

    verdict_score = 1.0 if verdict == query.correct_verdict else 0.0

    issue_score = 0.0
    issues = action.issues_found or []
    if query.has_injection_risk and "sql_injection" in issues:
        issue_score += 0.33
    if query.has_performance_issue and "performance" in issues:
        issue_score += 0.33
    if query.has_logic_bug and "logic_bug" in issues:
        issue_score += 0.34

    # If no issues exist and agent correctly says no_issues
    if not (query.has_injection_risk or query.has_performance_issue or query.has_logic_bug):
        if "no_issues" in issues:
            issue_score = 1.0

    final = (verdict_score * 0.6) + (issue_score * 0.4)
    final = max(0.0, min(1.0, final))

    return SQLReward(
        value=final,
        reason=f"Verdict {'correct' if verdict_score > 0 else 'wrong'}, issue detection {issue_score:.2f}",
        partial_progress=final,
        breakdown={"verdict": verdict_score * 0.6, "issue_detection": issue_score * 0.4}
    )


def grade_batch_review(
    actions: Dict[str, SQLAction],
    queries: Dict[str, SQLQuery],
    reviewed_ids: set,
    total_steps: int,
    max_steps: int,
) -> SQLReward:
    """Final grader for batch_review. Returns 0.0-1.0."""
    total_queries = len(queries)
    correct_verdicts = 0
    total_issues = 0
    correctly_identified = 0
    fix_scores: List[float] = []

    for qid, query in queries.items():
        # Count ground truth issues
        if query.has_injection_risk:
            total_issues += 1
        if query.has_performance_issue:
            total_issues += 1
        if query.has_logic_bug:
            total_issues += 1

        if qid in actions:
            action = actions[qid]
            verdict = action.verdict
            if verdict is None and action.action_type in ("approve", "reject"):
                verdict = action.action_type

            if verdict == query.correct_verdict:
                correct_verdicts += 1

            issues = action.issues_found or []
            if query.has_injection_risk and "sql_injection" in issues:
                correctly_identified += 1
            if query.has_performance_issue and "performance" in issues:
                correctly_identified += 1
            if query.has_logic_bug and "logic_bug" in issues:
                correctly_identified += 1

            # Fix quality for rejected queries
            if query.correct_verdict == "reject":
                fix = action.suggested_fix or ""
                if len(fix) == 0:
                    fix_scores.append(0.0)
                elif len(fix) < 30:
                    fix_scores.append(0.5)
                else:
                    fix_scores.append(1.0)

    verdict_accuracy = correct_verdicts / total_queries if total_queries > 0 else 0.0
    issue_detection_rate = correctly_identified / total_issues if total_issues > 0 else 0.0
    fix_quality = sum(fix_scores) / len(fix_scores) if fix_scores else 0.0

    # Completion bonus
    completion_bonus = 0.0
    if len(reviewed_ids) >= total_queries and total_steps <= max_steps:
        completion_bonus = 0.15

    base = (verdict_accuracy * 0.5) + (issue_detection_rate * 0.3) + (fix_quality * 0.2)
    final = max(0.0, min(1.0, base + completion_bonus))

    return SQLReward(
        value=final,
        reason=f"Verdict acc {verdict_accuracy:.2f}, issue detect {issue_detection_rate:.2f}, fix quality {fix_quality:.2f}",
        partial_progress=base,
        breakdown={
            "verdict": verdict_accuracy * 0.5,
            "issue_detection": issue_detection_rate * 0.3,
            "fix_quality": fix_quality * 0.2,
            "completion_bonus": completion_bonus
        }
    )


def grade_pipeline_review(
    actions: Dict[str, SQLAction],
    queries: Dict[str, SQLQuery],
    reviewed_ids: set,
    review_order: List[str],
    skipped_ids: set,
) -> SQLReward:
    """Final grader for pipeline_review. Returns 0.0-1.0."""
    total_queries = len(queries)
    correct_verdicts = 0
    total_issues = 0
    correctly_identified = 0
    fix_scores: List[float] = []
    penalties = 0.0

    # Priority handling: fraction of urgent queries reviewed before non-urgent
    urgent_ids = {qid for qid, q in queries.items() if q.is_urgent}
    normal_ids = {qid for qid, q in queries.items() if not q.is_urgent}

    # Determine priority score from review order
    first_normal_idx = len(review_order)  # default: all urgent reviewed first
    for i, qid in enumerate(review_order):
        if qid in normal_ids:
            first_normal_idx = i
            break

    urgent_reviewed_before_normal = 0
    for i, qid in enumerate(review_order):
        if qid in urgent_ids and i < first_normal_idx:
            urgent_reviewed_before_normal += 1
        elif qid in urgent_ids:
            # Count urgent queries reviewed at any point
            urgent_reviewed_before_normal += 0.5  # partial credit

    priority_score = urgent_reviewed_before_normal / len(urgent_ids) if urgent_ids else 1.0
    priority_score = min(1.0, priority_score)

    for qid, query in queries.items():
        if query.has_injection_risk:
            total_issues += 1
        if query.has_performance_issue:
            total_issues += 1
        if query.has_logic_bug:
            total_issues += 1

        if qid in actions:
            action = actions[qid]
            verdict = action.verdict
            if verdict is None and action.action_type in ("approve", "reject"):
                verdict = action.action_type

            if verdict == query.correct_verdict:
                correct_verdicts += 1

            issues = action.issues_found or []
            if query.has_injection_risk and "sql_injection" in issues:
                correctly_identified += 1
            if query.has_performance_issue and "performance" in issues:
                correctly_identified += 1
            if query.has_logic_bug and "logic_bug" in issues:
                correctly_identified += 1

            # Fix quality
            if query.correct_verdict == "reject":
                fix = action.suggested_fix or ""
                if len(fix) == 0:
                    fix_scores.append(0.0)
                elif len(fix) < 30:
                    fix_scores.append(0.5)
                else:
                    fix_scores.append(1.0)

            # Penalty: approving urgent query with critical issues
            has_critical = query.has_injection_risk or query.has_logic_bug
            if query.is_urgent and has_critical and verdict == "approve":
                penalties += 0.20

            # Penalty: empty fix on reject
            if verdict == "reject" and (not action.suggested_fix or len(action.suggested_fix.strip()) == 0):
                penalties += 0.15

    # Penalty: skipped queries
    penalties += len(skipped_ids) * 0.10

    verdict_accuracy = correct_verdicts / total_queries if total_queries > 0 else 0.0
    issue_detection_rate = correctly_identified / total_issues if total_issues > 0 else 0.0
    fix_quality = sum(fix_scores) / len(fix_scores) if fix_scores else 0.0

    base = (
        verdict_accuracy * 0.35
        + issue_detection_rate * 0.25
        + fix_quality * 0.20
        + priority_score * 0.20
    )

    final = max(0.0, min(1.0, base - penalties))

    return SQLReward(
        value=final,
        reason=f"Verdict {verdict_accuracy:.2f}, issues {issue_detection_rate:.2f}, fixes {fix_quality:.2f}, priority {priority_score:.2f}, penalties {penalties:.2f}",
        partial_progress=base,
        breakdown={
            "verdict": verdict_accuracy * 0.35,
            "issue_detection": issue_detection_rate * 0.25,
            "fix_quality": fix_quality * 0.20,
            "priority_handling": priority_score * 0.20,
            "penalties": -penalties
        }
    )
