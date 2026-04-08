"""Pydantic v2 models for SQL Review Environment."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class SQLQuery(BaseModel):
    """A SQL query to be reviewed. Ground truth fields are hidden from agent observations."""
    query_id: str
    sql: str
    submitted_by: str
    database: str
    query_type: Literal["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"]
    has_injection_risk: bool = False
    has_performance_issue: bool = False
    has_logic_bug: bool = False
    correct_verdict: Literal["approve", "reject"] = "approve"
    is_urgent: bool = False  # Used in pipeline_review task


class SQLQueryPublic(BaseModel):
    """Public view of a SQL query — ground truth stripped."""
    query_id: str
    sql: str
    submitted_by: str
    database: str
    query_type: Literal["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"]
    is_urgent: bool = False


class SQLObservation(BaseModel):
    """What the agent sees after each step."""
    queries: List[SQLQueryPublic]
    current_step: int
    task_id: str
    reviewed_count: int
    pending_count: int
    last_action_result: str
    session_stats: Dict[str, Any]
    done: bool


class SQLAction(BaseModel):
    """Action the agent takes on a query."""
    action_type: Literal["review", "approve", "reject", "request_changes", "skip"]
    query_id: str
    verdict: Optional[Literal["approve", "reject"]] = None
    issues_found: Optional[List[Literal[
        "sql_injection", "performance", "logic_bug",
        "missing_index", "n_plus_one", "no_issues"
    ]]] = None
    suggested_fix: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class SQLReward(BaseModel):
    """Reward breakdown for a single action."""
    value: float = Field(..., ge=0.0, le=1.0)
    reason: str
    partial_progress: float
    breakdown: Dict[str, float]


class TaskDefinition(BaseModel):
    """Metadata for a task."""
    id: str
    name: str
    difficulty: Literal["easy", "medium", "hard"]
    max_steps: int
    description: str
    num_queries: int
    scoring_weights: Dict[str, float]
