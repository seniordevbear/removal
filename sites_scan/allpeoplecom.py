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

def allpeoplecom(dataRow, website_name, in_user_email, run_mode):
    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    shot = screentShotDir + "\\AllPeopleCom_" + fName + "-" + lName + ".png"
    city = (dataRow.get("City") or "").strip()
    state = state_code(dataRow.get("State")).upper()
    where = ", ".join(x for x in (city, state) if x)

    def body(page):
        page.get(f"https://allpeople.com/search?ss={fName}+{lName}+&ss-e=&ss-p=&ss-i=&where={where}&industry-auto=&where-auto=")
        sleep(5)
        wait_cloudflare(page)
        sleep(5)
        if page.ele("tag:h3@@style=font-size: 12px; color: #577594;"):
            return None  # the "no results" heading
        results = page.eles("tag:div@@class=rev-flex rev-flex-s")
        if not results:
            return None  # used to fall off the end here and return None == FOUND
        return highlight_and_shoot(page, results[0], shot)
    return run_scan(body)
