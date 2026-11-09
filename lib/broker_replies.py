"""How a broker's reply is read, in one place.

Both the standalone triage tool and the mailbox sweep classify replies, and
they have to agree: a reply the tool calls "no data found" must be stamped on
the row the same way by the sweep, or a customer's report and the audit of it
disagree.

The sweep used to leave every reply that was not a bounce or a confirmation
link unread "for a person to look at". Over 90 days that was ~3,500 replies,
1,689 of them a broker saying it holds no data about the customer, against 104
confirming a removal. All of those rows said "removed".
"""
import re

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

# 2026-11-09: the first run scanned [Gmail]/All Mail, which contains Sent, so
# 5,062 of our OWN outgoing requests came back as "broker replies" - and since
# a request says "please delete the information you hold", most were filed as
# the broker confirming a removal. That alone turned 200 real confirmations
# into 2,729. Google's own notices ("2-Step Verification turned on") were read
# as a broker asking for ID. Neither is a reply from a broker, so neither is
# counted.
OURS = re.compile(r"@(privacyduck\.com|privacypros\.com|privacyprosremoval\.com)\s*$", re.I)
NOT_A_BROKER = re.compile(
    r"@([\w.-]*\.)?(google|googlemail|gmail|accounts\.google|workspace-noreply|youtube|"
    r"linkedin|microsoft|onmicrosoft|apple|icloud|stripe|intuit|paypal|docusign|zoom|slack|"
    r"dropbox|github|namecheap|godaddy|epik|digitalocean|cloudflare|atlassian|notion|canva|"
    r"calendly|meta|facebook|twitter|mailchimp|sendgrid|twilio|hubspot|salesforce|"
    r"supersetinbox)\.[a-z.]+\s*$", re.I)


def is_broker_reply(sender):
    """True only for mail that came from outside, from something broker-shaped."""
    if not sender or "@" not in sender:
        return False
    return not (OURS.search(sender) or NOT_A_BROKER.search(sender))


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


