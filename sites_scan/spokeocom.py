from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
import re
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShotScan", current_date)
os.makedirs(screentShotDir, exist_ok=True)
from sites_scan._template import *

def spokeocom(dataRow, website_name, in_user_email, run_mode):
    """Spokeo scan. State-aware since 2026-09-19: the name-only search page
    lists every namesake in the country (828 "Jonathan Whitfield"s), so the
    red-boxed first result was often someone else. Try the state page first
    and fall back to the national search if it yields nothing."""
    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    shot = screentShotDir + "\\SpokeoCom_" + fName + "-" + lName + ".png"
    state_name = state_slug(dataRow.get("State"))  # "texas" / "new-york" / ""

    def body(page):
        urls = []
        if state_name:
            urls.append(f"https://www.spokeo.com/{fName}-{lName}/{state_name.title()}")
        urls.append(f"https://www.spokeo.com/search/{fName}-{lName}")
        for url in urls:
            page.get(url)
            sleep(5)
            wait_cloudflare(page)
            results = page.eles("tag:div@@role=listitem")
            if results:
                return highlight_and_shoot(page, results[0], shot)
        return None
    return run_scan(body)
