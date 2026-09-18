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

def fastpeoplesearchcom(dataRow, website_name, in_user_email, run_mode):
    # state_code() accepts "TX" or "Texas"; "" when unknown (no "ny" fallback,
    # 2026-09-19). URL degrades: name_city-state -> name_state -> name.
    state = state_code(dataRow.get("State"))
    fName = dataRow["Name"].split()[0].lower()
    lName = dataRow["Name"].split()[-1].lower()
    city = (dataRow.get("City") or "").strip().lower().replace(" ", "-")
    shot = screentShotDir + "\\FastPeopleSearchCom_" + fName + "-" + lName + ".png"
    url = f"https://www.fastpeoplesearch.com/name/{fName}-{lName}"
    if city and state:
        url += f"_{city}-{state}"
    elif state:
        url += f"_{state}"

    def body(page):
        page.get(url)
        sleep(5)
        wait_cloudflare(page)
        sleep(5)
        results = page.eles("tag:div@@class=people-list")
        if not results:
            return None
        return highlight_and_shoot(page, results[0], shot)
    return run_scan(body)
