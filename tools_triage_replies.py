"""Read the broker replies nobody has been reading.

mailbox_sweep.py handles two kinds of incoming mail - bounces, and
confirmation links a live run is waiting for. Its docstring is honest about
the rest: "Everything else is left unread for a person to look at." Nobody
has, and 6,768 rows across 196 customers are marked removed on the strength
of a sent e-mail alone. Some of those brokers replied "we found no data",
some asked for ID, some refused outright.

This reads the mailbox and sorts what is in it. It changes nothing: no mail
is marked read, no row is touched, nothing is sent. Run it, read the summary,
then decide.

    Scripts\\python.exe tools_triage_replies.py              # last 90 days
    Scripts\\python.exe tools_triage_replies.py --days 30
    Scripts\\python.exe tools_triage_replies.py --csv replies.csv

Needs the same CONFIRMATION_* settings in .env that the pipeline already uses,
so run it on the VPS.
"""
import argparse
import csv
import email
import email.policy
import imaplib
import os
import re
import sys
import time
from collections import Counter
from email.utils import parseaddr

# .env has to be loaded before lib.email_verification is imported: it reads
# CONFIRMATION_* at import time, and only manage.py was loading the file, so a
# standalone tool saw nothing and reported the password as unset even on the
# VPS where it is right there in .env.
def _load_env_file(env_path):
    """Same parser manage.py uses: KEY=value, # comments, real env wins."""
    if not os.path.exists(env_path):
        return False
    with open(env_path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value
    return True


_HERE = os.path.dirname(os.path.abspath(__file__))
_ENV_FOUND = _load_env_file(os.path.join(_HERE, ".env"))

from lib.email_verification import imap_connect, FOLDERS
from lib.mailbox_sweep import _text, _broker_from_sender

from lib.broker_replies import classify, is_broker_reply, MEANING, CATEGORIES

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--csv", default="")
    ap.add_argument("--show", type=int, default=3, help="example subjects per bucket")
    ap.add_argument("--all-mail", action="store_true",
                    help="also scan [Gmail]/All Mail - it contains Sent, so our own "
                         "requests get counted as replies; off by default")
    args = ap.parse_args()

    try:
        m = imap_connect()
    except Exception as e:
        env = os.path.join(_HERE, ".env")
        missing = [k for k in ("CONFIRMATION_EMAIL_USER", "CONFIRMATION_EMAIL_PASSWORD",
                               "CONFIRMATION_IMAP_SERVER") if not os.getenv(k)]
        sys.exit(
            "could not open the mailbox: %s\n"
            "  .env looked for at: %s  (%s)\n"
            "  still unset after loading it: %s\n"
            "  run this from the pipeline folder on the VPS, the one holding manage.py"
            % (e, env, "found" if _ENV_FOUND else "NOT FOUND",
               ", ".join(missing) or "none - so the server or password is being refused"))

    # All Mail holds a copy of everything we sent, so it is excluded unless the
    # caller asks for it. INBOX and Spam are where replies actually land.
    folders = [f for f in FOLDERS if args.all_mail or "all mail" not in f.lower()]
    since = time.strftime("%d-%b-%Y", time.gmtime(time.time() - args.days * 86400))
    counts, examples, per_broker, rows = Counter(), {}, Counter(), []
    scanned = skipped_not_broker = 0
    for folder in folders:
        try:
            typ, _ = m.select('"%s"' % folder, readonly=True)   # readonly: nothing is marked read
        except Exception:
            continue
        if typ != "OK":
            continue
        typ, data = m.search(None, "SINCE", since)
        if typ != "OK":
            continue
        for num in data[0].split():
            # BODY.PEEK never sets \Seen.
            typ, d = m.fetch(num, "(BODY.PEEK[])")
            if typ != "OK" or not d or not isinstance(d[0], tuple):
                continue
            try:
                msg = email.message_from_bytes(d[0][1], policy=email.policy.default)
            except Exception:
                continue
            scanned += 1
            subject = (msg.get("subject") or "")[:200]
            sender = parseaddr(msg.get("from") or "")[1]
            if not is_broker_reply(sender):
                skipped_not_broker += 1
                continue
            body = _text(msg)[:6000]
            cat = classify(subject, body)
            counts[cat] += 1
            broker = _broker_from_sender(sender)
            if cat in ("no_data_found", "needs_verification", "refused", "action_required"):
                per_broker[(cat, broker)] += 1
            examples.setdefault(cat, []).append((sender, subject))
            rows.append({"folder": folder, "date": (msg.get("date") or "")[:31],
                         "from": sender, "broker": broker,
                         "category": cat, "subject": subject})
    try:
        m.logout()
    except Exception:
        pass

    print("\nread %d messages from the last %d days in %s (nothing was marked read)"
          % (scanned, args.days, ", ".join(folders)))
    print("  %d were not broker replies (our own sent mail, Google and vendor notices) - not counted" % skipped_not_broker)
    print("  %d genuine broker replies\n" % (scanned - skipped_not_broker))
    width = max((len(k) for k in counts), default=10)
    for cat, n in counts.most_common():
        print("  %-*s %5d   %s" % (width, cat, n, MEANING.get(cat, "")))
        for sender, subject in examples.get(cat, [])[:args.show]:
            print("  %-*s         %s | %s" % (width, "", sender[:34], subject[:70]))
    bad = sum(counts[k] for k in ("no_data_found", "needs_verification", "refused"))
    if bad:
        print("\n  %d replies say the removal did NOT happen, on rows we report as removed." % bad)
        print("  worst brokers:")
        for (cat, broker), n in per_broker.most_common(10):
            print("    %-28s %-20s %d" % (broker or "(unknown)", cat, n))
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["folder", "date", "from", "broker", "category", "subject"])
            w.writeheader(); w.writerows(rows)
        print("\n  wrote %d rows to %s" % (len(rows), args.csv))


if __name__ == "__main__":
    main()
