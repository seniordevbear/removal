# face_removal.py — helpers for the face-removal kind (kind=4) of the pipeline.
#
# Previously had:
#   DEFAULT_DB_CONFIG = {"host":"localhost","user":"root","password":"","database":"mattrhorn"}
# which is wrong on both axes (wrong host, wrong db name — leftover from a
# vendor's template). It would only fail safely because callers always
# passed an explicit config, but if a future refactor relied on the default,
# it would silently target the wrong database. Now we either accept an
# explicit config or pull from env (the same env keys manage.py uses), and
# never fall back to a fake one.
import os
import sys
import logging
from typing import Optional, Dict
from urllib.parse import quote

import mysql.connector

log = logging.getLogger("pd.face_removal")


def _db_config_from_env() -> Optional[Dict[str, object]]:
    """Returns a config dict if all required env vars are set, else None."""
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    if not (host and user and password):
        return None
    return {
        "host": host,
        "user": user,
        "password": password,
        "database": os.getenv("DB_NAME", "privacyduck"),
        "port": int(os.getenv("DB_PORT", "25060")),
        "ssl_ca": os.getenv("DB_SSL_CA", ""),
        "ssl_verify_cert": os.getenv("DB_SSL_VERIFY_CERT", "false").lower() in {"1", "true", "yes", "on"},
    }


ASSETS_UPLOAD_DIR = os.environ.get(
    "FACE_UPLOAD_DIR",
    os.path.join("assets", "uploads", "specialinfo"),
)


def get_user_face_image_path_from_filename(filename: str, base_dir: str = ASSETS_UPLOAD_DIR) -> str:
    """Mirror the PHP storage path: rawurlencode(filename) under specialinfo/."""
    encoded_name = quote(str(filename or ""), safe="")
    return os.path.join(base_dir, encoded_name)


def get_db_connection(db_config: Optional[Dict] = None) -> mysql.connector.MySQLConnection:
    cfg = db_config or _db_config_from_env()
    if cfg is None:
        raise RuntimeError(
            "face_removal: no DB config — pass one explicitly or set "
            "DB_HOST/DB_USER/DB_PASSWORD in .env"
        )
    return mysql.connector.connect(**cfg)


def get_user_image_filename(user_id: int, conn) -> Optional[str]:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT url FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()


def delete_image_file(filename: str, base_dir: str = ASSETS_UPLOAD_DIR) -> bool:
    if not filename:
        return False
    full_path = get_user_face_image_path_from_filename(filename, base_dir=base_dir)
    if not os.path.exists(full_path):
        return False
    try:
        os.remove(full_path)
        return True
    except OSError:
        log.exception("delete_image_file failed: %s", full_path)
        return False


def scrub_user_face_metadata(user_id: int, conn) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET url = NULL WHERE id = %s", (user_id,))
        conn.commit()
    finally:
        cursor.close()


def remove_user_face_data(user_id: int, db_config: Optional[Dict] = None) -> None:
    """Read filename -> delete file -> null out DB column. try/finally so a
    raise inside delete_image_file doesn't leave the conn open."""
    conn = get_db_connection(db_config)
    try:
        filename = get_user_image_filename(user_id, conn)
        if not filename:
            return
        delete_image_file(filename)
        scrub_user_face_metadata(user_id, conn)
    finally:
        try:
            conn.close()
        except Exception:
            log.exception("conn.close failed in remove_user_face_data")


def _cli() -> None:
    """python face_removal.py <user_id>"""
    if len(sys.argv) != 2:
        print("Usage: python face_removal.py <user_id>", file=sys.stderr)
        sys.exit(1)
    try:
        user_id = int(sys.argv[1])
    except ValueError:
        print("user_id must be an integer", file=sys.stderr)
        sys.exit(1)
    remove_user_face_data(user_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _cli()
