r"""
check_mailbox.py — verify the confirmation mailbox settings in .env.

    python check_mailbox.py            read-only checks
    python check_mailbox.py --send-test me@example.com

Tests IMAP login, lists the folders it can read and how much recent mail is
in each, then tests SMTP login (no message is sent unless --send-test is
given). Prints host, user and folder names only — never the password.

Run it after changing the mailbox settings, on whichever machine you changed
them. Nothing here writes to the mailbox or the database.
"""
import os
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _line in open(os.path.join(HERE, ".env"), encoding="utf-8", errors="replace"):
    if "=" in _line and not _line.lstrip().startswith("#"):
        _k, _v = _line.split("=", 1)
        os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))


def main():
    import imaplib
    import smtplib

    imap_host = os.getenv("CONFIRMATION_IMAP_SERVER", "mail1.privacypros.com")
    imap_port = int(os.getenv("CONFIRMATION_IMAP_PORT", "993"))
    user = os.getenv("CONFIRMATION_EMAIL_USER", "confirmation")
    pw = os.getenv("CONFIRMATION_EMAIL_PASSWORD", "")
    smtp_host = os.getenv("SMTP_SERVER") or imap_host
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME") or user
    from_email = os.getenv("FROM_EMAIL", "confirmation@privacypros.com")

    print("IMAP  %s:%d as %s" % (imap_host, imap_port, user))
    print("SMTP  %s:%d as %s (From: %s)" % (smtp_host, smtp_port, smtp_user, from_email))
    print("password set: %s (%d chars)" % ("yes" if pw else "NO", len(pw)))
    if not pw:
        print("\nFAIL: CONFIRMATION_EMAIL_PASSWORD is empty in .env")
        return 1

    socket.setdefaulttimeout(45)
    ok = True

    try:
        m = imaplib.IMAP4_SSL(imap_host, imap_port)
        m.login(user, pw)
        print("\nIMAP login OK")
        typ, boxes = m.list()
        names = []
        for b in (boxes or []):
            line = b.decode("utf-8", "replace")
            names.append(line.split(' "/" ')[-1].strip().strip('"') if ' "/" ' in line else line.split()[-1].strip('"'))
        print("folders: %s" % ", ".join(names[:12]))
        # read the folder list from .env directly: importing
        # lib.email_verification would pull in DrissionPage, which is only
        # installed on the VPS.
        FOLDERS = [f.strip() for f in os.getenv(
            "CONFIRMATION_IMAP_FOLDERS",
            "INBOX,Spam,Spam_Rejected,[Gmail]/Spam,[Gmail]/All Mail").split(",") if f.strip()]
        for f in FOLDERS:
            try:
                typ, data = m.select('"%s"' % f, readonly=True)
                if typ != "OK":
                    print("  %-22s not present (skipped)" % f)
                    continue
                total = int(data[0])
                typ, d = m.search(None, "UNSEEN")
                unseen = len(d[0].split()) if typ == "OK" else 0
                print("  %-22s %6d messages, %d unread" % (f, total, unseen))
            except Exception as e:
                print("  %-22s not readable: %s" % (f, type(e).__name__))
        m.logout()
    except Exception as e:
        ok = False
        print("\nIMAP FAILED: %s: %s" % (type(e).__name__, str(e)[:160]))
        if "AUTHENTICATIONFAILED" in str(e).upper():
            print("  -> for Google Workspace this must be a 16-character APP password,")
            print("     not the account password, and 2-step must be on for the account.")

    try:
        s = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
        s.starttls()
        s.login(smtp_user, pw)
        print("\nSMTP login OK")
        to = None
        for i, a in enumerate(sys.argv):
            if a == "--send-test" and i + 1 < len(sys.argv):
                to = sys.argv[i + 1]
        if to:
            from email.message import EmailMessage
            msg = EmailMessage()
            msg["From"] = from_email
            msg["To"] = to
            msg["Subject"] = "PrivacyDuck pipeline mailbox test"
            msg.set_content("Sent by check_mailbox.py to confirm the removal pipeline can send mail.")
            s.send_message(msg)
            print("test message sent to %s" % to)
        s.quit()
    except Exception as e:
        ok = False
        print("\nSMTP FAILED: %s: %s" % (type(e).__name__, str(e)[:160]))

    print("\n%s" % ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED (see above)"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
