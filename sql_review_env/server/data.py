"""Real-world SQL query pool for the SQL Review Environment.

Uses seeded random (seed=42) for full reproducibility.
62 unique SQL queries across 6 categories, modeled after actual
production code review submissions:
  - Safe (correct, well-written queries) -> approve
  - Injection risk (unsanitized user input) -> reject
  - Performance issues (missing indexes, full scans) -> reject
  - Logic bugs (wrong semantics, data corruption) -> reject
  - Multi-issue (combinations of the above) -> reject
  - Adversarial (designed to fool LLMs — tricky edge cases) -> mixed
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
            context="User management API — list active users endpoint",
            schema_hint="users(id INT PK, name VARCHAR, email VARCHAR, active BOOL, created_at TIMESTAMP) — idx on (active, created_at)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["parameterized", "limit", "indexed", "selective columns"],
        ),
        SQLQuery(
            query_id="safe-002",
            sql="SELECT o.id, o.total, u.name FROM orders o INNER JOIN users u ON o.user_id = u.id WHERE o.status = 'completed' AND o.created_at >= '2024-01-01' LIMIT 500;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Finance dashboard — completed orders report",
            schema_hint="orders(id, user_id FK, total DECIMAL, status VARCHAR, created_at TIMESTAMP); users(id PK, name) — idx on orders(status, created_at)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["join", "limit", "indexed", "explicit columns"],
        ),
        SQLQuery(
            query_id="safe-003",
            sql="INSERT INTO audit_log (event_type, user_id, timestamp, details) VALUES ($1, $2, NOW(), $3);",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            context="Audit service — logs user actions for compliance",
            schema_hint="audit_log(id SERIAL PK, event_type VARCHAR, user_id INT, timestamp TIMESTAMP, details JSONB)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["parameterized", "prepared statement", "$1"],
        ),
        SQLQuery(
            query_id="safe-004",
            sql="UPDATE orders SET status = 'shipped', updated_at = NOW() WHERE id = $1 AND status = 'processing';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="Order service — mark order as shipped after fulfillment",
            schema_hint="orders(id PK, status VARCHAR, updated_at TIMESTAMP) — idx on (id, status)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["parameterized", "where clause", "status check"],
        ),
        SQLQuery(
            query_id="safe-005",
            sql="SELECT COUNT(*) AS total_orders, SUM(total) AS revenue FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31' AND status = 'completed';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Analytics — annual revenue summary for board report",
            schema_hint="orders(id, total DECIMAL, status VARCHAR, created_at TIMESTAMP) — 4.2M rows, idx on (created_at, status)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["aggregation", "indexed", "bounded range"],
        ),
        SQLQuery(
            query_id="safe-006",
            sql="SELECT p.name, c.name AS category FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.price > 0 AND p.active = true ORDER BY p.name LIMIT 200;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Product catalog API — browse active products",
            schema_hint="products(id PK, name VARCHAR, price DECIMAL, active BOOL, category_id FK); categories(id PK, name VARCHAR)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["join", "limit", "filtered"],
        ),
        SQLQuery(
            query_id="safe-007",
            sql="DELETE FROM session_tokens WHERE expires_at < NOW() - INTERVAL '30 days';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            context="Auth service cron job — purge expired session tokens (runs nightly)",
            schema_hint="session_tokens(id PK, token VARCHAR, user_id INT, expires_at TIMESTAMP) — idx on expires_at",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["cleanup", "bounded delete", "expiration"],
        ),
        SQLQuery(
            query_id="safe-008",
            sql="SELECT department, COUNT(*) AS headcount, AVG(salary) AS avg_salary FROM employees WHERE terminated_at IS NULL GROUP BY department HAVING COUNT(*) > 5 ORDER BY avg_salary DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="HR dashboard — department salary analysis",
            schema_hint="employees(id PK, department VARCHAR, salary DECIMAL, terminated_at TIMESTAMP) — 12K rows",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["aggregation", "having", "group by"],
        ),
        SQLQuery(
            query_id="safe-009",
            sql="INSERT INTO notifications (user_id, message, type, created_at) SELECT id, 'Your subscription is expiring soon', 'warning', NOW() FROM users WHERE subscription_end BETWEEN NOW() AND NOW() + INTERVAL '7 days' AND active = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            context="Notification service — subscription expiry warning batch job",
            schema_hint="users(id PK, subscription_end DATE, active BOOL); notifications(id SERIAL, user_id, message, type, created_at)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["insert select", "bounded", "batch"],
        ),
        SQLQuery(
            query_id="safe-010",
            sql="SELECT u.id, u.name, COUNT(o.id) AS order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE u.created_at >= '2024-06-01' GROUP BY u.id, u.name ORDER BY order_count DESC LIMIT 50;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Growth team — top new customers by order volume",
            schema_hint="users(id PK, name, created_at); orders(id PK, user_id FK) — idx on users(created_at), orders(user_id)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["join", "limit", "group by", "aggregation"],
        ),
        SQLQuery(
            query_id="safe-011",
            sql="UPDATE inventory SET quantity = quantity - $1 WHERE product_id = $2 AND quantity >= $1;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="Inventory service — atomic stock deduction on purchase",
            schema_hint="inventory(product_id PK, quantity INT, updated_at TIMESTAMP)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["parameterized", "atomic", "check constraint"],
        ),
        SQLQuery(
            query_id="safe-012",
            sql="SELECT DATE_TRUNC('month', created_at) AS month, COUNT(*) AS signups FROM users WHERE created_at >= '2024-01-01' GROUP BY DATE_TRUNC('month', created_at) ORDER BY month;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Analytics — monthly signup trend chart",
            schema_hint="users(id PK, created_at TIMESTAMP) — idx on created_at",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["date_trunc", "aggregation", "time series"],
        ),
        SQLQuery(
            query_id="safe-013",
            sql="CREATE INDEX CONCURRENTLY idx_orders_user_status ON orders (user_id, status) WHERE status IN ('pending', 'processing');",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="CREATE",
            context="DBA migration — add partial index for order lookup hot path",
            schema_hint="orders(id PK, user_id FK, status VARCHAR) — 8M rows, ~15% are pending/processing",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["concurrently", "partial index", "non-blocking"],
        ),
        SQLQuery(
            query_id="safe-014",
            sql="SELECT r.id, r.rating, r.comment, u.name FROM reviews r INNER JOIN users u ON r.user_id = u.id WHERE r.product_id = $1 AND r.approved = true ORDER BY r.created_at DESC LIMIT 20;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Product page — display approved reviews",
            schema_hint="reviews(id PK, product_id FK, user_id FK, rating INT, comment TEXT, approved BOOL, created_at) — idx on (product_id, approved, created_at)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["parameterized", "limit", "indexed"],
        ),
        SQLQuery(
            query_id="safe-015",
            sql="SELECT COALESCE(SUM(amount), 0) AS total_refunds FROM refunds WHERE order_id = $1 AND status = 'completed';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Refund service — check total refunds issued for an order",
            schema_hint="refunds(id PK, order_id FK, amount DECIMAL, status VARCHAR) — idx on (order_id, status)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["parameterized", "coalesce", "null safe"],
        ),
    ]


# ── Injection queries ────────────────────────────────────────────
# These represent SQL templates extracted from application code during
# code review. The vulnerability is that user input is interpolated
# directly into the query string instead of using parameterized queries.

def _injection_queries() -> List[SQLQuery]:
    return [
        SQLQuery(
            query_id="inj-001",
            sql="SELECT id, name, email FROM users WHERE username = '{username}' AND password_hash = '{password_hash}';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Authentication service — login endpoint",
            schema_hint="users(id PK, name, email, username VARCHAR UNIQUE, password_hash VARCHAR)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "f-string", "parameterized", "sanitize", "prepared statement"],
        ),
        SQLQuery(
            query_id="inj-002",
            sql="SELECT * FROM products WHERE category_id = {category_id} AND active = true ORDER BY price;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Product catalog — filter by category endpoint",
            schema_hint="products(id PK, category_id INT FK, active BOOL, price DECIMAL)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "interpolat", "parameterized", "unsanitized"],
        ),
        SQLQuery(
            query_id="inj-003",
            sql="SELECT account_id, balance, account_type FROM accounts WHERE owner_name = '" + "' || user_input || '" + "' AND branch_id = 5;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Banking app — account lookup by name",
            schema_hint="accounts(account_id PK, balance DECIMAL, account_type VARCHAR, owner_name VARCHAR, branch_id INT)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "concatenat", "parameterized", "string building"],
        ),
        SQLQuery(
            query_id="inj-004",
            sql="DELETE FROM user_sessions WHERE session_token = '{token}' AND expires_at < NOW();",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            context="Session management — logout/cleanup endpoint",
            schema_hint="user_sessions(id PK, session_token VARCHAR, user_id INT, expires_at TIMESTAMP)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "interpolat", "delete", "parameterized"],
        ),
        SQLQuery(
            query_id="inj-005",
            sql="UPDATE user_profiles SET display_name = '{new_name}', updated_at = NOW() WHERE user_id = {user_id};",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="Profile service — update display name endpoint",
            schema_hint="user_profiles(user_id PK, display_name VARCHAR, updated_at TIMESTAMP)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "interpolat", "update", "parameterized"],
        ),
        SQLQuery(
            query_id="inj-006",
            sql="SELECT o.id, o.total, o.status FROM orders o WHERE o.user_id = {request_user_id} ORDER BY o.created_at DESC LIMIT 50;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Order history API — user's recent orders",
            schema_hint="orders(id PK, user_id FK, total DECIMAL, status VARCHAR, created_at TIMESTAMP)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "interpolat", "request", "parameterized"],
        ),
        SQLQuery(
            query_id="inj-007",
            sql="INSERT INTO feedback (user_id, subject, body, created_at) VALUES ({uid}, '{subject}', '{body}', NOW());",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            context="Feedback form — submit user feedback",
            schema_hint="feedback(id SERIAL PK, user_id INT, subject VARCHAR, body TEXT, created_at TIMESTAMP)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "interpolat", "user input", "parameterized"],
        ),
        SQLQuery(
            query_id="inj-008",
            sql="SELECT e.name, e.email, d.name AS dept FROM employees e JOIN departments d ON e.dept_id = d.id WHERE e.employee_id = '{emp_id}';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="HR portal — employee detail page",
            schema_hint="employees(employee_id PK, name, email, dept_id FK); departments(id PK, name)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "f-string", "parameterized"],
        ),
        SQLQuery(
            query_id="inj-009",
            sql="SELECT * FROM articles WHERE title LIKE '%{search_query}%' OR body LIKE '%{search_query}%' ORDER BY published_at DESC LIMIT 20;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Blog search — full-text search endpoint",
            schema_hint="articles(id PK, title VARCHAR, body TEXT, published_at TIMESTAMP)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "like", "search", "parameterized"],
        ),
        SQLQuery(
            query_id="inj-010",
            sql="SELECT id, filename, uploaded_by FROM attachments WHERE id IN ({attachment_ids}) AND project_id = 42;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Project management — download selected attachments",
            schema_hint="attachments(id PK, filename VARCHAR, uploaded_by INT, project_id INT FK)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "IN clause", "interpolat", "parameterized"],
        ),
        SQLQuery(
            query_id="inj-011",
            sql=(
                "EXECUTE 'SELECT id, role, last_login FROM staff WHERE department = '''"
                " || dept_param || "
                "'''  AND active = true' INTO result;"
            ),
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Admin tool — stored procedure for department staff lookup",
            schema_hint="staff(id PK, role VARCHAR, last_login TIMESTAMP, department VARCHAR, active BOOL)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "dynamic sql", "execute", "parameterized"],
        ),
        SQLQuery(
            query_id="inj-012",
            sql="SELECT t.id, t.name, t.due_date FROM tasks t WHERE t.assignee_id = {assignee} AND t.project_id = {project} AND t.status != 'archived';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Task board — list tasks assigned to user in project",
            schema_hint="tasks(id PK, name VARCHAR, due_date DATE, assignee_id FK, project_id FK, status VARCHAR)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "interpolat", "parameterized"],
        ),
    ]


# ── Performance queries ──────────────────────────────────────────
# Real-world anti-patterns: full table scans, functions on indexed
# columns, cartesian products, N+1 patterns, missing LIMIT, etc.

def _performance_queries() -> List[SQLQuery]:
    return [
        SQLQuery(
            query_id="perf-001",
            sql="SELECT * FROM event_logs ORDER BY created_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Admin dashboard — export all event logs for CSV download",
            schema_hint="event_logs(id PK, event_type, user_id, payload JSONB, created_at TIMESTAMP) — 48M rows",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["select *", "no limit", "full scan", "unbounded", "48M rows"],
        ),
        SQLQuery(
            query_id="perf-002",
            sql="SELECT id, email, created_at FROM users WHERE LOWER(email) = 'admin@company.com';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Auth service — case-insensitive email lookup",
            schema_hint="users(id PK, email VARCHAR UNIQUE, created_at) — idx on email, 2.1M rows",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["function on index", "lower", "full scan", "citext"],
        ),
        SQLQuery(
            query_id="perf-003",
            sql="SELECT p.id, p.name, p.price FROM products p WHERE p.id IN (SELECT oi.product_id FROM order_items oi WHERE oi.order_id IN (SELECT o.id FROM orders o WHERE o.user_id IN (SELECT u.id FROM users u WHERE u.country = 'US' AND u.active = true)));",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Marketing — products purchased by active US users",
            schema_hint="products(id PK); order_items(order_id FK, product_id FK); orders(id PK, user_id FK); users(id PK, country, active) — users: 2M, orders: 8M",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["nested subquery", "join", "rewrite", "IN"],
        ),
        SQLQuery(
            query_id="perf-004",
            sql="SELECT u.name, o.total, p.name AS product, c.code AS coupon FROM users u JOIN orders o ON u.id = o.user_id JOIN products p ON o.product_id = p.id, coupons c WHERE o.created_at > '2024-01-01';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Sales report — orders with coupon codes",
            schema_hint="users, orders, products — proper FKs; coupons(id, code) — 15K rows; NO join condition on coupons",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["cartesian", "cross join", "missing join condition", "coupons"],
        ),
        SQLQuery(
            query_id="perf-005",
            sql="SELECT user_id, COUNT(*) AS login_count FROM login_history WHERE DATE(login_time) = '2024-06-15' GROUP BY user_id;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Security audit — login frequency analysis for specific date",
            schema_hint="login_history(id PK, user_id FK, login_time TIMESTAMP) — idx on login_time, 95M rows",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["function on index", "DATE()", "range scan", "sargable"],
        ),
        SQLQuery(
            query_id="perf-006",
            sql="SELECT DISTINCT * FROM customer_events WHERE event_type IN ('page_view', 'click', 'scroll') ORDER BY created_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Analytics pipeline — deduplicate event stream",
            schema_hint="customer_events(id PK, user_id, event_type, page_url, metadata JSONB, created_at) — 200M rows, wide table",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["distinct *", "no limit", "full sort", "wide table"],
        ),
        SQLQuery(
            query_id="perf-007",
            sql="SELECT u.id, u.name, (SELECT MAX(o.created_at) FROM orders o WHERE o.user_id = u.id) AS last_order, (SELECT SUM(o.total) FROM orders o WHERE o.user_id = u.id) AS lifetime_value FROM users u WHERE u.active = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="CRM — customer lifetime value report",
            schema_hint="users(id PK, name, active BOOL) — 2M rows; orders(id, user_id FK, total, created_at) — 8M rows",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["correlated subquery", "N+1", "join", "lateral"],
        ),
        SQLQuery(
            query_id="perf-008",
            sql="SELECT id, title, body, author_id FROM blog_posts WHERE body LIKE '%kubernetes deployment strategy%' ORDER BY published_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Blog search — content search endpoint",
            schema_hint="blog_posts(id PK, title, body TEXT, author_id FK, published_at TIMESTAMP) — 850K rows, no full-text index",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["leading wildcard", "LIKE %", "full scan", "full-text search", "tsvector"],
        ),
        SQLQuery(
            query_id="perf-009",
            sql="SELECT id, amount, description FROM transactions WHERE EXTRACT(YEAR FROM created_at) = 2024 AND EXTRACT(MONTH FROM created_at) = 6 ORDER BY amount DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Finance — monthly transaction report",
            schema_hint="transactions(id PK, amount DECIMAL, description TEXT, created_at TIMESTAMP) — idx on created_at, 32M rows",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["function on index", "EXTRACT", "range scan", "sargable"],
        ),
        SQLQuery(
            query_id="perf-010",
            sql="SELECT p.id, p.name, p.price, (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id) AS review_count, (SELECT AVG(r.rating) FROM reviews r WHERE r.product_id = p.id) AS avg_rating FROM products p WHERE p.active = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Product listing — show products with ratings",
            schema_hint="products(id PK, name, price, active) — 45K rows; reviews(id, product_id FK, rating INT) — 2.3M rows",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["correlated subquery", "N+1", "join", "aggregate"],
        ),
        SQLQuery(
            query_id="perf-011",
            sql="SELECT id, name, phone FROM customers WHERE phone = 5551234567;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Customer support — phone number lookup",
            schema_hint="customers(id PK, name VARCHAR, phone VARCHAR) — idx on phone, 3.5M rows",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["type mismatch", "implicit cast", "varchar vs int", "index"],
        ),
        SQLQuery(
            query_id="perf-012",
            sql="SELECT id, subject, body, sender_id, recipient_id FROM messages WHERE sender_id = 42 OR recipient_id = 42 OR cc_list LIKE '%user:42%' ORDER BY sent_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Messaging — inbox view for user 42",
            schema_hint="messages(id PK, subject, body TEXT, sender_id FK, recipient_id FK, cc_list TEXT, sent_at TIMESTAMP) — 18M rows, separate idx on sender_id and recipient_id",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["OR", "multiple columns", "index", "UNION", "no limit"],
        ),
    ]


# ── Logic bug queries ────────────────────────────────────────────
# Queries that parse and execute but produce wrong results or cause
# data corruption.

def _logic_bug_queries() -> List[SQLQuery]:
    return [
        SQLQuery(
            query_id="bug-001",
            sql="DELETE FROM password_reset_tokens;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            context="Auth service — cleanup expired password reset tokens (cron job)",
            schema_hint="password_reset_tokens(id PK, user_id FK, token VARCHAR, expires_at TIMESTAMP) — only expired tokens should be removed",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["no where", "delete all", "unbounded", "missing condition"],
        ),
        SQLQuery(
            query_id="bug-002",
            sql="UPDATE accounts SET balance = 0, updated_at = NOW() WHERE status = 'active';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="Finance — year-end balance reset (was supposed to reset only test accounts)",
            schema_hint="accounts(id PK, balance DECIMAL, status VARCHAR, updated_at TIMESTAMP) — 340K active accounts",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["mass update", "balance zero", "all active", "destructive"],
        ),
        SQLQuery(
            query_id="bug-003",
            sql="SELECT u.id, u.email, o.id AS order_id, o.total FROM users u INNER JOIN orders o ON u.name = o.shipping_name WHERE o.status = 'pending';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Order service — pending orders with user details",
            schema_hint="users(id PK, name VARCHAR, email VARCHAR); orders(id PK, user_id FK, shipping_name VARCHAR, total DECIMAL, status VARCHAR)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["wrong join", "name instead of id", "duplicate", "incorrect join condition"],
        ),
        SQLQuery(
            query_id="bug-004",
            sql="UPDATE wallets SET balance = (SELECT balance FROM wallets WHERE user_id = $1) - $2 WHERE user_id = $1;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="Payment service — deduct wallet balance on purchase",
            schema_hint="wallets(user_id PK, balance DECIMAL, updated_at TIMESTAMP) — concurrent access expected",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["race condition", "TOCTOU", "concurrent", "FOR UPDATE", "atomic"],
        ),
        SQLQuery(
            query_id="bug-005",
            sql="UPDATE products SET price = price * -1, updated_at = NOW() WHERE category = 'electronics' AND price > 0;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="Catalog service — price adjustment batch job",
            schema_hint="products(id PK, price DECIMAL, category VARCHAR, updated_at TIMESTAMP) — 8.5K electronics products",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["negative price", "multiply -1", "data corruption"],
        ),
        SQLQuery(
            query_id="bug-006",
            sql="SELECT id, name, salary, department FROM employees WHERE salary > 50000 AND salary < 30000 AND active = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="HR — filter employees by salary range",
            schema_hint="employees(id PK, name, salary DECIMAL, department VARCHAR, active BOOL)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["impossible condition", "empty result", "contradictory", "> 50000 AND < 30000"],
        ),
        SQLQuery(
            query_id="bug-007",
            sql="INSERT INTO orders (user_id, total, status, created_at) VALUES (NULL, -49.99, 'completed', NOW());",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            context="Order service — create new order from checkout",
            schema_hint="orders(id SERIAL PK, user_id FK NOT NULL, total DECIMAL CHECK(total > 0), status VARCHAR, created_at TIMESTAMP)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["null user", "negative total", "constraint violation", "invalid data"],
        ),
        SQLQuery(
            query_id="bug-008",
            sql="UPDATE subscriptions SET status = 'expired', ended_at = NOW() WHERE renewal_date < CURRENT_DATE AND status = 'active';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="Billing service — expire overdue subscriptions (nightly cron)",
            schema_hint="subscriptions(id PK, user_id FK, status VARCHAR, renewal_date DATE, ended_at TIMESTAMP) — should expire only 30+ day overdue",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["off-by-one", "too aggressive", "grace period", "premature expiry"],
        ),
        SQLQuery(
            query_id="bug-009",
            sql="DROP TABLE IF EXISTS user_preferences CASCADE;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DROP",
            context="Migration script — cleanup step before schema change",
            schema_hint="user_preferences(user_id PK, theme, language, notifications_enabled) — 1.2M rows, referenced by user_settings",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["drop table", "cascade", "data loss", "production", "irreversible"],
        ),
        SQLQuery(
            query_id="bug-010",
            sql="SELECT id, user_id, amount, created_at FROM payments WHERE created_at >= '2025-12-31' AND created_at <= '2025-01-01' AND status = 'completed';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Finance — payments within date range for year-end report",
            schema_hint="payments(id PK, user_id FK, amount DECIMAL, created_at TIMESTAMP, status VARCHAR)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["inverted date", "empty result", "start > end", "impossible range"],
        ),
        SQLQuery(
            query_id="bug-011",
            sql="UPDATE users SET email = NULL, email_verified = false WHERE id > 0;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="User service — reset email verification for specific user (PR says 'for user id 42')",
            schema_hint="users(id PK, email VARCHAR NOT NULL, email_verified BOOL) — 2.1M rows",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["mass update", "all users", "null email", "WHERE id > 0", "missing specific id"],
        ),
        SQLQuery(
            query_id="bug-012",
            sql="DELETE FROM transactions WHERE amount IS NOT NULL OR amount IS NULL;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            context="Finance — archive old transactions (should be date-filtered)",
            schema_hint="transactions(id PK, amount DECIMAL, created_at TIMESTAMP) — 32M rows, should only delete where created_at < '2020-01-01'",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["always true", "tautology", "delete all", "IS NOT NULL OR IS NULL"],
        ),
    ]


# ── Multi-issue queries ──────────────────────────────────────────
# Queries with multiple problems simultaneously.

def _multi_issue_queries() -> List[SQLQuery]:
    return [
        SQLQuery(
            query_id="multi-001",
            sql="SELECT * FROM audit_logs WHERE actor_name = '{username}' ORDER BY created_at DESC;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Admin panel — view audit logs filtered by user",
            schema_hint="audit_logs(id PK, actor_name VARCHAR, action, details JSONB, created_at TIMESTAMP) — 65M rows",
            has_injection_risk=True, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "select *", "no limit", "full scan"],
        ),
        SQLQuery(
            query_id="multi-002",
            sql="DELETE FROM user_files WHERE owner_id = {user_id} AND expired = true;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            context="File service — cleanup expired files for a user",
            schema_hint="user_files(id PK, owner_id FK, filename, expired BOOL, created_at) — crafted user_id could wipe all files",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["injection", "delete", "interpolat", "destructive"],
        ),
        SQLQuery(
            query_id="multi-003",
            sql="SELECT id, name, email FROM customers WHERE LOWER(email) = LOWER('{email_input}') AND region = '{region}';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="CRM — customer lookup by email",
            schema_hint="customers(id PK, name, email VARCHAR, region VARCHAR) — idx on email, 3.5M rows",
            has_injection_risk=True, has_performance_issue=True, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "function on index", "LOWER()", "parameterized"],
        ),
        SQLQuery(
            query_id="multi-004",
            sql="UPDATE accounts SET balance = balance - {amount}, last_withdrawal = NOW() WHERE account_number = '{account_num}';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="Banking API — process withdrawal",
            schema_hint="accounts(account_number PK, balance DECIMAL CHECK(balance >= 0), last_withdrawal TIMESTAMP)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["injection", "no balance check", "negative balance", "parameterized"],
        ),
        SQLQuery(
            query_id="multi-005",
            sql="SELECT u.name, u.department, COUNT(t.id) AS task_count FROM users u, tasks t WHERE u.active = true AND (SELECT AVG(hours) FROM time_entries te WHERE te.user_id = u.id) > 4 GROUP BY u.name;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="PM dashboard — active users with high time commitment",
            schema_hint="users(id, name, department, active); tasks(id, assignee_id); time_entries(id, user_id, hours)",
            has_injection_risk=False, has_performance_issue=True, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["cartesian", "correlated subquery", "missing GROUP BY column", "department"],
        ),
    ]


# ── Adversarial queries ─────────────────────────────────────────
# Designed to fool LLMs: queries that LOOK dangerous but are safe,
# and queries that LOOK safe but have subtle bugs.

def _adversarial_queries() -> List[SQLQuery]:
    return [
        # SAFE: Looks like injection but uses parameterized query with a SQL comment
        SQLQuery(
            query_id="adv-001",
            sql="SELECT id, name, role FROM users WHERE id = $1 AND active = true; -- handles user login lookup",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Auth service — user lookup (parameterized, comment is developer note)",
            schema_hint="users(id PK, name VARCHAR, role VARCHAR, active BOOL)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["parameterized", "$1", "comment", "safe"],
        ),
        # SAFE: String literal contains scary SQL keywords but is just data
        SQLQuery(
            query_id="adv-002",
            sql="INSERT INTO audit_log (user_id, action, details, created_at) VALUES ($1, 'admin_action', 'User executed DROP TABLE command from admin UI', NOW());",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="INSERT",
            context="Audit service — logs admin actions, string is literal log message",
            schema_hint="audit_log(id SERIAL PK, user_id INT, action VARCHAR, details TEXT, created_at TIMESTAMP)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["literal string", "parameterized", "not injection", "audit"],
        ),
        # REJECT: Looks like a safe batch query but interpolates user input into ARRAY
        SQLQuery(
            query_id="adv-003",
            sql="SELECT o.id, o.total, o.status FROM orders o WHERE o.user_id = ANY(ARRAY[{user_ids}]) AND o.created_at > '2024-01-01' ORDER BY o.created_at DESC LIMIT 100;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="Order service — batch lookup for multiple users (called from admin API)",
            schema_hint="orders(id PK, user_id FK, total DECIMAL, status VARCHAR, created_at TIMESTAMP)",
            has_injection_risk=True, has_performance_issue=False, has_logic_bug=False, correct_verdict="reject",
            reasoning_keywords=["injection", "ARRAY", "interpolat", "parameterized"],
        ),
        # SAFE: Table name contains 'drop_table' but is a legitimate cleanup
        SQLQuery(
            query_id="adv-004",
            sql="DELETE FROM temp_drop_table_candidates WHERE analyzed_at < NOW() - INTERVAL '90 days' AND status = 'archived';",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="DELETE",
            context="DBA maintenance — cleanup old table analysis records (the table tracks tables considered for deletion)",
            schema_hint="temp_drop_table_candidates(id PK, table_name VARCHAR, analyzed_at TIMESTAMP, status VARCHAR)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=False, correct_verdict="approve",
            reasoning_keywords=["legitimate cleanup", "bounded delete", "where clause", "safe"],
        ),
        # REJECT: Subtle SQL syntax error — HAVING after ORDER BY
        SQLQuery(
            query_id="adv-005",
            sql="SELECT department, AVG(salary) AS avg_salary FROM employees WHERE active = true GROUP BY department ORDER BY avg_salary DESC HAVING avg_salary > 75000;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="SELECT",
            context="HR analytics — departments with high average salary",
            schema_hint="employees(id PK, department VARCHAR, salary DECIMAL, active BOOL)",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["HAVING after ORDER BY", "syntax", "wrong clause order", "GROUP BY"],
        ),
        # REJECT: Looks like proper parameterized query but has a subtle logic bug —
        # UPDATE without checking current status allows re-processing completed orders
        SQLQuery(
            query_id="adv-006",
            sql="UPDATE orders SET status = 'refunded', refunded_at = NOW(), refund_amount = $2 WHERE id = $1;",
            submitted_by=_rand_sub(), database=_rand_db(), query_type="UPDATE",
            context="Refund service — process refund for an order",
            schema_hint="orders(id PK, status VARCHAR, refunded_at TIMESTAMP, refund_amount DECIMAL) — status flow: pending->completed->refunded. Should only refund 'completed' orders",
            has_injection_risk=False, has_performance_issue=False, has_logic_bug=True, correct_verdict="reject",
            reasoning_keywords=["missing status check", "idempotency", "double refund", "state machine"],
        ),
    ]


# ── Master query pool ────────────────────────────────────────────
# Built once at import time with seed(42) for full reproducibility.

random.seed(42)
_ALL_QUERIES: List[SQLQuery] = (
    _safe_queries() + _injection_queries() + _performance_queries() +
    _logic_bug_queries() + _multi_issue_queries() + _adversarial_queries()
)
# Re-seed after building to ensure reproducibility on subsequent calls
random.seed(42)


def get_all_queries() -> List[SQLQuery]:
    """Return full query pool (62 queries)."""
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
        # 8 queries — mix of safe and problematic, include 1 adversarial
        safe = [q for q in pool if q.correct_verdict == "approve" and not q.query_id.startswith("adv")]
        reject = [q for q in pool if q.correct_verdict == "reject" and not q.query_id.startswith("adv")]
        adversarial = [q for q in pool if q.query_id.startswith("adv")]
        picked_safe = rng.sample(safe, min(2, len(safe)))
        picked_reject = rng.sample(reject, min(4, len(reject)))
        picked_adv = rng.sample(adversarial, min(2, len(adversarial)))
        result = picked_safe + picked_reject + picked_adv
        rng.shuffle(result)
        return result[:8]

    elif task_id == "pipeline_review":
        # 15 queries in 3 batches of 5, some marked urgent, includes adversarial
        safe = [q for q in pool if q.correct_verdict == "approve" and not q.query_id.startswith("adv")]
        reject = [q for q in pool if q.correct_verdict == "reject" and not q.query_id.startswith("adv")]
        adversarial = [q for q in pool if q.query_id.startswith("adv")]
        picked_safe = rng.sample(safe, min(4, len(safe)))
        picked_reject = rng.sample(reject, min(8, len(reject)))
        picked_adv = rng.sample(adversarial, min(3, len(adversarial)))
        result = picked_safe + picked_reject + picked_adv
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
