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
        scoring_weights={"verdict": 0.50, "issue_detection": 0.30, "reasoning": 0.10, "fix_quality": 0.10}
    ),
    "batch_review": TaskDefinition(
        id="batch_review",
        name="Batch Query Review",
        difficulty="medium",
        max_steps=25,
        description="Review 8 mixed SQL queries including adversarial edge cases",
        num_queries=8,
        scoring_weights={"verdict": 0.40, "issue_detection": 0.25, "reasoning": 0.10, "fix_quality": 0.15, "efficiency": 0.10}
    ),
    "pipeline_review": TaskDefinition(
        id="pipeline_review",
        name="Production Pipeline Review",
        difficulty="hard",
        max_steps=50,
        description="Review 15 queries with prioritization, urgent flags, adversarial queries, and strict penalties",
        num_queries=15,
        scoring_weights={"verdict": 0.30, "issue_detection": 0.20, "reasoning": 0.10, "fix_quality": 0.15, "priority_handling": 0.15, "efficiency": 0.10}
    ),
}


def get_task_definitions() -> List[TaskDefinition]:
    """Return all task definitions."""
    return list(TASK_DEFINITIONS.values())


def get_task(task_id: str) -> Optional[TaskDefinition]:
    """Return a specific task definition."""
    return TASK_DEFINITIONS.get(task_id)


# ── Reasoning Quality Scorer ─────────────────────────────────────

def _score_reasoning(reasoning: Optional[str], query: SQLQuery) -> float:
    """Score reasoning quality by checking for relevant keyword mentions.
    Returns 0.0-1.0 based on how many expected keywords appear."""
    if not reasoning or len(reasoning.strip()) < 10:
        return 0.0
    reasoning_lower = reasoning.lower()
    keywords = query.reasoning_keywords
    if not keywords:
        # No expected keywords defined — give credit for non-trivial reasoning
        return 0.5 if len(reasoning.strip()) > 30 else 0.2
    matches = sum(1 for kw in keywords if kw.lower() in reasoning_lower)
    return min(1.0, matches / max(1, len(keywords) * 0.5))  # Need 50% of keywords for full score


def _score_confidence(confidence: Optional[float], was_correct: bool) -> float:
    """Brier-style score: reward calibrated confidence.
    High confidence + correct = 1.0, high confidence + wrong = 0.0."""
    if confidence is None:
        return 0.5  # Neutral if not provided
    if was_correct:
        return confidence  # Higher confidence on correct = better
    else:
        return 1.0 - confidence  # Lower confidence on wrong = less bad


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

        # Reasoning bonus
        reasoning_score = _score_reasoning(action.reasoning, query)
        reward += reasoning_score * 0.08

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

        # Reasoning bonus
        reasoning_score = _score_reasoning(action.reasoning, query)
        reward += reasoning_score * 0.05

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

        # Reasoning bonus
        reasoning_score = _score_reasoning(action.reasoning, query)
        reward += reasoning_score * 0.05

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

    # Reasoning quality
    reasoning_score = _score_reasoning(action.reasoning, query)

    # Fix quality
    fix_score = 0.0
    has_any_issue = query.has_injection_risk or query.has_performance_issue or query.has_logic_bug
    if has_any_issue and action.suggested_fix:
        if len(action.suggested_fix) >= 30:
            fix_score = 1.0
        elif len(action.suggested_fix) >= 10:
            fix_score = 0.5
    elif not has_any_issue:
        fix_score = 1.0  # No fix needed for safe queries

    final = (verdict_score * 0.50) + (issue_score * 0.30) + (reasoning_score * 0.10) + (fix_score * 0.10)
    final = max(0.0, min(1.0, final))

    return SQLReward(
        value=final,
        reason=f"Verdict {'correct' if verdict_score > 0 else 'wrong'}, issues {issue_score:.2f}, reasoning {reasoning_score:.2f}, fix {fix_score:.2f}",
        partial_progress=final,
        breakdown={
            "verdict": verdict_score * 0.50,
            "issue_detection": issue_score * 0.30,
            "reasoning": reasoning_score * 0.10,
            "fix_quality": fix_score * 0.10,
        }
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
    reasoning_scores: List[float] = []

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

            # Reasoning quality
            reasoning_scores.append(_score_reasoning(action.reasoning, query))

    verdict_accuracy = correct_verdicts / total_queries if total_queries > 0 else 0.0
    issue_detection_rate = correctly_identified / total_issues if total_issues > 0 else 0.0
    fix_quality = sum(fix_scores) / len(fix_scores) if fix_scores else 0.0
    avg_reasoning = sum(reasoning_scores) / len(reasoning_scores) if reasoning_scores else 0.0

    # Efficiency bonus: reviewed all queries in fewer steps
    efficiency_score = 0.0
    if len(reviewed_ids) >= total_queries:
        if total_steps <= total_queries + 2:  # Near-optimal
            efficiency_score = 1.0
        elif total_steps <= total_queries * 2:
            efficiency_score = 0.7
        elif total_steps <= max_steps:
            efficiency_score = 0.4

    base = (
        verdict_accuracy * 0.40
        + issue_detection_rate * 0.25
        + avg_reasoning * 0.10
        + fix_quality * 0.15
        + efficiency_score * 0.10
    )
    final = max(0.0, min(1.0, base))

    return SQLReward(
        value=final,
        reason=f"Verdict acc {verdict_accuracy:.2f}, issues {issue_detection_rate:.2f}, reasoning {avg_reasoning:.2f}, fixes {fix_quality:.2f}, efficiency {efficiency_score:.2f}",
        partial_progress=base,
        breakdown={
            "verdict": verdict_accuracy * 0.40,
            "issue_detection": issue_detection_rate * 0.25,
            "reasoning": avg_reasoning * 0.10,
            "fix_quality": fix_quality * 0.15,
            "efficiency": efficiency_score * 0.10,
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
    reasoning_scores: List[float] = []
    penalties = 0.0

    # Priority handling: fraction of urgent queries reviewed before non-urgent
    urgent_ids = {qid for qid, q in queries.items() if q.is_urgent}
    normal_ids = {qid for qid, q in queries.items() if not q.is_urgent}

    # Determine priority score from review order
    first_normal_idx = len(review_order)
    for i, qid in enumerate(review_order):
        if qid in normal_ids:
            first_normal_idx = i
            break

    urgent_reviewed_before_normal = 0
    for i, qid in enumerate(review_order):
        if qid in urgent_ids and i < first_normal_idx:
            urgent_reviewed_before_normal += 1
        elif qid in urgent_ids:
            urgent_reviewed_before_normal += 0.5

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

            # Reasoning quality
            reasoning_scores.append(_score_reasoning(action.reasoning, query))

            # Penalty: approving urgent query with critical issues
            has_critical = query.has_injection_risk or query.has_logic_bug
            if query.is_urgent and has_critical and verdict == "approve":
                penalties += 0.15

            # Penalty: empty fix on reject
            if verdict == "reject" and (not action.suggested_fix or len(action.suggested_fix.strip()) == 0):
                penalties += 0.08

    # Penalty: skipped queries
    penalties += len(skipped_ids) * 0.05

    verdict_accuracy = correct_verdicts / total_queries if total_queries > 0 else 0.0
    issue_detection_rate = correctly_identified / total_issues if total_issues > 0 else 0.0
    fix_quality = sum(fix_scores) / len(fix_scores) if fix_scores else 0.0
    avg_reasoning = sum(reasoning_scores) / len(reasoning_scores) if reasoning_scores else 0.0

    # Efficiency: reviewed more queries = better
    review_ratio = len(reviewed_ids) / total_queries if total_queries > 0 else 0.0
    efficiency_score = review_ratio  # 1.0 if all reviewed

    base = (
        verdict_accuracy * 0.30
        + issue_detection_rate * 0.20
        + avg_reasoning * 0.10
        + fix_quality * 0.15
        + priority_score * 0.15
        + efficiency_score * 0.10
    )

    final = max(0.0, min(1.0, base - penalties))

    return SQLReward(
        value=final,
        reason=f"Verdict {verdict_accuracy:.2f}, issues {issue_detection_rate:.2f}, reasoning {avg_reasoning:.2f}, fixes {fix_quality:.2f}, priority {priority_score:.2f}, efficiency {efficiency_score:.2f}, penalties {penalties:.2f}",
        partial_progress=base,
        breakdown={
            "verdict": verdict_accuracy * 0.30,
            "issue_detection": issue_detection_rate * 0.20,
            "reasoning": avg_reasoning * 0.10,
            "fix_quality": fix_quality * 0.15,
            "priority_handling": priority_score * 0.15,
            "efficiency": efficiency_score * 0.10,
            "penalties": -penalties,
        }
    )
