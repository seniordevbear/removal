"""
Confirmation-mailbox access for brokers that e-mail a link.

2026-10-06 rewrite. The old version drove the SurgeMail webmail UI
(https://mail1.privacypros.com/surgeweb), which has been refusing
connections; every e-mail-link broker died at that step. The mail server's
IMAP port is fine, and the messages were all there -- 9,000+ unread, most of
them filed into the Spam / Spam_Rejected folders where nothing looked.

This reads the mailbox over IMAP instead:

  do_email_verification(site_name, screenshot_path, after_click=None,
                        to_address=None, wait_seconds=120)

  * polls INBOX, Spam and Spam_Rejected for a message addressed to
    `to_address` (the generated privacyprosremoval.com alias) or, failing
    that, one whose From/Subject mentions `site_name`
  * picks the most confirmation-looking link in it, opens it in Chrome,
    screenshots the result, hands the tab to `after_click` if given,
    marks the message as read, returns True
  * returns False when no such message arrived within `wait_seconds`

Configuration (.env): CONFIRMATION_IMAP_SERVER, CONFIRMATION_EMAIL_USER,
CONFIRMATION_EMAIL_PASSWORD -- the same values email_sender.py uses. To move
the mailbox to Google Workspace later, point these at imap.gmail.com and a
privacyduck.com mailbox; nothing else changes.
"""
import email
import imaplib
import threading
import logging
import os
import re
import socket
import time
from email import policy
from time import sleep

from DrissionPage import ChromiumOptions, ChromiumPage

log = logging.getLogger("pd.email_verification")

IMAP_HOST = os.getenv("CONFIRMATION_IMAP_SERVER", "mail1.privacypros.com")
IMAP_PORT = int(os.getenv("CONFIRMATION_IMAP_PORT", "993"))
IMAP_USER = os.getenv("CONFIRMATION_EMAIL_USER", "confirmation")
IMAP_PASSWORD = os.getenv("CONFIRMATION_EMAIL_PASSWORD", "")
# Folder names differ per server: SurgeMail calls them Spam / Spam_Rejected,
# Gmail calls its spam folder "[Gmail]/Spam". Both sets are listed by default
# and the ones that do not exist are skipped, so no setting has to change when
# the mailbox moves.
FOLDERS = [f.strip() for f in os.getenv(
    "CONFIRMATION_IMAP_FOLDERS",
    "INBOX,Spam,Spam_Rejected,[Gmail]/Spam,[Gmail]/All Mail").split(",") if f.strip()]

# link words in order of preference
# "dsar": CoStar's verification link is privacy.costar.com/DSAR-submission/?key=...
# and carried none of the other words, so 26 mails on 26 Oct were "found but
# no confirmation link".
_LINK_WORDS = ("verify-dsr", "verify", "confirm", "removalrequest", "opt-out", "optout", "dsar",
               "removal", "remove", "validate", "activate", "token", "dsr")
_SKIP_WORDS = ("unsubscribe", "privacy-policy", "privacypolicy", "terms", "zendesk.com/support",
               "customeriomail.com/unsubscribe", "facebook.com", "twitter.com", "linkedin.com",
               "mail1.privacypros.com")


def get_chromium_options(arguments):
    options = ChromiumOptions()
    for argument in arguments:
        options.set_argument(argument)
    return options


def imap_connect():
    if not IMAP_PASSWORD:
        raise RuntimeError("CONFIRMATION_EMAIL_PASSWORD is not set; cannot read the confirmation mailbox")
    socket.setdefaulttimeout(40)
    # Explicit per-connection timeout as well: the global default only
    # applies to sockets created while it is set, and the 24 Oct stall dumps
    # had seven workers parked in imaplib.readline with nothing coming back.
    m = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=40)
    m.login(IMAP_USER, IMAP_PASSWORD)
    return m


def message_text(msg):
    parts = []
    for p in msg.walk():
        ct = p.get_content_type()
        if ct in ("text/plain", "text/html"):
            try:
                parts.append(p.get_content())
            except Exception:
                try:
                    parts.append(p.get_payload(decode=True).decode("utf-8", "replace"))
                except Exception:
                    pass
    return "\n".join(str(x) for x in parts)


def extract_links(text):
    text = text.replace("&amp;", "&").replace("=\n", "")
    links = re.findall(r'https?://[^\s"\'<>\)\]]+', text)
    out = []
    for u in links:
        u = u.rstrip(".,;")
        if any(w in u.lower() for w in _SKIP_WORDS):
            continue
        if u not in out:
            out.append(u)
    return out


def pick_link(links):
    for word in _LINK_WORDS:
        for u in links:
            if word in u.lower():
                return u
    return None


def _search_ids(m, since_days):
    since = time.strftime("%d-%b-%Y", time.gmtime(time.time() - since_days * 86400))
    typ, data = m.search(None, "SINCE", since)
    return data[0].split() if typ == "OK" else []


def find_message(m, to_address=None, site_name=None, since_days=3):
    """Yield (folder, id, msg) for candidates, newest first."""
    to_l = (to_address or "").lower()
    site_l = (site_name or "").lower()
    site_l = re.sub(r"(com|org|net|io|co|us)$", "", site_l) if site_l else ""
    for folder in FOLDERS:
        try:
            typ, _ = m.select('"%s"' % folder, readonly=False)
        except Exception:
            continue
        if typ != "OK":
            continue
        for i in reversed(_search_ids(m, since_days)):
            try:
                typ, d = m.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT TO)])")
                raw = d[0][1].decode("utf-8", "replace") if d and d[0] else ""
            except Exception:
                continue
            raw_l = raw.lower()
            if to_l and to_l in raw_l:
                yield folder, i
            elif site_l and not to_l and site_l in raw_l:
                yield folder, i


def open_link_in_browser(url, screenshot_save_path, after_click=None):
    options = get_chromium_options(["-no-first-run", "--start-maximized", "-disable-gpu"]).auto_port()
    driver = ChromiumPage(addr_or_opts=options)
    try:
        driver.get(url)
        sleep(6)
        try:
            driver.get_screenshot(screenshot_save_path)
        except Exception:
            pass
        if after_click is not None:
            after_click(driver.latest_tab)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


# Gmail IMAP has limits a self-hosted mailbox never had: about 15
# simultaneous connections per account and a daily command/bandwidth budget.
# The first version of this loop opened a fresh IMAP4_SSL login every 15 s per
# worker for up to 120 s - eight logins per row, six workers, plus the sweep -
# and on the morning of 15 Oct half of contactout's failures read
# "[ALERT] Account exceeded command or bandwidth limits". One connection per
# wait, at most two IMAP sessions at once across the process, a slower poll,
# and Gmail's throttle answered with a pause rather than a failed removal.
_IMAP_SLOTS = threading.BoundedSemaphore(int(os.getenv("CONFIRMATION_IMAP_MAX_SESSIONS", "2")))
_POLL_SECONDS = float(os.getenv("CONFIRMATION_POLL_SECONDS", "20"))
_THROTTLE_PAUSE = float(os.getenv("CONFIRMATION_THROTTLE_PAUSE", "60"))


def _is_throttle(exc):
    t = str(exc).lower()
    return ("exceeded command or bandwidth" in t or "too many simultaneous" in t
            or "temporarily unavailable" in t or "[throttled]" in t)


def do_email_verification(site_name, screenshot_save_path, after_click=None,
                          to_address=None, wait_seconds=120):
    deadline = time.time() + wait_seconds
    m = None
    try:
        with _IMAP_SLOTS:
            while True:
                try:
                    if m is None:
                        m = imap_connect()
                    for folder, i in find_message(m, to_address=to_address, site_name=site_name):
                        typ, d = m.fetch(i, "(BODY.PEEK[])")
                        if not d or not d[0]:
                            continue
                        msg = email.message_from_bytes(d[0][1], policy=policy.default)
                        subject = str(msg.get("Subject", ""))
                        if re.search(r"undeliverable|delivery status|spam report", subject, re.I):
                            continue
                        link = pick_link(extract_links(message_text(msg)))
                        if not link:
                            log.info("[%s] mail found (%s) but no confirmation link; subject=%r", site_name, folder, subject[:80])
                            try:
                                m.store(i, "+FLAGS", "\\Seen")
                            except Exception:
                                pass
                            continue
                        log.info("[%s] confirmation mail in %s: %r -> opening %s", site_name, folder, subject[:80], link[:100])
                        try:
                            m.store(i, "+FLAGS", "\\Seen")
                        except Exception:
                            pass
                        open_link_in_browser(link, screenshot_save_path, after_click=after_click)
                        return True
                except (imaplib.IMAP4.error, OSError) as e:
                    # Drop the connection; reconnect on the next pass. A throttle
                    # answer gets a longer pause and does not count as "no mail" -
                    # the mail may well be sitting there, we were just told to wait.
                    try:
                        m.logout()
                    except Exception:
                        pass
                    m = None
                    if _is_throttle(e):
                        log.warning("[%s] mailbox throttled (%s); pausing %.0fs", site_name, str(e)[:80], _THROTTLE_PAUSE)
                        deadline = max(deadline, time.time() + _THROTTLE_PAUSE + _POLL_SECONDS)
                        sleep(_THROTTLE_PAUSE)
                        continue
                    log.warning("[%s] mailbox error (%s); reconnecting", site_name, str(e)[:80])
                if time.time() >= deadline:
                    log.info("[%s] no confirmation mail for %s within %ss", site_name, to_address or site_name, wait_seconds)
                    return False
                sleep(_POLL_SECONDS)
    finally:
        if m is not None:
            try:
                m.logout()
            except Exception:
                pass
