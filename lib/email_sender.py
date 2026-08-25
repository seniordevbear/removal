# lib/email_sender.py — SMTP sender for the email-based broker opt-outs.
#
# Credentials come from env (.env): CONFIRMATION_EMAIL_* / FROM_EMAIL.
#
# 2026-08-25: added a HARD daily send cap. The 78 GDPR/EU broker scripts call
# send_email() with no throttle, all sending as confirmation@privacypros.com
# through mail1.privacypros.com. Once the pipeline sped up they pushed past
# SurgeMail's 500/day warning (user_send_max=5000) from IP 80.190.77.59 —
# the same kind of burst that damages sending reputation. This mirrors the
# CCPA path's global cap. When the budget is spent, send_email raises
# CCPADailyLimitReached, which manage.py already catches and leaves the row
# at step=0 to retry tomorrow (no failure, no lost work). Fail-closed: an
# unreadable counter is treated as spent, never as unlimited.
import os
import json
import time
import datetime
import smtplib
import logging
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from lib.broker_helpers import CCPADailyLimitReached

log = logging.getLogger("pd.email_sender")

SMTP_SERVER = os.getenv("CONFIRMATION_IMAP_SERVER", "mail1.privacypros.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("CONFIRMATION_EMAIL_USER", "confirmation")
SMTP_PASSWORD = os.getenv("CONFIRMATION_EMAIL_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "confirmation@privacypros.com")
SMTP_TIMEOUT = float(os.getenv("SMTP_TIMEOUT", "20"))

# Global daily cap for THIS sender. Combined with the CCPA path's 50/day,
# the account stays well under SurgeMail's 500 warning threshold. Tunable
# via .env; keep (this + 50) < 500.
try:
    EMAIL_SENDER_TOTAL_PER_DAY = int(os.getenv("EMAIL_SENDER_TOTAL_PER_DAY", "250"))
except ValueError:
    EMAIL_SENDER_TOTAL_PER_DAY = 250

_COUNTER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "email_sender_counter.json")
_counter_lock = threading.Lock()


def _reserve_daily_slot():
    """Increment today's counter; raise CCPADailyLimitReached if at the cap.
    Fail-closed: an unreadable/corrupt counter is treated as fully spent."""
    today = datetime.date.today().isoformat()
    with _counter_lock:
        try:
            with open(_COUNTER_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except FileNotFoundError:
            state = {"date": today, "count": 0}
        except (json.JSONDecodeError, OSError):
            log.error("email_sender counter unreadable — treating today as "
                      "spent (fail closed): %s", _COUNTER_PATH)
            raise CCPADailyLimitReached("email_sender counter unreadable")
        if state.get("date") != today:
            state = {"date": today, "count": 0}
        cur = int(state.get("count", 0))
        if cur >= EMAIL_SENDER_TOTAL_PER_DAY:
            raise CCPADailyLimitReached(
                "email_sender daily cap reached %d/%d"
                % (cur, EMAIL_SENDER_TOTAL_PER_DAY))
        state["count"] = cur + 1
        tmp = _COUNTER_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _COUNTER_PATH)
        return cur + 1


def send_email(to_email, subject, body):
    """Send a plain-text email via SMTP+STARTTLS. Returns True on success.
    Raises CCPADailyLimitReached when the daily cap is spent (manage.py
    catches it and leaves the row at step=0 for tomorrow)."""
    if not SMTP_PASSWORD:
        log.error("send_email skipped: CONFIRMATION_EMAIL_PASSWORD not set")
        return False
    if not to_email:
        log.warning("send_email skipped: empty to_email")
        return False

    # Reserve BEFORE connecting — raises if the budget is spent, so we never
    # open an SMTP session we're not allowed to use.
    n = _reserve_daily_slot()
    if n >= EMAIL_SENDER_TOTAL_PER_DAY - 25:
        log.warning("email_sender near daily cap: %d/%d",
                    n, EMAIL_SENDER_TOTAL_PER_DAY)

    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    server = None
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        log.info("send_email ok (%d/%d today) to=%s subject=%r",
                 n, EMAIL_SENDER_TOTAL_PER_DAY, to_email, subject[:60])
        return True
    except Exception:
        log.exception("send_email failed to=%s subject=%r", to_email, subject[:60])
        return False
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass
