# lib/email_sender.py — SMTP relay helper.
#
# Credentials now come from env (.env). Previously hardcoded as
#   SMTP_USERNAME = "confirmation"
#   SMTP_PASSWORD = "privacypros123"
# which baked the password into git forever. The .env on this VPS already has
# CONFIRMATION_EMAIL_PASSWORD set (used by main.py), so we reuse it here
# rather than introducing a second key for the same identity.
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("pd.email_sender")

SMTP_SERVER = os.getenv("CONFIRMATION_IMAP_SERVER", "mail1.privacypros.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("CONFIRMATION_EMAIL_USER", "confirmation")
SMTP_PASSWORD = os.getenv("CONFIRMATION_EMAIL_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "confirmation@privacypros.com")
SMTP_TIMEOUT = float(os.getenv("SMTP_TIMEOUT", "20"))


def send_email(to_email, subject, body):
    """Send a plain-text email via SMTP+STARTTLS. Returns True on success."""
    if not SMTP_PASSWORD:
        log.error("send_email skipped: CONFIRMATION_EMAIL_PASSWORD not set")
        return False
    if not to_email:
        log.warning("send_email skipped: empty to_email")
        return False

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
        log.info("send_email ok to=%s subject=%r", to_email, subject[:60])
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
