from lib.broker_helpers import log_step, screenshot_step
import os
import datetime
import requests


# Rewritten 2026-08-23. faraday.ai/privacy-options embeds a Google Form
# ("Faraday Data Deletion/Opt-out/Do-Not-Sell request form"); the old
# browser flow targeted a page layout that no longer exists and failed for
# every customer. Google Forms accepts a plain POST to formResponse with
# the entry ids below (extracted from FB_PUBLIC_LOAD_DATA_ on the live
# form) — no browser, no captcha, and immune to page redesigns unless the
# form itself is rebuilt (in which case the entry ids stop matching and
# this fails loudly with the response text).
_FORM_ID = "1FAIpQLSd4h_G6XcXXpHq8FGeYgHH9CkQ3s4_qdIE-ZBKlNtdzKSXPfA"
_URL = "https://docs.google.com/forms/d/e/%s/formResponse" % _FORM_ID

_ENTRIES = {
    "first":  "entry.1544865296",   # First name (required)
    "last":   "entry.457414109",    # Last name (required)
    "dob":    "entry.580305585",    # Date of birth (optional)
    "address":"entry.1296567634",   # Address (optional)
    "city":   "entry.29073984",     # City (optional)
    "state":  "entry.172887688",    # State (optional)
    "type":   "entry.1821666757",   # request type (required, choices)
    "who":    "entry.713444953",    # Consumer / Authorized Agent (required)
}


def faradayio(dataRow, website_name, in_user_email, run_mode):
    broker = "faradayio"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    if not first or not last:
        raise RuntimeError("faradayio: form requires first AND last name")

    dob = ""
    if dataRow.get("Birth Year") and dataRow.get("Birth Month") and dataRow.get("Birth Day"):
        dob = "%s/%s/%s" % (dataRow["Birth Month"], dataRow["Birth Day"], dataRow["Birth Year"])

    payload = {
        _ENTRIES["first"]: first,
        _ENTRIES["last"]: last,
        _ENTRIES["type"]: "Data Deletion",
        _ENTRIES["who"]: "Consumer",
    }
    for key, field in (("dob", dob),
                       ("address", dataRow.get("Address") or ""),
                       ("city", dataRow.get("City") or ""),
                       ("state", dataRow.get("State") or "")):
        if field:
            payload[_ENTRIES[key]] = field

    log_step(broker, "POST google form (data deletion) for %s %s" % (first, last))
    resp = requests.post(_URL, data=payload, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://docs.google.com/forms/d/e/%s/viewform" % _FORM_ID,
    })
    body = resp.text or ""
    ok = resp.status_code == 200 and (
        "formResponse" in resp.url or "freebirdFormviewerViewResponse" in body
        or "Your response has been recorded" in body or "submit another response" in body.lower()
    )
    if not ok:
        raise RuntimeError(
            "faradayio: google form rejected the submission "
            "(HTTP %s) — form schema may have changed" % resp.status_code)

    # No browser, so no screenshot — persist the acceptance page instead so
    # the evidence chain has a real artifact.
    out_dir = os.path.join(os.getcwd(), "ScreenShot",
                           datetime.datetime.now().strftime("%Y-%m-%d"))
    try:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "FaradayIo_%s-%s.html" % (first, last))
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        log_step(broker, "submitted, receipt saved")
        return path
    except OSError:
        log_step(broker, "submitted (receipt not saved)")
        return None
