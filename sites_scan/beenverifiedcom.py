"""beenverifiedcom scan — written 2026-10-12 from the live search page.

Replaces the generated placeholder, so the free exposure scan can check
this site at all. Result page captured on the VPS: https://www.beenverified.com/people/first-last/

A hit here is actionable: sites/beenverifiedcom.py can remove the listing.
"""
from sites_scan._template import *


def beenverifiedcom(dataRow, website_name, in_user_email, run_mode):
    name = (dataRow.get("Name") or "").strip()
    if not name:
        return "Not Found"
    parts = name.split()
    First, Last = parts[0], parts[-1]
    first, last = First.lower(), Last.lower()
    shot = scan_shot_path("beenverifiedcom", dataRow)
    urls = [
        f"https://www.beenverified.com/people/{first}-{last}/",
    ]
    return name_search_scan(shot, urls, ["css:li.search-result", "css:div.result-detail"], require_text=Last)
