from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
import re
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from sites_scan._template import *

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShotScan", current_date)
os.makedirs(screentShotDir, exist_ok=True)

def advancedbackgroundcheckscom(dataRow, website_name, in_user_email, run_mode):
    fName = dataRow["Name"].split()[0].lower()
    lName = dataRow["Name"].split()[-1].lower()
    # The site wants the FULL state name as a slug ("texas", "new-york"); a
    # two-letter code produced "_tx_" and no results. Unknown state / empty
    # age are simply omitted (2026-09-19).
    state = state_slug(dataRow.get("State"))
    age = str(dataRow.get("Age") or "").strip()
    shot = screentShotDir + "\\AdvancedBackgroundChecksCom_" + fName + "-" + lName + ".png"
    url = f"https://www.advancedbackgroundchecks.com/names/{fName}-{lName}"
    if state:
        url += f"_{state}"
    if age.isdigit():
        url += f"_age_{age}"

    def body(page):
        page.get(url)
        sleep(6)
        wait_cloudflare(page)
        sleep(1)
        if not page.ele("tag:div@@id=cads-container"):
            return None
        results = page.eles("tag:div@@class=card-block")
        if not results:
            return None
        return highlight_and_shoot(page, results[0], shot)
    return run_scan(body)
