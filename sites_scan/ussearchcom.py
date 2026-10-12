"""ussearchcom scan — written 2026-10-12 from the live search page.

Was an auto-generated stub, so the free exposure scan could not check this
site at all. Result page captured on the VPS: https://www.ussearch.com/people-search/first-last/state/

A hit here is actionable: sites/ussearchcom.py can remove the listing.
"""
from sites_scan._template import *


def ussearchcom(dataRow, website_name, in_user_email, run_mode):
    name = (dataRow.get("Name") or "").strip()
    if not name:
        return "Not Found"
    parts = name.split()
    First, Last = parts[0], parts[-1]
    first, last = First.lower(), Last.lower()
    state_slug_ = state_slug(dataRow.get("State"))
    state_name = (dataRow.get("State") or "").strip()
    shot = scan_shot_path("ussearchcom", dataRow)
    urls = [
        f"https://www.ussearch.com/people-search/{first}-{last}/{state_slug_}/" if state_slug_ else None,
        f"https://www.ussearch.com/people-search/{first}-{last}/",
    ]
    return name_search_scan(shot, urls, ["css:div.person", "css:a.serp-card__details"], require_text=Last)
