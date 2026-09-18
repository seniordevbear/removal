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
