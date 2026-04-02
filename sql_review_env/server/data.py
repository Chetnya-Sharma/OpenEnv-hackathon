"""Synthetic SQL query generator for the SQL Review Environment.

Uses seeded random (seed=42) for full reproducibility.
Generates 50+ unique SQL queries across 4 categories:
  - Safe (correct, well-written queries) → approve
  - Injection risk → reject
  - Performance issues → reject
  - Logic bugs → reject
"""

import random
from typing import List
from .models import SQLQuery

random.seed(42)

_DATABASES = ["analytics_db", "production_db", "warehouse_db", "users_db", "orders_db"]
_SUBMITTERS = ["alice.chen", "bob.martinez", "carol.johnson", "dave.kim", "eve.patel",
               "frank.wong", "grace.lee", "henry.taylor", "iris.smith", "jack.brown"]


def _rand_db() -> str:
    return random.choice(_DATABASES)


def _rand_sub() -> str:
    return random.choice(_SUBMITTERS)


def _safe_queries() -> List[SQLQuery]:
    """Well-written, secure, efficient queries that should be approved."""
    return [
        SQLQuery(
            query_id="safe-001", sql="SELECT id, name, email FROM users WHERE active = true ORDER BY created_at DESC LIMIT 100;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-002", sql="SELECT o.id, o.total, u.name FROM orders o INNER JOIN users u ON o.user_id = u.id WHERE o.status = 'completed' AND o.created_at >= '2024-01-01' LIMIT 500;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-003", sql="INSERT INTO audit_log (event_type, user_id, timestamp, details) VALUES (%s, %s, NOW(), %s);",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-004", sql="UPDATE orders SET status = 'shipped', updated_at = NOW() WHERE id = ? AND status = 'processing';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-005", sql="SELECT COUNT(*) as total_orders, SUM(total) as revenue FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31' AND status = 'completed';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-006", sql="SELECT p.name, c.name AS category FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.price > 0 AND p.active = true ORDER BY p.name LIMIT 200;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-007", sql="DELETE FROM session_tokens WHERE expires_at < NOW() AND revoked = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-008", sql="SELECT department, COUNT(*) as headcount, AVG(salary) as avg_salary FROM employees WHERE active = true GROUP BY department HAVING COUNT(*) > 5 ORDER BY avg_salary DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-009", sql="INSERT INTO notifications (user_id, message, type, created_at) SELECT id, 'Your subscription is expiring soon', 'warning', NOW() FROM users WHERE subscription_end < NOW() + INTERVAL '7 days' AND active = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-010", sql="SELECT u.id, u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE u.created_at >= '2024-06-01' GROUP BY u.id, u.name ORDER BY order_count DESC LIMIT 50;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-011", sql="UPDATE inventory SET quantity = quantity - ? WHERE product_id = ? AND quantity >= ?;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-012", sql="SELECT DATE_TRUNC('month', created_at) as month, COUNT(*) as signups FROM users WHERE created_at >= '2024-01-01' GROUP BY DATE_TRUNC('month', created_at) ORDER BY month;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-013", sql="CREATE INDEX CONCURRENTLY idx_orders_user_status ON orders (user_id, status) WHERE status IN ('pending', 'processing');",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="CREATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-014", sql="SELECT r.id, r.rating, r.comment, u.name FROM reviews r INNER JOIN users u ON r.user_id = u.id WHERE r.product_id = ? AND r.approved = true ORDER BY r.created_at DESC LIMIT 20;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-015", sql="SELECT COALESCE(SUM(amount), 0) as total_refunds FROM refunds WHERE order_id = %s AND status = 'completed';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
    ]


def _injection_queries() -> List[SQLQuery]:
    """Queries with SQL injection vulnerabilities — must be rejected."""
    return [
        SQLQuery(
            query_id="inj-001", sql="SELECT * FROM users WHERE username = '" + "' + user_input + '" + "' AND password = '" + "' + pwd + '" + "';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-002", sql="SELECT * FROM products WHERE id = " + "user_id" + " OR 1=1;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-003", sql="SELECT * FROM accounts WHERE account_id = '1' UNION SELECT username, password, null, null FROM admin_users --';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-004", sql="DELETE FROM orders WHERE order_id = '" + "'; DROP TABLE orders; --" + "';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-005", sql="UPDATE users SET role = 'admin' WHERE id = " + "request.params.id" + ";",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-006", sql="SELECT * FROM users WHERE email = '" + "user@test.com' OR '1'='1" + "';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-007", sql="INSERT INTO logs (message) VALUES ('" + "User input: '); DELETE FROM logs; --" + "');",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-008", sql="SELECT name, balance FROM accounts WHERE id = CAST(" + "user_input" + " AS INTEGER);",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-009", sql="SELECT * FROM users WHERE username LIKE '%" + "search_term" + "%' ORDER BY created_at;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-010", sql="SELECT * FROM sessions WHERE token = '" + "abc123'; UPDATE users SET admin=true WHERE id=1; --" + "';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-011", sql="SELECT * FROM products WHERE category = '" + "electronics' UNION SELECT table_name, column_name, null FROM information_schema.columns --" + "';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-012", sql="SELECT * FROM employees WHERE department = CONCAT('" + "engineering', '; DROP TABLE salaries; --" + "');",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
    ]


def _performance_queries() -> List[SQLQuery]:
    """Queries with performance issues — must be rejected."""
    return [
        SQLQuery(
            query_id="perf-001", sql="SELECT * FROM orders;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-002", sql="SELECT * FROM users WHERE UPPER(email) = 'ADMIN@COMPANY.COM';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-003", sql="SELECT * FROM products WHERE id IN (SELECT product_id FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE user_id IN (SELECT id FROM users WHERE active = true)));",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-004", sql="SELECT u.*, o.* FROM users u, orders o;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-005", sql="SELECT * FROM logs WHERE DATE_FORMAT(created_at, '%Y-%m') = '2024-01';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-006", sql="SELECT DISTINCT * FROM events ORDER BY created_at;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-007", sql="SELECT * FROM transactions WHERE amount > (SELECT AVG(amount) FROM transactions);",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-008", sql="SELECT a.*, b.*, c.*, d.* FROM table_a a, table_b b, table_c c, table_d d WHERE a.id = b.a_id;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-009", sql="SELECT * FROM users WHERE YEAR(created_at) = 2024 AND MONTH(created_at) = 6;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-010", sql="SELECT name, (SELECT COUNT(*) FROM orders WHERE orders.user_id = users.id) as order_count FROM users;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-011", sql="SELECT * FROM products WHERE LOWER(name) LIKE '%widget%' OR LOWER(description) LIKE '%widget%';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="perf-012", sql="SELECT * FROM audit_log WHERE CAST(user_id AS VARCHAR) = '12345';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
    ]


def _logic_bug_queries() -> List[SQLQuery]:
    """Queries with logic bugs — must be rejected."""
    return [
        SQLQuery(
            query_id="bug-001", sql="DELETE FROM users;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-002", sql="UPDATE accounts SET balance = 0 WHERE status = 'active';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-003", sql="SELECT * FROM orders WHERE total > 100 LIMIT 10 OFFSET -1;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-004", sql="SELECT u.name, o.total FROM users u INNER JOIN orders o ON u.id = o.user_id WHERE o.status = 'pending';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
        ),
        SQLQuery(
            query_id="bug-005", sql="UPDATE products SET price = price * -1 WHERE category = 'electronics';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-006", sql="SELECT * FROM employees WHERE salary > 50000 AND salary < 30000;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-007", sql="INSERT INTO orders (user_id, total, status) VALUES (NULL, -50.00, 'completed');",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-008", sql="UPDATE inventory SET quantity = quantity + 1 WHERE product_id = 'ABC' AND quantity <= 0;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-009", sql="DROP TABLE users CASCADE;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DROP",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-010", sql="SELECT * FROM orders WHERE created_at > '2025-01-01' AND created_at < '2024-01-01';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-011", sql="UPDATE users SET email = NULL WHERE id > 0;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="bug-012", sql="DELETE FROM transactions WHERE amount = amount;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
    ]


def _multi_issue_queries() -> List[SQLQuery]:
    """Queries with multiple issues simultaneously."""
    return [
        SQLQuery(
            query_id="multi-001",
            sql="SELECT * FROM users WHERE name = '" + "admin' OR '1'='1" + "';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="multi-002",
            sql="DELETE FROM logs WHERE id = " + "user_input" + ";",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="multi-003",
            sql="SELECT * FROM orders WHERE UPPER(status) = 'PENDING' AND user_id = " + "request.user_id" + ";",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="multi-004",
            sql="UPDATE accounts SET balance = -100 WHERE owner = '" + "'; DROP TABLE accounts; --" + "';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="multi-005",
            sql="SELECT *, (SELECT COUNT(*) FROM orders) FROM users, products WHERE LOWER(users.name) = 'test';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=True, correct_verdict="reject"
        ),
    ]


# Master query pool — built once at import time with seed(42)
random.seed(42)
_ALL_QUERIES: List[SQLQuery] = (
    _safe_queries() + _injection_queries() + _performance_queries() +
    _logic_bug_queries() + _multi_issue_queries()
)
# Re-seed after building to ensure reproducibility on subsequent calls
random.seed(42)


def get_all_queries() -> List[SQLQuery]:
    """Return full query pool (56 queries)."""
    return list(_ALL_QUERIES)


def get_queries_for_task(task_id: str, seed: int = 42) -> List[SQLQuery]:
    """Return a deterministic subset of queries for the given task."""
    rng = random.Random(seed)
    pool = list(_ALL_QUERIES)

    if task_id == "single_review":
        # 1 query — pick one that has at least one issue for interesting grading
        candidates = [q for q in pool if q.correct_verdict == "reject"]
        return [rng.choice(candidates)]

    elif task_id == "batch_review":
        # 8 queries — mix of safe and problematic
        safe = [q for q in pool if q.correct_verdict == "approve"]
        reject = [q for q in pool if q.correct_verdict == "reject"]
        picked_safe = rng.sample(safe, min(3, len(safe)))
        picked_reject = rng.sample(reject, min(5, len(reject)))
        result = picked_safe + picked_reject
        rng.shuffle(result)
        return result[:8]

    elif task_id == "pipeline_review":
        # 15 queries in 3 batches of 5, some marked urgent
        safe = [q for q in pool if q.correct_verdict == "approve"]
        reject = [q for q in pool if q.correct_verdict == "reject"]
        picked_safe = rng.sample(safe, min(5, len(safe)))
        picked_reject = rng.sample(reject, min(10, len(reject)))
        result = picked_safe + picked_reject
        rng.shuffle(result)
        result = result[:15]
        # Mark ~5 queries as urgent (prioritize reject ones)
        urgent_candidates = [i for i, q in enumerate(result) if q.correct_verdict == "reject"]
        urgent_indices = set(rng.sample(urgent_candidates, min(5, len(urgent_candidates))))
        for i in urgent_indices:
            result[i] = result[i].model_copy(update={"is_urgent": True})
        return result

    else:
        return rng.sample(pool, min(8, len(pool)))
