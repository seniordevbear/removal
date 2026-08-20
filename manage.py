# manage.py — orchestrator for the PrivacyDuck removal pipeline.
#
# Spawns 5 worker threads:
#   0 — process_groups()              kind=0 (scan) + kind=3 (google_scan)
#   1 — placeholder (no-op)           kept for back-compat with executor.map
#   2 — process_groups_removal()      kind=1 (removal)
#   3 — process_groups_face_removal() kind=4 (face removal)
#   4 — socketio.run()                Flask + Socket.IO server (blocking)
#
# Lifecycle invariants this rewrite enforces:
#   - Every MySQL connection acquired in a loop iteration is closed in a
#     try/finally. The previous version closed conns only on the happy
#     path; any exception inside the loop body leaked them, which after
#     ~hours of uptime exhausted the DO managed-MySQL connection budget.
#   - Cursors are explicitly closed (mysql-connector-python tracks cursors
#     per connection; orphaning them eats memory).
#   - All UPDATE statements use parameter substitution. Values come from the
#     DB so this isn't an injection risk per se, but it makes the queries
#     resilient against weird unicode in target_domain and gives prepared
#     statements a chance to cache.
#   - last_removal_processed_at is a bounded dict (~OrderedDict-as-LRU). The
#     old plain dict grew unbounded — one entry per user_id ever seen, never
#     evicted, costing real memory on the long-running process.
#   - upload_file_to_server has a request timeout, status-code check, and
#     stops trying to .json()-parse responses that aren't JSON.
#   - ModuleMissing from the dispatcher is caught distinctly and the row is
#     marked step=4 ("not implemented") instead of step=3 ("failed"), which
#     keeps the 376K unimplemented scan rows from polluting the failure
#     dashboards.
#
# step values used (results.step is an int, no enum constraint in the table):
#   0  queued
#   1  in_flight (claimed by a worker)
#   2  done
#   3  failed (broker module ran but errored)
#   4  not_implemented (no sites/<domain>.py file — informational, won't retry)
#   5  skipped_missing_pii (user record was incomplete; user must fix profile)
import os
import sys
import time
import json
import logging
import threading
import concurrent.futures
from collections import OrderedDict

import mysql.connector
import requests
from flask import Flask, request
from flask_socketio import SocketIO, join_room

from __scan import scan as scan_dispatch, ModuleMissing as ScanModuleMissing
from __scanGoogle import google_scan as google_scan_dispatch, ModuleMissing as GoogleScanModuleMissing
from __removal import (
    removal as removal_dispatch,
    ModuleMissing as RemovalModuleMissing,
    IncompletePII,
)
from lib.broker_helpers import CCPADailyLimitReached, ccpa_global_quota_reached
from __face_removal import face_removal
from lib.automation_delay import enable_automation_delays

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(message)s",
    stream=sys.stderr,
)
logging.getLogger("socketio").setLevel(logging.ERROR)
logging.getLogger("engineio").setLevel(logging.ERROR)
log = logging.getLogger("pd.removal")


# ----- env loading ----------------------------------------------------------

def _load_env_file(env_path):
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


def _get_env_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_env_int(key, default):
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


def _get_env_float(key, default):
    try:
        return float(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


_load_env_file(os.path.join(os.path.dirname(__file__), ".env"))
enable_automation_delays()


# ----- config ---------------------------------------------------------------

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
if not (DB_HOST and DB_USER and DB_PASSWORD):
    sys.exit("FATAL: DB_HOST / DB_USER / DB_PASSWORD env vars are required (check .env).")
DB_NAME = os.getenv("DB_NAME", "privacyduck")
DB_PORT = _get_env_int("DB_PORT", 25060)
DB_SSL_CA = os.getenv("DB_SSL_CA", "")
DB_SSL_VERIFY_CERT = _get_env_bool("DB_SSL_VERIFY_CERT", False)

REMOVAL_TARGET_DAYS_PER_USER = _get_env_float("REMOVAL_TARGET_DAYS_PER_USER", 7.0)
REMOVAL_TARGET_TOTAL_PER_USER = _get_env_int("REMOVAL_TARGET_TOTAL_PER_USER", 413)
REMOVAL_MIN_INTERVAL_SECONDS = _get_env_float("REMOVAL_MIN_INTERVAL_SECONDS", 0.0)
if REMOVAL_MIN_INTERVAL_SECONDS <= 0:
    REMOVAL_MIN_INTERVAL_SECONDS = max(
        1.0,
        (REMOVAL_TARGET_DAYS_PER_USER * 24 * 60 * 60) / max(1, REMOVAL_TARGET_TOTAL_PER_USER),
    )

# Cap on how many user_id->timestamp pairs we keep in last_removal_processed_at.
# Beyond this we evict oldest. At 10K entries the dict is ~1MB which is plenty
# of room without growing unbounded over weeks of uptime.
REMOVAL_INTERVAL_DICT_MAXSIZE = _get_env_int("REMOVAL_INTERVAL_DICT_MAXSIZE", 10000)

# How many removals run at once. Safe because every broker script builds its
# browser via ChromiumOptions().auto_port() (unique debug port + temp profile
# per instance), so parallel Chromes cannot collide. The two brokers that
# drive the ACTUAL desktop mouse/keyboard (pyautogui) are serialised through
# _desktop_lock below — those cannot overlap with each other.
# 12GB box: 3 removal browsers + the scan loops' browsers fits comfortably.
REMOVAL_CONCURRENCY = max(1, _get_env_int("REMOVAL_CONCURRENCY", 3))

UPLOAD_TIMEOUT_SECONDS = _get_env_float("UPLOAD_TIMEOUT_SECONDS", 30.0)
LOOP_IDLE_SLEEP_SECONDS = _get_env_float("LOOP_IDLE_SLEEP_SECONDS", 5.0)
PD_UPLOAD_SECRET = os.getenv("PD_UPLOAD_SECRET", "").strip()
if not PD_UPLOAD_SECRET:
    log.warning(
        "PD_UPLOAD_SECRET is not set in .env; PHP /…_api/upload endpoints "
        "will reject our uploads with 403 until both sides have the same "
        "secret. Set it on the web VPS first, then mirror here, then "
        "restart pd-removal."
    )

SCAN_UPLOAD_URL_TEMPLATE = os.getenv(
    "SCAN_UPLOAD_URL_TEMPLATE",
    "https://privacyduck.com/scan_api/upload?domain={domain}&user_id={user_id}",
)
GOOGLE_SCAN_UPLOAD_URL_TEMPLATE = os.getenv(
    "GOOGLE_SCAN_UPLOAD_URL_TEMPLATE",
    "https://privacyduck.com/googleScan_api/upload?domain={domain}&user_id={user_id}",
)
REMOVAL_UPLOAD_URL_TEMPLATE = os.getenv(
    "REMOVAL_UPLOAD_URL_TEMPLATE",
    "https://privacyduck.com/removal_api/upload?domain={domain}&user_id={user_id}",
)
FACE_REMOVAL_UPLOAD_URL_TEMPLATE = os.getenv(
    "FACE_REMOVAL_UPLOAD_URL_TEMPLATE",
    "https://privacyduck.com/faceremoval_api/upload?domain={domain}&user_id={user_id}",
)

SOCKET_SERVER_HOST = os.getenv("SOCKET_SERVER_HOST", "144.126.136.20")
SOCKET_SERVER_PORT = _get_env_int("SOCKET_SERVER_PORT", 443)
SOCKET_SERVER_SSL_CERT = os.getenv("SOCKET_SERVER_SSL_CERT", "C:/Certbot/live/sayloapp.com/fullchain.pem")
SOCKET_SERVER_SSL_KEY = os.getenv("SOCKET_SERVER_SSL_KEY", "C:/Certbot/live/sayloapp.com/privkey.pem")
SOCKET_SERVER_USE_SSL = _get_env_bool("SOCKET_SERVER_USE_SSL", True)

log.info(
    "config removal_pacing min_interval_seconds=%s target_days=%s target_total=%s",
    REMOVAL_MIN_INTERVAL_SECONDS, REMOVAL_TARGET_DAYS_PER_USER, REMOVAL_TARGET_TOTAL_PER_USER,
)


db_config = {
    "host": DB_HOST,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "port": DB_PORT,
    # Force the pure-Python driver. mysql-connector-python 9.x defaults to a
    # compiled C extension whose TLS stack hangs indefinitely against the
    # managed database — it ignores connection_timeout, so it never even
    # errors. The pure-Python path connects normally.
    "use_pure": True,
}
# Only pass SSL options when a CA file is actually configured. Passing
# ssl_ca="" made mysql-connector-python 9.x treat the empty string as a real
# CA path, so the TLS handshake hung forever against the managed database.
# (The old 2.2.9 connector silently ignored it.)
if DB_SSL_CA:
    db_config["ssl_ca"] = DB_SSL_CA
    db_config["ssl_verify_cert"] = DB_SSL_VERIFY_CERT


# ----- Flask + SocketIO -----------------------------------------------------

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def index():
    return "SocketIO Real-time Server"


@app.route("/health")
def health():
    """Simple liveness probe — useful for NSSM monitoring + load balancers."""
    return {"ok": True, "ts": int(time.time())}


@socketio.on("connect")
def handle_connect():
    log.info("client connected sid=%s", request.sid)


@socketio.on("join")
def handle_join(data):
    try:
        if isinstance(data, dict):
            user_id = data.get("user_id")
        else:
            user_id = str(data)
        if user_id:
            join_room(user_id)
            log.info("client joined user_id=%s", user_id)
        else:
            log.warning("join with no user_id")
    except Exception:
        log.exception("error handling join")


# ----- bounded LRU for per-user pacing --------------------------------------

class _BoundedDict(OrderedDict):
    """OrderedDict that drops the oldest entry once it exceeds maxsize."""

    def __init__(self, maxsize):
        super().__init__()
        self._maxsize = maxsize
        self._lock = threading.Lock()

    def set(self, key, value):
        with self._lock:
            if key in self:
                self.move_to_end(key)
            self[key] = value
            while len(self) > self._maxsize:
                self.popitem(last=False)

    def get_value(self, key):
        with self._lock:
            return self.get(key)


last_removal_processed_at = _BoundedDict(REMOVAL_INTERVAL_DICT_MAXSIZE)


# ----- shared DB helper -----------------------------------------------------

# Failure reasons are persisted into the existing `results.data` JSON column
# under a namespaced key rather than a new column, so no schema migration is
# needed against the shared production database. Query them with e.g.
#   SELECT target_domain, data->>'$.pipeline_last_error' AS err, COUNT(*)
#   FROM results WHERE kind=1 AND step=3 GROUP BY 1,2 ORDER BY 3 DESC;
# Previously the reason was only logged, so "why did 10,106 removals fail?"
# was unanswerable without grepping weeks of rotated service logs.
_ERR_KEY = "$.pipeline_last_error"
_ERR_AT_KEY = "$.pipeline_last_error_at"


def _set_step(conn, row_id, new_step, reason=None):
    """Single source of truth for step transitions. Parameterized.

    When `reason` is given it is recorded on the row; when it is absent (a
    success or a requeue) any previous reason is cleared, so a row's stored
    error always describes its current state rather than a stale past one.
    """
    cur = conn.cursor()
    try:
        if reason:
            sql = (
                "UPDATE results SET step = %s, data = JSON_SET("
                "COALESCE(data, '{}'), '" + _ERR_KEY + "', %s, "
                "'" + _ERR_AT_KEY + "', NOW()) WHERE id = %s"
            )
            params = (new_step, str(reason)[:255], row_id)
        else:
            sql = (
                "UPDATE results SET step = %s, data = JSON_REMOVE("
                "data, '" + _ERR_KEY + "', '" + _ERR_AT_KEY + "') WHERE id = %s"
            )
            params = (new_step, row_id)
        try:
            cur.execute(sql, params)
        except Exception:
            # Never lose a step transition because the JSON write failed
            # (old MySQL, malformed pre-existing JSON, column type change).
            log.exception("step %s id=%s: reason write failed, "
                          "falling back to plain update", new_step, row_id)
            conn.rollback()
            cur.execute("UPDATE results SET step = %s WHERE id = %s",
                        (new_step, row_id))
        conn.commit()
        if reason:
            log.info("step %s -> id=%s reason=%s", new_step, row_id, reason)
    finally:
        cur.close()


# ----- upload helper --------------------------------------------------------

def upload_file_to_server(url, file_path, attempts=3):
    """POST `file_path` as multipart to `url`. Returns parsed JSON on
    Content-Type: application/json, else returns the raw text on success,
    None on failure. Has a real timeout and surfaces failures via logging
    instead of swallowing them.

    Retries transient failures (network blips, 5xx) up to `attempts` times
    with a short backoff — evidence is the product here, so a single hiccup
    must not silently discard proof of a completed removal."""
    if not file_path or not os.path.exists(file_path):
        log.warning("upload skipped (file missing): %s", file_path)
        return None
    for attempt in range(1, attempts + 1):
        result = _upload_once(url, file_path)
        if result is _PERMANENT_FAILURE:
            return None  # 4xx: wrong secret/format/IP — retrying cannot help
        if result is not None:
            return result
        if attempt < attempts:
            log.warning("upload attempt %d/%d failed, retrying: %s", attempt, attempts, file_path)
            time.sleep(5 * attempt)
    return None


_PERMANENT_FAILURE = object()  # sentinel: do-not-retry upload outcome


def _upload_once(url, file_path):
    try:
        headers = {}
        if PD_UPLOAD_SECRET:
            # Authenticates us to the PHP upload endpoints. Bypasses CSRF
            # for server-to-server calls (the browser-CSRF path stays
            # intact for any future user-driven upload).
            headers["X-PD-Upload-Secret"] = PD_UPLOAD_SECRET
        with open(file_path, "rb") as fh:
            files = {"file": (os.path.basename(file_path), fh, "application/octet-stream")}
            resp = requests.post(url, files=files, headers=headers, timeout=UPLOAD_TIMEOUT_SECONDS)
        if not resp.ok:
            log.warning("upload non-2xx %s -> %s: %s", file_path, resp.status_code, resp.text[:200])
            # 4xx = permanent (bad secret, blocked IP, rejected format):
            # retrying cannot change the outcome. 5xx/timeouts are transient.
            return _PERMANENT_FAILURE if 400 <= resp.status_code < 500 else None
        ctype = resp.headers.get("content-type", "")
        if "application/json" in ctype:
            try:
                return resp.json()
            except json.JSONDecodeError:
                log.warning("upload claimed JSON content-type but body wasn't valid JSON: %s", resp.text[:200])
                return None
        return resp.text
    except Exception:
        log.exception("upload failed url=%s file=%s", url, file_path)
        return None


# ----- query helpers --------------------------------------------------------

def _fetch_pending(conn, query, params=()):
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(query, params)
        return cur.fetchall() or []
    finally:
        cur.close()


def get_pending_google_scan(conn):
    return _fetch_pending(conn, """
        SELECT t.*, u.email, u.firstname, u.lastname, u.city, u.zip, u.state, u.age
        FROM (SELECT * FROM results WHERE step = 0 AND kind = 3 LIMIT 1000) AS t
        LEFT JOIN users u ON t.user_id = u.id
    """)


def get_pending_scan(conn):
    return _fetch_pending(conn, """
        SELECT t.*, u.email, u.firstname, u.lastname, u.city, u.zip, u.state, u.age
        FROM (SELECT * FROM results WHERE step = 0 AND kind = 0 LIMIT 1000) AS t
        LEFT JOIN users u ON t.user_id = u.id
    """)


_CCPA_DOMAINS_CACHE = None

def _ccpa_email_domains():
    """Domains whose broker script is a CCPA email opt-out (subject to the
    global daily email cap). Discovered once by scanning sites/*.py for the
    run_ccpa_email_optout call, so no per-script registry has to be kept."""
    global _CCPA_DOMAINS_CACHE
    if _CCPA_DOMAINS_CACHE is None:
        found = set()
        sites_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sites")
        try:
            for fname in os.listdir(sites_dir):
                if not fname.endswith(".py"):
                    continue
                try:
                    with open(os.path.join(sites_dir, fname), "r", encoding="utf-8", errors="ignore") as f:
                        if "run_ccpa_email_optout" in f.read():
                            found.add(fname[:-3])
                except OSError:
                    continue
        except OSError:
            log.exception("could not scan sites/ for CCPA email brokers")
        _CCPA_DOMAINS_CACHE = found
        log.info("ccpa email brokers discovered: %d", len(found))
    return _CCPA_DOMAINS_CACHE


def get_pending_removal(conn, exclude_domains=()):
    # FAIRNESS FIX 2026-05-28: previous version had
    #   ORDER BY user_id ASC LIMIT 1000
    # which monopolized the first ~5 user_ids (they had 1164+ rows
    # combined). Every paid user with user_id > 58 was starved -- saw
    # ZERO removal activity even after weeks of paid service.
    #
    # New: ROW_NUMBER() window function partitions by user_id so each
    # user contributes up to 10 rows per tick. With ~100 paid users
    # that's a 1000-row batch divided fairly.
    return _fetch_pending(conn, """
        SELECT
            ranked.id, ranked.user_id, ranked.target_domain, ranked.step, ranked.kind,
            ranked.removal_url, ranked.site_url, ranked.planable,
            JSON_UNQUOTE(ranked.data->'$.email')       AS email,
            JSON_UNQUOTE(ranked.data->'$.firstname')   AS firstname,
            JSON_UNQUOTE(ranked.data->'$.lastname')    AS lastname,
            JSON_UNQUOTE(ranked.data->'$.age')         AS age,
            JSON_UNQUOTE(ranked.data->'$.city')        AS city,
            JSON_UNQUOTE(ranked.data->'$.zip')         AS zip,
            JSON_UNQUOTE(ranked.data->'$.state')       AS state,
            JSON_UNQUOTE(ranked.data->'$.phone')       AS phone,
            JSON_UNQUOTE(ranked.data->'$.address')     AS address,
            JSON_UNQUOTE(ranked.data->'$.birth_day')   AS birth_day,
            JSON_UNQUOTE(ranked.data->'$.birth_month') AS birth_month,
            JSON_UNQUOTE(ranked.data->'$.birth_year')  AS birth_year,
            JSON_UNQUOTE(ranked.data->'$.area_code')   AS area_code,
            JSON_UNQUOTE(ranked.data->'$.street')      AS street,
            JSON_UNQUOTE(ranked.data->'$.county')      AS county
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY id) AS rn
            FROM results
            WHERE step = 0 AND kind = 1 AND planable = 1 {exclude_clause}
        ) ranked
        LEFT JOIN users u ON u.id = ranked.user_id
        WHERE ranked.rn <= 10
        -- PRIORITY FIX 2026-06-02: newest paid users come first so a
        -- brand-new signup sees their first broker attempt in minutes.
        -- planedAt is set when dashboard_bootstrap creates kind=1 rows.
        -- COALESCE so users without planedAt sort to the end, not crash.
        ORDER BY COALESCE(u.planedAt, '1970-01-01') DESC, ranked.user_id ASC, ranked.id ASC
        LIMIT 1000
    """.format(exclude_clause=(
        "AND target_domain NOT IN (" + ",".join(["%s"] * len(exclude_domains)) + ")"
        if exclude_domains else ""
    )), tuple(exclude_domains))


def get_pending_face_removal(conn):
    return _fetch_pending(conn, """
        SELECT r.id, r.user_id, r.target_domain, r.step, r.kind, r.planable,
               u.email, u.url AS face_filename
        FROM results r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE r.step = 0 AND r.kind = 4 AND (r.planable = 1 OR r.planable IS NULL)
        ORDER BY r.user_id ASC, r.id ASC
        LIMIT 1000
    """)


def _claim_row(conn, row_id, kind, require_planable=False):
    """Atomic CAS: only sets step=1 if it's still step=0. Returns True on
    successful claim, False if someone else got it first."""
    cur = conn.cursor()
    try:
        if require_planable:
            cur.execute(
                "UPDATE results SET step = 1 WHERE id = %s AND step = 0 AND kind = %s AND planable = 1",
                (row_id, kind),
            )
        else:
            cur.execute(
                "UPDATE results SET step = 1 WHERE id = %s AND step = 0 AND kind = %s",
                (row_id, kind),
            )
        conn.commit()
        return cur.rowcount == 1
    finally:
        cur.close()


# ----- worker bodies --------------------------------------------------------

def process_groups_google_scan():
    """ONE tick — pulls up to 1000 google-scan rows and processes them all.
    Caller loops; we don't loop internally."""
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        data = get_pending_google_scan(conn)
        if not data:
            return
        log.info("google_scan tick: %d rows", len(data))
        for row in data:
            try:
                socketio.emit("progress", {
                    "id": row["id"], "user_id": row["user_id"],
                    "target_domain": row["target_domain"], "kind": 3,
                }, room=str(row["user_id"]))
                try:
                    path = google_scan_dispatch(
                        socketio, row["target_domain"], row["id"], row["user_id"],
                        row["email"], row["firstname"], row["lastname"],
                        row["city"], row["zip"], row["state"], row["age"],
                    )
                    _set_step(conn, row["id"], 2)
                    socketio.emit("complete", {
                        "id": row["id"], "user_id": row["user_id"],
                        "target_domain": row["target_domain"], "kind": 3,
                    }, room=str(row["user_id"]))
                    upload_file_to_server(
                        GOOGLE_SCAN_UPLOAD_URL_TEMPLATE.format(
                            domain=row["target_domain"], user_id=row["user_id"]),
                        path,
                    )
                except GoogleScanModuleMissing:
                    _set_step(conn, row["id"], 4, "module_missing")
                except Exception:
                    log.exception("google_scan row failed id=%s", row["id"])
                    _set_step(conn, row["id"], 3, "broker_raised")
            except Exception:
                log.exception("google_scan outer row error id=%s", row.get("id"))
    except Exception:
        log.exception("google_scan tick failed")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                log.exception("conn.close failed (google_scan)")


def process_groups():
    """Worker 0: scan loop (also pumps google_scan once per tick)."""
    while True:
        process_groups_google_scan()
        conn = None
        try:
            conn = mysql.connector.connect(**db_config)
            data = get_pending_scan(conn)
            if data:
                log.info("scan tick: %d rows", len(data))
                for row in data:
                    try:
                        # Policy May 2026: we used to upfront-reject any row
                        # whose user was missing city/zip/state/age and set
                        # step=5 so the scan loop would skip them forever
                        # (well, until the dashboard reset them). New policy:
                        # let the scan run regardless. Per-broker validation
                        # in the removal worker downstream raises
                        # IncompletePII for the brokers that genuinely need
                        # a missing field, and only those rows get marked
                        # step=5. Brokers that work with just name+email
                        # succeed for everyone.

                        socketio.emit("progress", {
                            "id": row["id"], "user_id": row["user_id"],
                            "target_domain": row["target_domain"], "kind": 0,
                        }, room=str(row["user_id"]))

                        try:
                            path = scan_dispatch(
                                socketio, row["target_domain"], row["id"], row["user_id"],
                                row["email"], row["firstname"], row["lastname"],
                                row["city"], row["zip"], row["state"], row["age"],
                            )
                            if path == "Not Found":
                                _set_step(conn, row["id"], 3, "not_found")
                            else:
                                _set_step(conn, row["id"], 2)
                                socketio.emit("complete", {
                                    "id": row["id"], "user_id": row["user_id"],
                                    "target_domain": row["target_domain"], "kind": 0,
                                }, room=str(row["user_id"]))
                                upload_file_to_server(
                                    SCAN_UPLOAD_URL_TEMPLATE.format(
                                        domain=row["target_domain"], user_id=row["user_id"]),
                                    path,
                                )
                        except (ScanModuleMissing, NotImplementedError):
                            _set_step(conn, row["id"], 4, "module_missing")
                        except Exception:
                            log.exception("scan row failed id=%s", row["id"])
                            _set_step(conn, row["id"], 3, "broker_raised")
                    except Exception:
                        log.exception("scan outer row error id=%s", row.get("id"))
        except Exception:
            log.exception("scan tick failed")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    log.exception("conn.close failed (scan)")
        time.sleep(LOOP_IDLE_SLEEP_SECONDS)


# ----- maintenance: stale-claim recovery + chrome reaper ---------------------

MAINTENANCE_INTERVAL_SECONDS = _get_env_float("MAINTENANCE_INTERVAL_SECONDS", 3600.0)
STALE_CLAIM_HOURS = _get_env_int("STALE_CLAIM_HOURS", 2)
CHROME_REAPER_ENABLED = _get_env_bool("CHROME_REAPER_ENABLED", True)
CHROME_MAX_AGE_MINUTES = _get_env_int("CHROME_MAX_AGE_MINUTES", 180)


def _recover_stale_claims():
    """Reset rows stuck at step=1 (claimed but never finished).

    A crash or power loss mid-task leaves claimed rows orphaned forever —
    the old --reset-claims flag existed for exactly this, but had to be run
    by hand and never was (16 rows were found stuck from previous crashes).
    No legitimate task runs anywhere near STALE_CLAIM_HOURS, and `results`
    bumps updated_at on every step change, so age == staleness.
    Only kinds 1 and 4 use the claim mechanism.
    """
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE results SET step = 0 "
                "WHERE step = 1 AND kind IN (1, 4) "
                "AND updated_at < NOW() - INTERVAL %s HOUR",
                (STALE_CLAIM_HOURS,),
            )
            conn.commit()
            if cur.rowcount:
                log.warning("stale-claim recovery: requeued %d orphaned step=1 rows", cur.rowcount)
        finally:
            cur.close()
    except Exception:
        log.exception("stale-claim recovery failed")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _reap_old_chrome():
    """Kill chrome processes older than CHROME_MAX_AGE_MINUTES.

    Most broker scripts create the page directly and only call page.quit()
    on the happy path, so crashes leak chromium processes; over days they
    exhaust RAM (this contributed to killing the previous server). No
    legitimate task keeps a browser open longer than the cutoff, so anything
    older is a leak — and killing it also frees any worker thread hung on a
    wedged browser, which would otherwise stall its pool slot forever.
    """
    if not CHROME_REAPER_ENABLED:
        return
    try:
        import psutil
    except ImportError:
        log.warning("chrome reaper: psutil not installed; skipping")
        return
    cutoff = time.time() - CHROME_MAX_AGE_MINUTES * 60
    killed = 0
    for proc in psutil.process_iter(["name", "create_time"]):
        try:
            name = (proc.info["name"] or "").lower()
            if not name.startswith("chrome"):
                continue
            if (proc.info["create_time"] or time.time()) < cutoff:
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            log.exception("chrome reaper: error on pid %s", getattr(proc, "pid", "?"))
    if killed:
        log.warning("chrome reaper: killed %d chrome processes older than %dmin",
                    killed, CHROME_MAX_AGE_MINUTES)


# Rows parked at step=5 (missing_pii) were never looked at again. The global
# PII check is only "does this user have a name?", and it runs in __removal.py
# *before* any module import or browser launch — so re-testing a parked row is
# a string comparison, not a page load.
#
# Since the signup redesign moved removal details to after payment, customers
# routinely complete their profile long after their rows were parked. At the
# time of writing 19,078 of the 19,189 parked rows belong to customers who now
# have a full name: real, paid-for removals that would otherwise never run.
#
# PII_REQUEUE_LIMIT bounds this so a row can never ping-pong between 5 and 0
# forever; the counter lives in the same JSON column as the error reason.
PII_REQUEUE_LIMIT = _get_env_int("PII_REQUEUE_LIMIT", 2)
PII_REQUEUE_BATCH = _get_env_int("PII_REQUEUE_BATCH", 2000)


def _requeue_recovered_pii():
    """Return step=5 rows to the queue once their owner has a usable name."""
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        try:
            # MySQL forbids LIMIT on a multi-table UPDATE, and forbids a
            # LIMIT subquery directly inside IN(...) — hence the single-table
            # UPDATE with the join wrapped in a derived table. CAST(...) keeps
            # the counter an integer; ->> alone yields a string and `+ 1`
            # would coerce it to a double (2.0).
            cur.execute(
                "UPDATE results r "
                "SET r.step = 0, "
                "    r.data = JSON_SET(COALESCE(r.data, '{}'), "
                "        '$.pii_requeues', "
                "        CAST(COALESCE(r.data->>'$.pii_requeues', 0) "
                "             AS UNSIGNED) + 1) "
                "WHERE r.id IN (SELECT id FROM ("
                "    SELECT r2.id FROM results r2 "
                "      JOIN users u ON u.id = r2.user_id "
                "    WHERE r2.kind = 1 AND r2.step = 5 "
                "      AND TRIM(COALESCE(u.firstname, '')) <> '' "
                "      AND TRIM(COALESCE(u.lastname, '')) <> '' "
                "      AND CAST(COALESCE(r2.data->>'$.pii_requeues', 0) "
                "               AS UNSIGNED) < %s "
                "    LIMIT %s) x)",
                (PII_REQUEUE_LIMIT, PII_REQUEUE_BATCH),
            )
            n = cur.rowcount
            conn.commit()
            if n:
                log.info("pii recovery: requeued %d parked row(s) whose "
                         "profile is now complete", n)
        finally:
            cur.close()
    except Exception:
        log.exception("pii requeue failed")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def maintenance_loop():
    """Worker 1 (the historically reserved slot): housekeeping.

    Runs stale-claim recovery immediately at startup — that is exactly when
    orphans from the previous run exist — then both tasks every interval.
    """
    _recover_stale_claims()
    _requeue_recovered_pii()
    while True:
        time.sleep(MAINTENANCE_INTERVAL_SECONDS)
        _recover_stale_claims()
        _reap_old_chrome()
        _requeue_recovered_pii()


# The only two brokers that drive the real desktop mouse/keyboard via
# pyautogui. Two of these at once would fight over the single cursor, so they
# take this lock. Every other broker is pure DrissionPage on its own debug
# port and needs no serialisation.
_DESKTOP_AUTOMATION_BROKERS = {"allantgroupcom", "digitalsegmentcom"}
_desktop_lock = threading.Lock()

# Users with a removal currently running, so two rows for the same user are
# never processed at the same time (keeps per-user pacing meaningful and
# avoids a user's own tasks racing each other).
_inflight_users = set()
_inflight_lock = threading.Lock()

# A broker crash is NOT a result. Previously every exception went straight to
# step=3 — the same step as "person not found on that site" — so customer
# reports counted CAPTCHA hiccups and site redesigns as completed checks.
# Now a crashed row is requeued (step=0) until the same DOMAIN has crashed
# DOMAIN_CRASHES_BEFORE_GIVEUP times today; only then do we conclude the
# broker script itself is broken and record step=3 (reason=broker_raised),
# so a genuinely broken script still cannot loop forever.
DOMAIN_CRASHES_BEFORE_GIVEUP = _get_env_int("DOMAIN_CRASHES_BEFORE_GIVEUP", 3)
_domain_crashes = {"date": None, "counts": {}}
_domain_crashes_lock = threading.Lock()


def _note_domain_crash(domain):
    """Count today's crashes for one broker domain; returns the new count."""
    import datetime
    today = datetime.date.today().isoformat()
    with _domain_crashes_lock:
        if _domain_crashes["date"] != today:
            _domain_crashes["date"] = today
            _domain_crashes["counts"] = {}
        n = _domain_crashes["counts"].get(domain, 0) + 1
        _domain_crashes["counts"][domain] = n
        return n


def _process_removal_row(row):
    """Run ONE removal end-to-end on its own DB connection.

    mysql-connector connections are not thread-safe, so each worker opens a
    short-lived connection for its claim/step writes rather than sharing the
    tick's connection.
    """
    user_id_str = str(row["user_id"])
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        if not _claim_row(conn, row["id"], kind=1, require_planable=True):
            return

        socketio.emit("progress", {
            "id": row["id"], "user_id": row["user_id"],
            "target_domain": row["target_domain"], "kind": 1,
        }, room=str(row["user_id"]))

        needs_desktop = row["target_domain"] in _DESKTOP_AUTOMATION_BROKERS
        try:
            if needs_desktop:
                _desktop_lock.acquire()
            try:
                path = removal_dispatch(
                    socketio, row["target_domain"], row["site_url"],
                    row["id"], row["user_id"],
                    row["email"], row["firstname"], row["lastname"],
                    row["city"], row["zip"], row["state"], row["age"],
                    row["address"], row["phone"],
                    row["birth_day"], row["birth_month"], row["birth_year"],
                    row["area_code"], row["street"], row["county"],
                )
            finally:
                if needs_desktop:
                    _desktop_lock.release()
            _set_step(conn, row["id"], 2)
            socketio.emit("complete", {
                "id": row["id"], "user_id": row["user_id"],
                "target_domain": row["target_domain"], "kind": 1,
            }, room=str(row["user_id"]))
            if path and os.path.exists(path):
                upload_file_to_server(
                    REMOVAL_UPLOAD_URL_TEMPLATE.format(
                        domain=row["target_domain"], user_id=row["user_id"]),
                    path,
                )
            else:
                # The broker "succeeded" but produced no evidence file — the
                # screenshot call failed and was swallowed inside the script.
                # The removal itself was performed, so step=2 stands, but this
                # must be loudly visible: evidence is what customer reports
                # (and dispute defences) are built on.
                log.warning(
                    "removal id=%s domain=%s user=%s completed WITHOUT evidence (path=%r)",
                    row["id"], row["target_domain"], row["user_id"], path)
            last_removal_processed_at.set(user_id_str, time.time())
        except (RemovalModuleMissing, NotImplementedError):
            _set_step(conn, row["id"], 4, "module_missing")
            # Don't update the pacing timer — a missing-module
            # "skip" shouldn't burn this user's rate window.
        except IncompletePII as e:
            _set_step(conn, row["id"], 5, "missing_pii:" + ",".join(e.args[0]))
        except CCPADailyLimitReached as e:
            # Boundary race: quota filled between selection and dispatch.
            # Leave at step=0; selection excludes this domain from the next
            # tick onward, and the counter resets at midnight.
            _set_step(conn, row["id"], 0)
            log.info("ccpa throttle: id=" + str(row["id"]) + " " + str(e))
        except Exception:
            log.exception("removal row failed id=%s", row["id"])
            crashes = _note_domain_crash(row["target_domain"])
            if crashes < DOMAIN_CRASHES_BEFORE_GIVEUP:
                _set_step(conn, row["id"], 0)
                log.info("broker crash %d/%d today for %s — row id=%s requeued",
                         crashes, DOMAIN_CRASHES_BEFORE_GIVEUP,
                         row["target_domain"], row["id"])
            else:
                _set_step(conn, row["id"], 3, "broker_raised")
            last_removal_processed_at.set(user_id_str, time.time())
    except Exception:
        log.exception("removal outer row error id=%s", row.get("id"))
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                log.exception("conn.close failed (removal worker)")
        with _inflight_lock:
            _inflight_users.discard(user_id_str)


_ccpa_exclusion_logged = [False]  # log the quota state change once, not every tick


def process_groups_removal():
    """Worker 2: removal loop.

    Selection excludes CCPA email brokers once today's global email budget is
    spent — previously those rows were claimed, raised CCPADailyLimitReached,
    and were reset to step=0 hundreds of times per tick, clogging each user's
    10-row fairness window so browser-automation work never got selected.

    Rows are then dispatched onto a small worker pool (REMOVAL_CONCURRENCY),
    at most one in-flight row per user. Atomic CAS claiming is kept, so this
    also stays safe if multiple instances ever run.
    """
    pool = concurrent.futures.ThreadPoolExecutor(
        max_workers=REMOVAL_CONCURRENCY, thread_name_prefix="removal-worker")
    while True:
        conn = None
        try:
            exclude = ()
            if ccpa_global_quota_reached():
                exclude = tuple(_ccpa_email_domains())
                if exclude and not _ccpa_exclusion_logged[0]:
                    log.info(
                        "ccpa quota spent — excluding %d email brokers from selection until midnight",
                        len(exclude))
                    _ccpa_exclusion_logged[0] = True
            elif _ccpa_exclusion_logged[0]:
                _ccpa_exclusion_logged[0] = False
                log.info("ccpa quota reset — email brokers back in selection")
            conn = mysql.connector.connect(**db_config)
            data = get_pending_removal(conn, exclude_domains=exclude)
            log.info("removal tick: %d rows (concurrency=%d)", len(data), REMOVAL_CONCURRENCY)
            conn.close()
            conn = None

            futures = []
            for row in data:
                user_id_str = str(row["user_id"])
                now_ts = time.time()
                last_ts = last_removal_processed_at.get_value(user_id_str)
                if last_ts and (now_ts - last_ts) < REMOVAL_MIN_INTERVAL_SECONDS:
                    continue
                with _inflight_lock:
                    if user_id_str in _inflight_users:
                        continue
                    _inflight_users.add(user_id_str)
                futures.append(pool.submit(_process_removal_row, row))

            # Barrier per tick: claimed rows are step=1 so a re-fetch couldn't
            # double-claim anyway, but waiting keeps pacing/in-flight state
            # simple and bounds how much work is ever queued at once.
            if futures:
                concurrent.futures.wait(futures)
                for f in futures:
                    if f.exception() is not None:
                        log.error("removal worker crashed: %r", f.exception())
        except Exception:
            log.exception("removal tick failed")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    log.exception("conn.close failed (removal)")
        time.sleep(LOOP_IDLE_SLEEP_SECONDS)


def process_groups_face_removal():
    """Worker 3: face-removal loop."""
    while True:
        conn = None
        try:
            conn = mysql.connector.connect(**db_config)
            data = get_pending_face_removal(conn)
            if data:
                log.info("face_removal tick: %d rows", len(data))
                for row in data:
                    try:
                        if not _claim_row(conn, row["id"], kind=4):
                            continue
                        socketio.emit("progress", {
                            "id": row["id"], "user_id": row["user_id"],
                            "target_domain": row["target_domain"], "kind": 4,
                        }, room=str(row["user_id"]))
                        try:
                            path = face_removal(
                                socketio, row["target_domain"], row["id"], row["user_id"],
                                row.get("email") or "",
                                row.get("face_filename") or "",
                                run_mode="non-headless",
                            )
                            _set_step(conn, row["id"], 2)
                            socketio.emit("complete", {
                                "id": row["id"], "user_id": row["user_id"],
                                "target_domain": row["target_domain"], "kind": 4,
                            }, room=str(row["user_id"]))
                            if path:
                                upload_file_to_server(
                                    FACE_REMOVAL_UPLOAD_URL_TEMPLATE.format(
                                        domain=row["target_domain"], user_id=row["user_id"]),
                                    path,
                                )
                            log.info("face_removal ok id=%s user=%s domain=%s",
                                     row["id"], row["user_id"], row["target_domain"])
                            try:
                                cur = conn.cursor()
                                try:
                                    cur.execute(
                                        "UPDATE users SET face_manual_removed = 1 WHERE id = %s",
                                        (row["user_id"],),
                                    )
                                    conn.commit()
                                finally:
                                    cur.close()
                            except Exception:
                                log.exception("face_removal users update failed user=%s", row["user_id"])
                        except Exception:
                            log.exception("face_removal row failed id=%s", row["id"])
                            _set_step(conn, row["id"], 3, "broker_raised")
                    except Exception:
                        log.exception("face_removal outer row error id=%s", row.get("id"))
        except Exception:
            log.exception("face_removal tick failed")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    log.exception("conn.close failed (face_removal)")
        time.sleep(LOOP_IDLE_SLEEP_SECONDS)


# ----- worker entry ---------------------------------------------------------

def runs(x):
    if x == 0:
        process_groups()
    elif x == 1:
        # Historically ran google_scan (now pumped from process_groups()).
        # Reused for housekeeping: stale-claim recovery + chrome reaper.
        maintenance_loop()
    elif x == 2:
        process_groups_removal()
    elif x == 3:
        process_groups_face_removal()
    else:
        ssl_context = None
        if SOCKET_SERVER_USE_SSL:
            ssl_context = (SOCKET_SERVER_SSL_CERT, SOCKET_SERVER_SSL_KEY)
        socketio.run(
            app,
            port=SOCKET_SERVER_PORT,
            host=SOCKET_SERVER_HOST,
            ssl_context=ssl_context,
            debug=False,
        )


if "--reset-claims" in sys.argv:
    _conn = mysql.connector.connect(**db_config)
    try:
        _cur = _conn.cursor()
        try:
            _cur.execute("UPDATE results SET step = 0 WHERE step = 1")
            _conn.commit()
            log.warning("--reset-claims: reset %d step=1 rows back to step=0", _cur.rowcount)
        finally:
            _cur.close()
    finally:
        _conn.close()


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(runs, range(5))
