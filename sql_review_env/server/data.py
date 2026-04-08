"""Real-world SQL query pool for the SQL Review Environment.

Uses seeded random (seed=42) for full reproducibility.
56 unique SQL queries across 5 categories, modeled after actual
production code review submissions:
  - Safe (correct, well-written queries) -> approve
  - Injection risk (unsanitized user input) -> reject
  - Performance issues (missing indexes, full scans) -> reject
  - Logic bugs (wrong semantics, data corruption) -> reject
  - Multi-issue (combinations of the above) -> reject
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


# ── Safe queries ─────────────────────────────────────────────────
# Well-written, parameterized, efficient — should be approved.

def _safe_queries() -> List[SQLQuery]:
    return [
        SQLQuery(
            query_id="safe-001",
            sql="SELECT id, name, email FROM users WHERE active = true ORDER BY created_at DESC LIMIT 100;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-002",
            sql="SELECT o.id, o.total, u.name FROM orders o INNER JOIN users u ON o.user_id = u.id WHERE o.status = 'completed' AND o.created_at >= '2024-01-01' LIMIT 500;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-003",
            sql="INSERT INTO audit_log (event_type, user_id, timestamp, details) VALUES ($1, $2, NOW(), $3);",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-004",
            sql="UPDATE orders SET status = 'shipped', updated_at = NOW() WHERE id = $1 AND status = 'processing';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-005",
            sql="SELECT COUNT(*) AS total_orders, SUM(total) AS revenue FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31' AND status = 'completed';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-006",
            sql="SELECT p.name, c.name AS category FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.price > 0 AND p.active = true ORDER BY p.name LIMIT 200;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-007",
            sql="DELETE FROM session_tokens WHERE expires_at < NOW() - INTERVAL '30 days';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-008",
            sql="SELECT department, COUNT(*) AS headcount, AVG(salary) AS avg_salary FROM employees WHERE terminated_at IS NULL GROUP BY department HAVING COUNT(*) > 5 ORDER BY avg_salary DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-009",
            sql="INSERT INTO notifications (user_id, message, type, created_at) SELECT id, 'Your subscription is expiring soon', 'warning', NOW() FROM users WHERE subscription_end BETWEEN NOW() AND NOW() + INTERVAL '7 days' AND active = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-010",
            sql="SELECT u.id, u.name, COUNT(o.id) AS order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE u.created_at >= '2024-06-01' GROUP BY u.id, u.name ORDER BY order_count DESC LIMIT 50;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-011",
            sql="UPDATE inventory SET quantity = quantity - $1 WHERE product_id = $2 AND quantity >= $1;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-012",
            sql="SELECT DATE_TRUNC('month', created_at) AS month, COUNT(*) AS signups FROM users WHERE created_at >= '2024-01-01' GROUP BY DATE_TRUNC('month', created_at) ORDER BY month;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-013",
            sql="CREATE INDEX CONCURRENTLY idx_orders_user_status ON orders (user_id, status) WHERE status IN ('pending', 'processing');",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="CREATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-014",
            sql="SELECT r.id, r.rating, r.comment, u.name FROM reviews r INNER JOIN users u ON r.user_id = u.id WHERE r.product_id = $1 AND r.approved = true ORDER BY r.created_at DESC LIMIT 20;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
        SQLQuery(
            query_id="safe-015",
            sql="SELECT COALESCE(SUM(amount), 0) AS total_refunds FROM refunds WHERE order_id = $1 AND status = 'completed';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve"
        ),
    ]


# ── Injection queries ────────────────────────────────────────────
# These represent SQL templates extracted from application code during
# code review. The vulnerability is that user input is interpolated
# directly into the query string instead of using parameterized queries.
# Each sql field shows the template as it appears in the codebase.

def _injection_queries() -> List[SQLQuery]:
    return [
        SQLQuery(
            query_id="inj-001",
            sql="SELECT id, name, email FROM users WHERE username = '{username}' AND password_hash = '{password_hash}';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-002",
            sql="SELECT * FROM products WHERE category_id = {category_id} AND active = true ORDER BY price;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-003",
            sql="SELECT account_id, balance, account_type FROM accounts WHERE owner_name = '" + "' || user_input || '" + "' AND branch_id = 5;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-004",
            sql="DELETE FROM user_sessions WHERE session_token = '{token}' AND expires_at < NOW();",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-005",
            sql="UPDATE user_profiles SET display_name = '{new_name}', updated_at = NOW() WHERE user_id = {user_id};",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-006",
            sql="SELECT o.id, o.total, o.status FROM orders o WHERE o.user_id = {request_user_id} ORDER BY o.created_at DESC LIMIT 50;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-007",
            sql="INSERT INTO feedback (user_id, subject, body, created_at) VALUES ({uid}, '{subject}', '{body}', NOW());",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-008",
            sql="SELECT e.name, e.email, d.name AS dept FROM employees e JOIN departments d ON e.dept_id = d.id WHERE e.employee_id = '{emp_id}';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-009",
            sql="SELECT * FROM articles WHERE title LIKE '%{search_query}%' OR body LIKE '%{search_query}%' ORDER BY published_at DESC LIMIT 20;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-010",
            sql="SELECT id, filename, uploaded_by FROM attachments WHERE id IN ({attachment_ids}) AND project_id = 42;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-011",
            sql=(
                "EXECUTE 'SELECT id, role, last_login FROM staff WHERE department = '''"
                " || dept_param || "
                "'''  AND active = true' INTO result;"
            ),
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
        SQLQuery(
            query_id="inj-012",
            sql="SELECT t.id, t.name, t.due_date FROM tasks t WHERE t.assignee_id = {assignee} AND t.project_id = {project} AND t.status != 'archived';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject"
        ),
    ]


# ── Performance queries ──────────────────────────────────────────
# Real-world anti-patterns: full table scans, functions on indexed
# columns, cartesian products, N+1 patterns, missing LIMIT, etc.

def _performance_queries() -> List[SQLQuery]:
    return [
        # Unbounded SELECT * on a large table — no WHERE, no LIMIT
        SQLQuery(
            query_id="perf-001",
            sql="SELECT * FROM event_logs ORDER BY created_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # Function on indexed column prevents index usage
        SQLQuery(
            query_id="perf-002",
            sql="SELECT id, email, created_at FROM users WHERE LOWER(email) = 'admin@company.com';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # Deeply nested subqueries instead of JOINs
        SQLQuery(
            query_id="perf-003",
            sql="SELECT p.id, p.name, p.price FROM products p WHERE p.id IN (SELECT oi.product_id FROM order_items oi WHERE oi.order_id IN (SELECT o.id FROM orders o WHERE o.user_id IN (SELECT u.id FROM users u WHERE u.country = 'US' AND u.active = true)));",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # Implicit cartesian join — missing JOIN condition between c and d
        SQLQuery(
            query_id="perf-004",
            sql="SELECT u.name, o.total, p.name AS product, c.code AS coupon FROM users u JOIN orders o ON u.id = o.user_id JOIN products p ON o.product_id = p.id, coupons c WHERE o.created_at > '2024-01-01';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # Function wrapping indexed timestamp column
        SQLQuery(
            query_id="perf-005",
            sql="SELECT user_id, COUNT(*) AS login_count FROM login_history WHERE DATE(login_time) = '2024-06-15' GROUP BY user_id;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # SELECT DISTINCT * on a wide table — sorts entire result set
        SQLQuery(
            query_id="perf-006",
            sql="SELECT DISTINCT * FROM customer_events WHERE event_type IN ('page_view', 'click', 'scroll') ORDER BY created_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # Correlated subquery executes once per row in outer query
        SQLQuery(
            query_id="perf-007",
            sql="SELECT u.id, u.name, (SELECT MAX(o.created_at) FROM orders o WHERE o.user_id = u.id) AS last_order, (SELECT SUM(o.total) FROM orders o WHERE o.user_id = u.id) AS lifetime_value FROM users u WHERE u.active = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # Wildcard LIKE with leading % on unindexed text — full table scan
        SQLQuery(
            query_id="perf-008",
            sql="SELECT id, title, body, author_id FROM blog_posts WHERE body LIKE '%kubernetes deployment strategy%' ORDER BY published_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # YEAR() and MONTH() on indexed column prevent index usage
        SQLQuery(
            query_id="perf-009",
            sql="SELECT id, amount, description FROM transactions WHERE EXTRACT(YEAR FROM created_at) = 2024 AND EXTRACT(MONTH FROM created_at) = 6 ORDER BY amount DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # N+1 pattern: correlated subquery per row
        SQLQuery(
            query_id="perf-010",
            sql="SELECT p.id, p.name, p.price, (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id) AS review_count, (SELECT AVG(r.rating) FROM reviews r WHERE r.product_id = p.id) AS avg_rating FROM products p WHERE p.active = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # Implicit type cast on indexed column — string compared to integer
        SQLQuery(
            query_id="perf-011",
            sql="SELECT id, name, phone FROM customers WHERE phone = 5551234567;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # OR across different columns defeats index usage
        SQLQuery(
            query_id="perf-012",
            sql="SELECT id, subject, body, sender_id, recipient_id FROM messages WHERE sender_id = 42 OR recipient_id = 42 OR cc_list LIKE '%user:42%' ORDER BY sent_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
    ]


# ── Logic bug queries ────────────────────────────────────────────
# Queries that parse and execute but produce wrong results or cause
# data corruption. These are the bugs that pass unit tests and break
# in production.

def _logic_bug_queries() -> List[SQLQuery]:
    return [
        # DELETE without WHERE — wipes entire table
        SQLQuery(
            query_id="bug-001",
            sql="DELETE FROM password_reset_tokens;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # UPDATE sets all active accounts to zero balance
        SQLQuery(
            query_id="bug-002",
            sql="UPDATE accounts SET balance = 0, updated_at = NOW() WHERE status = 'active';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # Wrong JOIN condition — joins on name instead of id, producing duplicates
        SQLQuery(
            query_id="bug-003",
            sql="SELECT u.id, u.email, o.id AS order_id, o.total FROM users u INNER JOIN orders o ON u.name = o.shipping_name WHERE o.status = 'pending';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # Race condition: reads and writes balance without FOR UPDATE
        SQLQuery(
            query_id="bug-004",
            sql="UPDATE wallets SET balance = (SELECT balance FROM wallets WHERE user_id = $1) - $2 WHERE user_id = $1;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # Negating price makes all electronics have negative prices
        SQLQuery(
            query_id="bug-005",
            sql="UPDATE products SET price = price * -1, updated_at = NOW() WHERE category = 'electronics' AND price > 0;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # Impossible WHERE — salary cannot be both > 50k and < 30k
        SQLQuery(
            query_id="bug-006",
            sql="SELECT id, name, salary, department FROM employees WHERE salary > 50000 AND salary < 30000 AND active = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # Inserting order with NULL user and negative total
        SQLQuery(
            query_id="bug-007",
            sql="INSERT INTO orders (user_id, total, status, created_at) VALUES (NULL, -49.99, 'completed', NOW());",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # Off-by-one: excludes exactly the users who should be charged
        SQLQuery(
            query_id="bug-008",
            sql="UPDATE subscriptions SET status = 'expired', ended_at = NOW() WHERE renewal_date < CURRENT_DATE AND status = 'active';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # DROP TABLE in production without safeguards
        SQLQuery(
            query_id="bug-009",
            sql="DROP TABLE IF EXISTS user_preferences CASCADE;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DROP",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # Inverted date range — start > end, always returns empty
        SQLQuery(
            query_id="bug-010",
            sql="SELECT id, user_id, amount, created_at FROM payments WHERE created_at >= '2025-12-31' AND created_at <= '2025-01-01' AND status = 'completed';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # NULLs all emails for every user in the table
        SQLQuery(
            query_id="bug-011",
            sql="UPDATE users SET email = NULL, email_verified = false WHERE id > 0;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # WHERE always true — deletes all transactions
        SQLQuery(
            query_id="bug-012",
            sql="DELETE FROM transactions WHERE amount IS NOT NULL OR amount IS NULL;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
    ]


# ── Multi-issue queries ──────────────────────────────────────────
# Queries with multiple problems simultaneously. These test whether
# the agent can identify all issues, not just the most obvious one.

def _multi_issue_queries() -> List[SQLQuery]:
    return [
        # Injection (interpolated user input) + Performance (SELECT *, no LIMIT)
        SQLQuery(
            query_id="multi-001",
            sql="SELECT * FROM audit_logs WHERE actor_name = '{username}' ORDER BY created_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # Injection (interpolated id) + Logic bug (DELETE can wipe with crafted input)
        SQLQuery(
            query_id="multi-002",
            sql="DELETE FROM user_files WHERE owner_id = {user_id} AND expired = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # Injection (interpolated param) + Performance (function on indexed column)
        SQLQuery(
            query_id="multi-003",
            sql="SELECT id, name, email FROM customers WHERE LOWER(email) = LOWER('{email_input}') AND region = '{region}';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=True, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject"
        ),
        # Injection (interpolated values) + Logic bug (negative balance, no validation)
        SQLQuery(
            query_id="multi-004",
            sql="UPDATE accounts SET balance = balance - {amount}, last_withdrawal = NOW() WHERE account_number = '{account_num}';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject"
        ),
        # Performance (cartesian join, correlated subquery) + Logic bug (missing GROUP BY column)
        SQLQuery(
            query_id="multi-005",
            sql="SELECT u.name, u.department, COUNT(t.id) AS task_count FROM users u, tasks t WHERE u.active = true AND (SELECT AVG(hours) FROM time_entries te WHERE te.user_id = u.id) > 4 GROUP BY u.name;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=True, correct_verdict="reject"
        ),
    ]


# ── Master query pool ────────────────────────────────────────────
# Built once at import time with seed(42) for full reproducibility.

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
