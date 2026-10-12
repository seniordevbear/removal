"""inteliuscom scan — written 2026-10-12 from the live search page.

Replaces the generated placeholder, so the free exposure scan can check
this site at all. Result page captured on the VPS: https://www.intelius.com/people-search/First-Last/state/

A hit here is actionable: sites/inteliuscom.py can remove the listing.
"""
from sites_scan._template import *


def inteliuscom(dataRow, website_name, in_user_email, run_mode):
    name = (dataRow.get("Name") or "").strip()
    if not name:
        return "Not Found"
    parts = name.split()
    First, Last = parts[0], parts[-1]
    first, last = First.lower(), Last.lower()
    state_slug_ = state_slug(dataRow.get("State"))
    state_name = (dataRow.get("State") or "").strip()
    shot = scan_shot_path("inteliuscom", dataRow)
    urls = [
        f"https://www.intelius.com/people-search/{first}-{last}/{state_slug_}/" if state_slug_ else None,
        f"https://www.intelius.com/people-search/{first}-{last}/",
    ]
    return name_search_scan(shot, urls, ["css:div.person"], require_text=Last)
