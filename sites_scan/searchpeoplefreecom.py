"""searchpeoplefreecom scan — written 2026-10-12 from the live search page.

Was an auto-generated stub, so the free exposure scan could not check this
site at all. Result page captured on the VPS: https://www.searchpeoplefree.com/find/first-last

A hit here is actionable: sites/searchpeoplefreecom.py can remove the listing.
"""
from sites_scan._template import *


def searchpeoplefreecom(dataRow, website_name, in_user_email, run_mode):
    name = (dataRow.get("Name") or "").strip()
    if not name:
        return "Not Found"
    parts = name.split()
    First, Last = parts[0], parts[-1]
    first, last = First.lower(), Last.lower()
    state_slug_ = state_slug(dataRow.get("State"))
    state_name = (dataRow.get("State") or "").strip()
    shot = scan_shot_path("searchpeoplefreecom", dataRow)
    urls = [
        f"https://www.searchpeoplefree.com/find/{first}-{last}/{state_slug_}" if state_slug_ else None,
        f"https://www.searchpeoplefree.com/find/{first}-{last}",
    ]
    return name_search_scan(shot, urls, ["css:div.card", "css:div.row div.col"], require_text=Last)
