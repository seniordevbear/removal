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
