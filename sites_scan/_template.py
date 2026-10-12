usaStateDictionary = { 
    'Alabama': 'AL', 
    'Alaska': 'AK', 
    'Arizona': 'AZ', 
    'Arkansas': 'AR', 
    'California': 'CA', 
    'Colorado': 'CO', 
    'Connecticut': 'CT', 
    'Delaware': 'DE', 
    'District of Columbia': 'DC', 
    'Florida': 'FL', 
    'Georgia': 'GA', 
    'Hawaii': 'HI', 
    'Idaho': 'ID', 
    'Illinois': 'IL', 
    'Indiana': 'IN', 
    'Iowa': 'IA', 
    'Kansas': 'KS', 
    'Kentucky': 'KY', 
    'Louisiana': 'LA', 
    'Maine': 'ME', 
    'Maryland': 'MD', 
    'Massachusetts': 'MA', 
    'Michigan': 'MI', 
    'Minnesota': 'MN', 
    'Mississippi': 'MS', 
    'Missouri': 'MO', 
    'Montana': 'MT', 
    'Nebraska': 'NE', 
    'Nevada': 'NV', 
    'New Hampshire': 'NH', 
    'New Jersey': 'NJ', 
    'New Mexico': 'NM', 
    'New York': 'NY', 
    'North Carolina': 'NC', 
    'North Dakota': 'ND', 
    'Ohio': 'OH', 
    'Oklahoma': 'OK', 
    'Oregon': 'OR', 
    'Pennsylvania': 'PA', 
    'Rhode Island': 'RI', 
    'South Carolina': 'SC', 
    'South Dakota': 'SD', 
    'Tennessee': 'TN', 
    'Texas': 'TX', 
    'Utah': 'UT', 
    'Vermont': 'VT', 
    'Virginia': 'VA', 
    'Washington': 'WA', 
    'West Virginia': 'WV', 
    'Wisconsin': 'WI', 
    'Wyoming': 'WY' 
    }

# --- state helpers (2026-09-19) -------------------------------------------
# Profiles hold either a code ("TX", "tx") or a full name ("Texas"): the
# profile form is free text. The scan modules did
#     usaStateDictionary[state.capitalize()]  else "ny"
# so a two-letter code silently searched NEW YORK — addresses.com returned
# "David Reyes in New York" for a customer in Katy, TX, and that wrong page
# was shown to the lead as their exposure. Never fall back to a guessed
# state: return "" and let the caller search without it.
_STATE_BY_CODE = {v: k for k, v in usaStateDictionary.items()}


def state_code(raw):
    """'Texas' / 'TX' / ' tx ' -> 'tx'; unknown or empty -> ''."""
    s = (raw or "").strip()
    if not s:
        return ""
    if len(s) == 2 and s.upper() in _STATE_BY_CODE:
        return s.lower()
    return usaStateDictionary.get(s.title(), "").lower()


def state_slug(raw):
    """'TX' / 'Texas' -> 'texas'; 'New York' / 'NY' -> 'new-york'; unknown -> ''."""
    code = state_code(raw)
    if not code:
        return ""
    return _STATE_BY_CODE[code.upper()].lower().replace(" ", "-")


# --- shared scan runner (2026-09-19) ---------------------------------------
# The five live scan modules each created their own ChromiumPage and called
# page.quit() only on the happy paths, so any exception leaked a Chrome
# process; allpeople could also fall off the end and return None, which the
# dispatcher treats as FOUND (anything but "Not Found") — a hit with no
# screenshot. This runner guarantees quit() and maps None/"" to "Not Found".
from time import sleep as _sleep


def wait_cloudflare(page, tries=20):
    """Click through Cloudflare's 'Just a moment' interstitial if it appears."""
    for _ in range(tries):
        try:
            title = (page.title or "").lower()
        except Exception:
            return
        if "just a moment" not in title:
            return
        try:
            page.actions.click()
            page.actions.key_down("TAB"); _sleep(0.2); page.actions.key_up("TAB"); _sleep(0.2)
            page.actions.key_down("SPACE"); _sleep(0.2); page.actions.key_up("SPACE")
        except Exception:
            pass
        _sleep(1.0)
        print("Cloudflare solving...")


def highlight_and_shoot(page, element, path):
    """Red-box the matching listing and save the screenshot; returns path."""
    page.run_js('arguments[0].setAttribute("style", "border: 5px solid red;")', element)
    _sleep(4)
    page.get_screenshot(path)
    print("Success Confirmation API is sent successfully!")
    return path


def run_scan(body):
    """Open a browser, run body(page) -> screenshot path | 'Not Found', always quit."""
    from DrissionPage import ChromiumPage
    page = ChromiumPage()
    try:
        result = body(page)
        if not result:
            print("No results found.")
            return "Not Found"
        return result
    finally:
        try:
            page.quit()
        except Exception:
            pass


# --- shared people-search scan (2026-10-12) --------------------------------
# Ten new scan modules all do the same three things: build a search URL from
# the customer's name (and state where the site has state pages), find the
# first result card, red-box it and screenshot. Written once here so a
# selector change is a one-line fix in the module rather than a new flow.
#
# Why it matters: only 7 of 416 sites_scan modules were real, so the free
# exposure scan could check five sites and told two of October's eight leads
# they appear on none. Each site added here is one we can also remove from,
# so anything found is actionable.

def name_search_scan(shot_path, url_templates, selectors, wait=5, require_text=None):
    """Try each URL in turn; return a screenshot of the first result card.

    url_templates: already-formatted URLs, most specific first (state page
                   before the national one).
    selectors:     DrissionPage selectors for one result card, best first.
    require_text:  if given, the card's text must contain it (case-insensitive)
                   before it counts — guards against matching a template or an
                   advert block on a page with no real results.
    """
    def body(page):
        for url in url_templates:
            if not url:
                continue
            try:
                page.get(url)
            except Exception:
                continue
            _sleep(wait)
            wait_cloudflare(page)
            title = (page.title or "").lower()
            if "just a moment" in title or "attention required" in title:
                continue          # still blocked: try the next URL
            for sel in selectors:
                try:
                    els = page.eles(sel, timeout=3)
                except Exception:
                    continue
                for el in (els or [])[:3]:
                    if require_text:
                        try:
                            if require_text.lower() not in (el.text or "").lower():
                                continue
                        except Exception:
                            continue
                    return highlight_and_shoot(page, el, shot_path)
        return None
    return run_scan(body)


def scan_shot_path(broker, dataRow):
    """ScreenShotScan/<date>/<Broker>_<First>-<Last>_<unique>.png — unique so
    two workers on the same broker in the same second cannot overwrite each
    other's evidence (the 2026-10-02 cross-filing bug)."""
    import datetime as _dt, os as _os, re as _re, threading as _th, uuid as _uuid
    name = (dataRow.get("Name") or "").strip()
    first = name.split()[0] if name else "unknown"
    last = name.split()[-1] if len(name.split()) > 1 else ""
    out = _os.path.join(_os.getcwd(), "ScreenShotScan", _dt.datetime.now().strftime("%Y-%m-%d"))
    _os.makedirs(out, exist_ok=True)
    who = _re.sub(r"[^A-Za-z0-9]+", "", _th.current_thread().name)[-10:] or "main"
    stamp = _dt.datetime.now().strftime("%H%M%S_%f")
    safe = _re.sub(r"[^A-Za-z0-9-]+", "", first + "-" + last)
    return _os.path.join(out, "%s_%s_%s_%s_%s.png" % (broker, safe, stamp, who, _uuid.uuid4().hex[:6]))
