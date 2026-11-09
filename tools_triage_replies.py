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

# Ordered: the first pattern that matches wins, so a refusal is not filed as a
# polite acknowledgement just because it opens with "thank you for contacting".
CATEGORIES = [
    ("no_data_found", re.compile(
        r"(did not|could ?n[o']?t|were unable to|unable to) (find|locate|identify)[^.]{0,40}"
        r"(any )?(data|record|information|match)|no (data|records?|information|results?) "
        r"(was |were )?(found|located|associated|linked)|not (found|located) in our", re.I)),
    ("needs_verification", re.compile(
        r"(provide|submit|upload|attach|send)[^.]{0,60}"
        r"(government[- ]issued|photo )?(id|identification|driver'?s licen[cs]e|passport|"
        r"proof of (identity|residence)|notari[sz]ed)|verify your identity|"
        r"identity verification|additional (information|documentation) (is )?(required|needed)", re.I)),
    ("action_required", re.compile(
        r"click (the|this) link|confirm your (request|e-?mail)|complete (the|your) (form|request)|"
        r"within \d+ (business )?days? (or|to avoid)|we need you to|please (reply|respond|complete)", re.I)),
    ("refused", re.compile(
        r"(we )?(are )?(unable|cannot|can not|can'?t|decline|denied|deny|refuse)[^.]{0,50}"
        r"(process|fulfil|fulfill|complete|honor|honour|comply)|"
        r"request (has been |was )?(denied|rejected|closed without)|not subject to|"
        r"does not apply to|outside the scope", re.I)),
    ("completed", re.compile(
        r"(has been|have been|was|were|is now)[^.]{0,30}"
        r"(removed|deleted|suppressed|opted out|processed|completed|fulfilled)|"
        r"we have (removed|deleted|processed|completed)|your (request|record)[^.]{0,30}"
        r"(is )?(complete|closed|fulfilled)|successfully (removed|deleted|processed)", re.I)),
    ("received_only", re.compile(
        r"(request|ticket|case|message) (\(?#?\d+\)? )?(has been |was )?received|"
        r"we have received|thank you for (contacting|reaching out|your request)|"
        r"is being reviewed|we will (review|respond|get back)", re.I)),
]
BOUNCE = re.compile(r"undeliverable|delivery (status|has failed)|mail delivery|returned to sender", re.I)
AUTOREPLY = re.compile(r"out of (the )?office|auto(matic)?[- ]?reply|vacation", re.I)


def classify(subject, body):
    text = (subject or "") + "\n" + (body or "")
    if BOUNCE.search(text):
        return "bounce"
    if AUTOREPLY.search(subject or ""):
        return "autoreply"
    for name, pat in CATEGORIES:
        if pat.search(text):
            return name
    return "unclassified"


# What each bucket means for the customer's row, in plain words.
MEANING = {
    "no_data_found":      "broker says it holds nothing - row should be 'not listed', not 'removed'",
    "needs_verification": "broker wants ID before acting - the removal has NOT happened",
    "action_required":    "broker is waiting on us - a link, a form, a deadline",
    "refused":            "broker declined - the removal has NOT happened",
    "completed":          "broker confirms the removal - the row is honest",
    "received_only":      "acknowledgement only, no outcome yet",
    "bounce":             "address is dead (mailbox_sweep already handles these)",
    "autoreply":          "ignore",
    "unclassified":       "needs a human eye",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--csv", default="")
    ap.add_argument("--show", type=int, default=3, help="example subjects per bucket")
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

    since = time.strftime("%d-%b-%Y", time.gmtime(time.time() - args.days * 86400))
    counts, examples, per_broker, rows = Counter(), {}, Counter(), []
    scanned = 0
    for folder in FOLDERS:
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

    print("\nscanned %d messages from the last %d days (nothing was marked read)\n" % (scanned, args.days))
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
