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
    context: str = ""  # Production context (e.g., "Payment service - checkout endpoint")
    schema_hint: str = ""  # Relevant table schema (e.g., "users(id, name, email, active)")
    has_injection_risk: bool = False
    has_performance_issue: bool = False
    has_logic_bug: bool = False
    correct_verdict: Literal["approve", "reject"] = "approve"
    is_urgent: bool = False
    reasoning_keywords: List[str] = []  # Keywords expected in agent reasoning


class SQLQueryPublic(BaseModel):
    """Public view of a SQL query — ground truth stripped."""
    query_id: str
    sql: str
    submitted_by: str
    database: str
    query_type: Literal["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"]
    context: str = ""
    schema_hint: str = ""
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
    review_history: List[Dict[str, Any]] = []  # Previous reviews this episode
    done: bool


class SQLAction(BaseModel):
    """Action the agent takes on a query."""
    action_type: Literal[
        "review", "approve", "reject", "request_changes", "skip",
        "request_schema", "request_context",
    ]
    query_id: str
    verdict: Optional[Literal["approve", "reject"]] = None
    issues_found: Optional[List[Literal[
        "sql_injection", "performance", "logic_bug",
        "missing_index", "n_plus_one", "no_issues"
    ]]] = None
    suggested_fix: Optional[str] = None
    reasoning: Optional[str] = None  # Why the agent made this decision
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
