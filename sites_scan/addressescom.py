from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import os, datetime
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from sites_scan._template import *

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShotScan", current_date)
os.makedirs(screentShotDir, exist_ok=True)

def addressescom(dataRow, website_name, in_user_email, run_mode):
    # state_code() accepts "TX" or "Texas"; "" when unknown. The old code
    # fell back to "ny" for any two-letter code (2026-09-19 fix).
    state = state_code(dataRow.get("State"))
    fName = (dataRow["Name"].split()[0]).lower()
    lName = (dataRow["Name"].split()[-1]).lower()
    shot = screentShotDir + "\\AddressesCom_" + fName + "-" + lName + ".png"
    url = f"https://www.addresses.com/people/{fName}+{lName}/" + (f"{state}/" if state else "")

    def body(page):
        page.get(url)
        sleep(2)
        wait_cloudflare(page)
        sleep(1)
        cb = page.ele("tag:div@@id=checkbox", timeout=5)
        if cb:
            cb.click()
            sleep(5)
        if not page.ele("tag:div@@class=people-container", timeout=10):
            return None
        results = page.eles("tag:div@@class=person")
        if not results:
            return None
        return highlight_and_shoot(page, results[0], shot)
    return run_scan(body)
