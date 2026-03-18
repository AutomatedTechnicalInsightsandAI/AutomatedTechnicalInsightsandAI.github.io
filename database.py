"""
SQLite database layer for the SEO Audit Platform.
"""

import sqlite3
import json
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DATABASE_PATH", "seo_audits.db")


def _get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create database tables if they do not already exist."""
    try:
        with _get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT,
                    customer_email TEXT NOT NULL,
                    website_url TEXT NOT NULL,
                    business_name TEXT,
                    keyword TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    seo_score INTEGER,
                    audit_results_json TEXT,
                    report_html TEXT,
                    report_pdf_path TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id INTEGER,
                    message TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (audit_id) REFERENCES audit_requests(id)
                )
            """)
            conn.commit()
        logger.info("Database initialised at %s", DB_PATH)
    except sqlite3.Error as exc:
        logger.error("Failed to initialise database: %s", exc)
        raise


def create_audit_request(
    url: str,
    email: str,
    business_name: str = "",
    contact_name: str = "",
    keyword: str = "",
) -> int:
    """
    Insert a new audit request and return its generated id.
    """
    now = datetime.now(timezone.utc).isoformat()
    try:
        with _get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO audit_requests
                    (customer_name, customer_email, website_url, business_name, keyword, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (contact_name, email, url, business_name, keyword, now),
            )
            conn.commit()
            return cur.lastrowid
    except sqlite3.Error as exc:
        logger.error("create_audit_request failed: %s", exc)
        raise


def update_audit_status(
    audit_id: int,
    status: str,
    seo_score: Optional[int] = None,
    audit_results: Optional[Dict[str, Any]] = None,
    report_html: Optional[str] = None,
    report_pdf_path: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """Update the status (and optional fields) of an existing audit record."""
    now = datetime.now(timezone.utc).isoformat()
    completed_at = now if status in ("completed", "failed") else None
    results_json = json.dumps(audit_results) if audit_results is not None else None

    try:
        with _get_connection() as conn:
            conn.execute(
                """
                UPDATE audit_requests
                SET status = ?,
                    seo_score = COALESCE(?, seo_score),
                    audit_results_json = COALESCE(?, audit_results_json),
                    report_html = COALESCE(?, report_html),
                    report_pdf_path = COALESCE(?, report_pdf_path),
                    error_message = COALESCE(?, error_message),
                    completed_at = COALESCE(?, completed_at)
                WHERE id = ?
                """,
                (
                    status,
                    seo_score,
                    results_json,
                    report_html,
                    report_pdf_path,
                    error_message,
                    completed_at,
                    audit_id,
                ),
            )
            conn.commit()
    except sqlite3.Error as exc:
        logger.error("update_audit_status failed for id=%s: %s", audit_id, exc)
        raise


def get_audit_by_id(audit_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single audit record by id. Returns None if not found."""
    try:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM audit_requests WHERE id = ?", (audit_id,)
            ).fetchone()
            if row is None:
                return None
            record = dict(row)
            if record.get("audit_results_json"):
                try:
                    record["audit_results"] = json.loads(record["audit_results_json"])
                except json.JSONDecodeError:
                    record["audit_results"] = {}
            return record
    except sqlite3.Error as exc:
        logger.error("get_audit_by_id failed for id=%s: %s", audit_id, exc)
        return None


def get_all_audits(limit: int = 100) -> List[Dict[str, Any]]:
    """Return the most recent *limit* audit records (excluding full HTML/JSON blobs)."""
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, customer_name, customer_email, website_url, business_name,
                       keyword, status, seo_score, error_message, created_at, completed_at
                FROM audit_requests
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_all_audits failed: %s", exc)
        return []


def get_pending_audits() -> List[Dict[str, Any]]:
    """Return all audits with status 'pending' or 'processing'."""
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, customer_name, customer_email, website_url, business_name,
                       keyword, status, created_at
                FROM audit_requests
                WHERE status IN ('pending', 'processing')
                ORDER BY created_at ASC
                """,
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_pending_audits failed: %s", exc)
        return []


def get_monthly_analytics() -> Dict[str, Any]:
    """
    Return aggregated monthly statistics:
    - audits_per_month: list of {month, count}
    - avg_score_per_month: list of {month, avg_score}
    - status_distribution: {status: count}
    - top_issues: list of common failing check names
    """
    try:
        with _get_connection() as conn:
            # Monthly audit counts
            monthly_counts = conn.execute(
                """
                SELECT strftime('%Y-%m', created_at) AS month,
                       COUNT(*) AS count
                FROM audit_requests
                GROUP BY month
                ORDER BY month
                """
            ).fetchall()

            # Monthly average scores (completed only)
            avg_scores = conn.execute(
                """
                SELECT strftime('%Y-%m', created_at) AS month,
                       ROUND(AVG(seo_score), 1) AS avg_score
                FROM audit_requests
                WHERE status = 'completed' AND seo_score IS NOT NULL
                GROUP BY month
                ORDER BY month
                """
            ).fetchall()

            # Status distribution
            status_dist = conn.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM audit_requests
                GROUP BY status
                """
            ).fetchall()

            # Top issues — parse JSON blobs
            issue_counter: Dict[str, int] = {}
            rows = conn.execute(
                "SELECT audit_results_json FROM audit_requests WHERE audit_results_json IS NOT NULL"
            ).fetchall()
            for row in rows:
                try:
                    data = json.loads(row[0])
                    for check in data.get("checks", []):
                        if check.get("status") == "fail":
                            name = check.get("name", "Unknown")
                            issue_counter[name] = issue_counter.get(name, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass

            top_issues = sorted(issue_counter.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "audits_per_month": [dict(r) for r in monthly_counts],
                "avg_score_per_month": [dict(r) for r in avg_scores],
                "status_distribution": {r["status"]: r["count"] for r in status_dist},
                "top_issues": [{"issue": k, "count": v} for k, v in top_issues],
            }
    except sqlite3.Error as exc:
        logger.error("get_monthly_analytics failed: %s", exc)
        return {
            "audits_per_month": [],
            "avg_score_per_month": [],
            "status_distribution": {},
            "top_issues": [],
        }


def get_db_stats() -> Dict[str, Any]:
    """
    Return live diagnostics about the SQLite database:
    - absolute file path
    - file size in KB
    - row counts for every table
    - SQLite version
    - connection status
    """
    stats: Dict[str, Any] = {
        "db_path": os.path.abspath(DB_PATH),
        "connected": False,
        "sqlite_version": "",
        "file_size_kb": None,
        "tables": {},
        "error": None,
    }

    # File size (may be 0 if DB hasn't been flushed yet)
    try:
        size_bytes = os.path.getsize(DB_PATH)
        stats["file_size_kb"] = round(size_bytes / 1024, 1)
    except OSError:
        stats["file_size_kb"] = 0

    try:
        with _get_connection() as conn:
            stats["connected"] = True
            stats["sqlite_version"] = conn.execute("SELECT sqlite_version()").fetchone()[0]

            # Only report on known application tables to avoid dynamic SQL on
            # arbitrary schema names (prevents SQL injection via schema manipulation).
            _KNOWN_TABLES = {"audit_requests", "admin_notifications"}
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            for (tbl,) in tables:
                if tbl not in _KNOWN_TABLES:
                    # Skip internal SQLite tables (e.g. sqlite_sequence)
                    continue
                try:
                    # Table name is validated against the whitelist above.
                    count = conn.execute(f"SELECT COUNT(*) FROM \"{tbl}\"").fetchone()[0]
                    stats["tables"][tbl] = count
                except sqlite3.Error:
                    stats["tables"][tbl] = "?"
    except sqlite3.Error as exc:
        stats["error"] = str(exc)
        logger.error("get_db_stats failed: %s", exc)

    return stats


def get_recent_audits(days: int = 30) -> List[Dict[str, Any]]:
    """Return audits created within the last *days* days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, customer_name, customer_email, website_url, business_name,
                       keyword, status, seo_score, created_at, completed_at
                FROM audit_requests
                WHERE created_at >= ?
                ORDER BY created_at DESC
                """,
                (cutoff,),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_recent_audits failed: %s", exc)
        return []
