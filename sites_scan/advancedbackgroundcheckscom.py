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

def advancedbackgroundcheckscom(dataRow, website_name, in_user_email, run_mode) : 
    fName = dataRow["Name"].split()[0].lower() # split string based on space to get first name
    lName = dataRow["Name"].split()[-1].lower()# split string based on space to get last name
    states = dataRow["State"].lower().split(" ")
    if len(states) > 1 :
        state = "-".join(states)
    else :
        state = "".join(states)
    screenshot_save_path = screentShotDir + "\\AdvancedBackgroundChecksCom_" + fName + "-" + lName + ".png"
    page = ChromiumPage()
    url = f"https://www.advancedbackgroundchecks.com/names/{fName}-{lName}_{state}_age_{dataRow['Age']}"
    page.get(url)
    sleep(6)
    cnt = 0

    while True:
        cnt = cnt + 1
        if cnt > 20 : 
            break
        page_title = page.title
        if "just a moment" in page_title.lower() :
            page.actions.click()
            page.actions.key_down("TAB")
            sleep(0.2)
            page.actions.key_up("TAB")
            sleep(0.2)

            page.actions.key_down("SPACE")
            sleep(0.2)
            page.actions.key_up("SPACE")

            sleep(1.0)
            print("Cloudflare solving...")
        else :
            break
    sleep(1)
    search_result = page.ele("tag:div@@id=cads-container")
    if search_result:
        result = page.eles("tag:div@@class=card-block")
        if result:
            element = result[0]
            page.run_js('arguments[0].setAttribute("style", "border: 5px solid red;")', element)
            sleep(4)
            page.get_screenshot(screenshot_save_path)
            page.quit()
            print("Success Confirmation API is sent successfully!")
            return screenshot_save_path
        else:
            print("No results found.")
            page.quit()
            return "Not Found"
    else:
        print("No results found.")
        page.quit()
        return "Not Found"