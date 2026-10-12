"""anywhocom scan — written 2026-10-12 from the live search page.

Replaces the generated placeholder, so the free exposure scan can check
this site at all. Result page captured on the VPS: https://www.anywho.com/people/First+Last/state  (the national page is a state index, not a result list)

A hit here is actionable: sites/anywhocom.py can remove the listing.
"""
from sites_scan._template import *


def anywhocom(dataRow, website_name, in_user_email, run_mode):
    name = (dataRow.get("Name") or "").strip()
    if not name:
        return "Not Found"
    parts = name.split()
    First, Last = parts[0], parts[-1]
    first, last = First.lower(), Last.lower()
    state_slug_ = state_slug(dataRow.get("State"))
    state_name = (dataRow.get("State") or "").strip()
    shot = scan_shot_path("anywhocom", dataRow)
    urls = [
        f"https://www.anywho.com/people/{First}+{Last}/{state_slug_}" if state_slug_ else None,
        f"https://www.anywho.com/people/{First}+{Last}",
    ]
    return name_search_scan(shot, urls, ["css:li.items-center"], require_text=Last)
