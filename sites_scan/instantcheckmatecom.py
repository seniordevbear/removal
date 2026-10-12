"""instantcheckmatecom scan — written 2026-10-12 from the live search page.

Was an auto-generated stub, so the free exposure scan could not check this
site at all. Result page captured on the VPS: https://www.instantcheckmate.com/people/first-last/

A hit here is actionable: sites/instantcheckmatecom.py can remove the listing.
"""
from sites_scan._template import *


def instantcheckmatecom(dataRow, website_name, in_user_email, run_mode):
    name = (dataRow.get("Name") or "").strip()
    if not name:
        return "Not Found"
    parts = name.split()
    First, Last = parts[0], parts[-1]
    first, last = First.lower(), Last.lower()
    shot = scan_shot_path("instantcheckmatecom", dataRow)
    urls = [
        f"https://www.instantcheckmate.com/people/{first}-{last}/",
    ]
    return name_search_scan(shot, urls, ["css:article.rgv2-result", "css:li.rgv2-results__item"], require_text=Last)
