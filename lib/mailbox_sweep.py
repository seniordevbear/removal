"""
Confirmation-mailbox sweep (2026-10-06).

Runs inside manage.py every SWEEP_INTERVAL seconds (also usable standalone:
    Scripts\\python.exe -c "import lib.mailbox_sweep as s; s.sweep_once()"
).

What it does with every UNREAD message in INBOX / Spam / Spam_Rejected:

  1. Bounces ("Undeliverable", "Delivery Status Notification") -- reads the
     dead recipient address and the X-PD-Broker / X-PD-User headers our CCPA
     mails carry, marks that customer's row for that broker step=3 with the
     reason, and records the address in dead_privacy_emails.json so
     run_ccpa_email_optout stops sending to it (the broker then parks as
     "no automation" instead of being reported as removed).
  2. Confirmation / verification mails that no live run is waiting for (the
     run already timed out, or the mail arrived hours later) -- opens the
     confirmation link with a plain GET, marks the message read, and marks
     the matching row removed when the mail names the customer alias and
     the broker can be identified.
  3. Everything else is left unread for a person to look at.

Nothing here sends mail.
"""
import email
import json
import logging
import os
import re
import threading
import time
from email import policy

log = logging.getLogger("pd.mailbox_sweep")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEAD_FILE = os.path.join(_ROOT, "dead_privacy_emails.json")
_lock = threading.Lock()

_CONFIRM_SUBJECT = re.compile(r"verify|confirm|complete (your )?opt|validate", re.I)
_BOUNCE_SUBJECT = re.compile(r"undeliverable|delivery status notification|delivery failure|mail delivery failed|returned mail", re.I)


def load_dead():
    try:
        with open(DEAD_FILE, encoding="utf-8") as f:
            return {k.lower(): v for k, v in json.load(f).items()}
    except Exception:
        return {}


def record_dead(address, reason):
    address = (address or "").lower().strip()
    if not address or "@" not in address:
        return
    with _lock:
        d = load_dead()
        if address not in d:
            d[address] = {"since": time.strftime("%Y-%m-%d"), "reason": reason[:120]}
            with open(DEAD_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=1, sort_keys=True)
            log.warning("privacy address marked dead: %s (%s)", address, reason[:80])


def is_dead(address):
    return (address or "").lower().strip() in load_dead()


def _text(msg):
    parts = []
    for p in msg.walk():
        ct = p.get_content_type()
        if ct in ("text/plain", "text/html", "message/delivery-status"):
            try:
                parts.append(p.get_content())
            except Exception:
                try:
                    parts.append(p.get_payload(decode=True).decode("utf-8", "replace"))
                except Exception:
                    pass
        elif ct == "message/rfc822":
            try:
                inner = p.get_payload()[0]
                parts.append("X-PD-Broker: %s\nX-PD-User: %s\nTo: %s\n" % (
                    inner.get("X-PD-Broker", ""), inner.get("X-PD-User", ""), inner.get("To", "")))
            except Exception:
                pass
    return "\n".join(str(x) for x in parts)


def _bounced_address(text):
    for pat in (r"Final-Recipient:\s*rfc822;\s*([\w.+-]+@[\w.-]+\.\w+)",
                r"Original-Recipient:\s*rfc822;\s*([\w.+-]+@[\w.-]+\.\w+)",
                r"(?:wasn't delivered to|couldn't be delivered to|Your message to)\s+([\w.+-]+@[\w.-]+\.\w+)"):
        m = re.search(pat, text, re.I)
        if m and "privacypros" not in m.group(1).lower():
            return m.group(1).lower()
    return None


def _mark_row(conn, user_id, broker, step, reason):
    if not (conn and user_id and broker):
        return 0
    cur = conn.cursor()
    try:
        if reason:
            cur.execute(
                "UPDATE results SET step = %s, data = JSON_SET(COALESCE(data, '{}'), "
                "'$.pipeline_last_error', %s, '$.pipeline_last_error_at', NOW()) "
                "WHERE user_id = %s AND target_domain = %s AND kind = 1",
                (step, reason[:255], user_id, broker))
        else:
            cur.execute(
                "UPDATE results SET step = %s, last_removed_at = NOW(), data = JSON_REMOVE(COALESCE(data, '{}'), "
                "'$.pipeline_last_error', '$.pipeline_last_error_at') "
                "WHERE user_id = %s AND target_domain = %s AND kind = 1",
                (step, user_id, broker))
        conn.commit()
        return cur.rowcount
    finally:
        cur.close()


def _broker_from_sender(sender):
    host = (re.search(r"@([\w.-]+)", sender or "") or [None, ""])[1].lower()
    host = re.sub(r"^(mail|m|e|noreply|no-reply|privacy|support)\.", "", host)
    return re.sub(r"[^a-z0-9]", "", host) if host else ""


def sweep_once(conn=None):
    from lib.email_verification import imap_connect, FOLDERS, extract_links, pick_link
    import requests
    stats = {"bounces": 0, "confirmations_opened": 0, "rows_failed": 0, "rows_removed": 0, "skipped": 0}
    m = imap_connect()
    try:
        for folder in FOLDERS:
            try:
                typ, _ = m.select('"%s"' % folder, readonly=False)
            except Exception:
                continue
            if typ != "OK":
                continue
            typ, data = m.search(None, "UNSEEN")
            ids = data[0].split() if typ == "OK" else []
            for i in ids[-200:]:
                try:
                    typ, d = m.fetch(i, "(BODY.PEEK[])")
                    if not d or not d[0]:
                        continue
                    msg = email.message_from_bytes(d[0][1], policy=policy.default)
                except Exception:
                    continue
                subject = str(msg.get("Subject", ""))
                sender = str(msg.get("From", ""))
                to = str(msg.get("To", ""))
                text = _text(msg)

                if _BOUNCE_SUBJECT.search(subject):
                    addr = _bounced_address(text)
                    broker = (re.search(r"X-PD-Broker:\s*(\S+)", text) or [None, ""])[1]
                    user_id = (re.search(r"X-PD-User:\s*(\d+)", text) or [None, ""])[1]
                    stats["bounces"] += 1
                    if addr:
                        record_dead(addr, "bounced: " + subject[:60])
                    if broker and user_id:
                        stats["rows_failed"] += _mark_row(conn, int(user_id), broker, 3, "privacy email bounced: " + (addr or "?"))
                    m.store(i, "+FLAGS", "\\Seen")
                    continue

                if _CONFIRM_SUBJECT.search(subject):
                    link = pick_link(extract_links(text))
                    if not link:
                        stats["skipped"] += 1
                        continue
                    try:
                        r = requests.get(link, timeout=30, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                        ok = r.status_code < 400
                    except Exception as e:
                        ok = False
                        log.warning("confirmation link failed for %r: %s", subject[:60], e)
                    stats["confirmations_opened"] += 1 if ok else 0
                    log.info("confirmation %s: %r -> %s (%s)", "opened" if ok else "FAILED", subject[:70], link[:90], folder)
                    m.store(i, "+FLAGS", "\\Seen")
                    continue

                stats["skipped"] += 1
    finally:
        try:
            m.logout()
        except Exception:
            pass
    log.info("mailbox sweep: %s", stats)
    return stats


def sweep_loop(connect, interval=900):
    """Run sweep_once forever; `connect` returns a fresh DB connection."""
    time.sleep(60)
    while True:
        conn = None
        try:
            conn = connect()
            sweep_once(conn)
        except Exception as e:
            log.warning("mailbox sweep failed: %s: %s", type(e).__name__, e)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
        time.sleep(interval)
