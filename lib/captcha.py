# lib/captcha.py — single source of truth for the CAPTCHA-solver API key.
#
# History: the key was previously hardcoded inline in every broker script as
#   apiKey = "c1f41f9edead3997c405c3a31d00687c"
# That made rotation impossible (302+ files to change) and shipped the key
# in git forever. New scripts should `from lib.captcha import get_solver` and
# call `get_solver().turnstile(...)` / `.audio(...)`. Existing brokers can be
# migrated incrementally; this module is a no-op for them until they're
# refactored, but at least all future work has one place to set the key.
#
# Env: set TWOCAPTCHA_API_KEY in .env (or fall back to the legacy hardcoded
# value during the transition so we don't break the existing 302 brokers in
# one big-bang change).
import os
import threading
import sys

_LEGACY_KEY = "c1f41f9edead3997c405c3a31d00687c"  # see git history; will rotate
_TWOCAPTCHA_KEY = os.getenv("TWOCAPTCHA_API_KEY") or _LEGACY_KEY

_solver_lock = threading.Lock()
_solver_singleton = None


def get_solver():
    """Lazy singleton — TwoCaptcha() does no network work on construction but
    we'd rather not have hundreds of identical instances scattered across
    the broker scripts."""
    global _solver_singleton
    if _solver_singleton is not None:
        return _solver_singleton
    with _solver_lock:
        if _solver_singleton is None:
            try:
                from twocaptcha import TwoCaptcha
            except ImportError:
                print("[CAPTCHA] twocaptcha package not installed", file=sys.stderr)
                raise
            _solver_singleton = TwoCaptcha(_TWOCAPTCHA_KEY)
        return _solver_singleton


def get_api_key():
    """Used by brokers that pass the raw key to a custom call. Prefer
    get_solver() when possible — this is for migration only."""
    return _TWOCAPTCHA_KEY
