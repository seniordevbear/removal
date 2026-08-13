# main.py — inbox confirmation bot.
#
# Polls the confirmation@privacypros.com mailbox via SurgeWeb and clicks the
# "Confirm Email" / "Verify My Identity" links that brokers send back to us
# so they actually action the opt-outs we filed.
#
# Lifecycle / safety changes:
#   - The previous version had `except Exception: 1` in the poll loop,
#     silently swallowing every error. That made it impossible to tell why
#     the bot would stop processing — chromium crash? login expired? element
#     not found? Now we log with traceback.
#   - The Chromium page was started at module import (before main()) which
#     made the script unimportable for testing. Moved into main().
#   - On a login failure or fatal chromium crash, we now re-create the
#     ChromiumPage instead of looping over a dead handle.
#   - Sleep cadence and timeouts come from env so the operator can tune
#     without editing code.
from time import sleep
import os, random, datetime, sys, logging, traceback

# Load .env from this directory so credentials are not hardcoded.
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip("'").strip('"'))

from DrissionPage import ChromiumPage, ChromiumOptions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("pd.confirmation_bot")

# Email Login Constants - sourced from env (.env). No hardcoded credentials.
IMAP_SERVER = os.getenv("CONFIRMATION_IMAP_SERVER", "mail1.privacypros.com")
USERNAME = os.getenv("CONFIRMATION_EMAIL_USER", "confirmation")
PASSWORD = os.getenv("CONFIRMATION_EMAIL_PASSWORD")
WEBMAIL_URL = os.getenv("CONFIRMATION_WEBMAIL_URL", "https://mail1.privacypros.com/surgeweb")
POLL_INTERVAL_SECONDS = float(os.getenv("CONFIRMATION_POLL_INTERVAL", "10"))
SCREENSHOT_DIR = os.getenv("CONFIRMATION_SCREENSHOT_DIR", "screen_shot")
USER_DATA_DIR = os.getenv("CONFIRMATION_USER_DATA_DIR", "user_data")

if not PASSWORD:
    sys.exit("FATAL: CONFIRMATION_EMAIL_PASSWORD env var is required (check .env).")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BUTTON_TEXTS = [
    "Confirm Email",
    "Click here to verify email",
    "Confirm my email",
    "Confirm my request",
    "Confirm my email address",
    "click here",
    "/control/confirm_request",
    "Click here to remove",
    "View Request",
    "Verify My Identity",
    "Continue",
    "Verify your email address",
]


def _make_browser():
    options = ChromiumOptions()
    options.set_user_data_path(USER_DATA_DIR)
    return ChromiumPage(addr_or_opts=options)


def _human_typing(element, text):
    element.clear()
    for c in text:
        element.input(c)
        sleep(random.uniform(0.05, 0.1))
    sleep(random.uniform(0.5, 1))


def _login(tab):
    log.info("logging in to SurgeWeb as %s", USERNAME)
    username_input = tab.ele("tag:input@@name=username_ex")
    _human_typing(username_input, USERNAME)
    password_input = tab.ele("tag:input@@name=password")
    _human_typing(password_input, PASSWORD)
    login_btn = tab.ele("tag:input@@id=cmd_login")
    login_btn.click()
    log.info("login submitted; waiting for inbox")
    tab.wait.ele_displayed("tag:li@@fld_id=INBOX")
    log.info("inbox loaded")


def _check_new_emails(page):
    inbox_btn = page.ele("tag:li@@fld_id=INBOX")
    inbox_btn.click()
    sleep(2)
    unread_emails = page.eles("tag:tr@@class:msg_unread")
    if not unread_emails:
        log.debug("no unread emails")
        return
    log.info("processing %d unread emails", len(unread_emails))
    for email_row in unread_emails:
        try:
            _handle_email(page, email_row)
        except Exception:
            log.exception("error handling individual email")


def _handle_email(page, email_row):
    log.info("opening email at %s", datetime.datetime.now().strftime("%H:%M:%S"))
    email_row.click()
    sleep(5)

    verify_button = None
    for text in BUTTON_TEXTS:
        verify_button = page.ele(f"tag:a@@text():{text}", timeout=5)
        if verify_button:
            break

    if not verify_button:
        log.info("no matching button found in this email")
        sleep(2)
        return

    new_url = verify_button.attr("href")
    if not new_url:
        log.warning("verify button found but href is empty")
        return

    new_tab = page.new_tab(new_url)
    log.info("clicked verify: %r", verify_button.text)
    sleep(7)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{timestamp}.png")
    try:
        new_tab.get_screenshot(screenshot_path)
        log.info("saved %s", screenshot_path)
    finally:
        try:
            new_tab.close()
        except Exception:
            log.exception("new_tab.close failed")


def main():
    log.info("confirmation bot starting; poll=%.1fs", POLL_INTERVAL_SECONDS)
    page = None
    while True:
        try:
            if page is None:
                page = _make_browser()
                page.get(WEBMAIL_URL)
                _login(page)
            _check_new_emails(page)
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt; shutting down")
            break
        except Exception:
            log.exception("poll iteration failed; recycling browser")
            try:
                if page is not None:
                    page.quit()
            except Exception:
                pass
            page = None
            sleep(min(60, POLL_INTERVAL_SECONDS * 3))
            continue
        sleep(POLL_INTERVAL_SECONDS)

    if page is not None:
        try:
            page.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
