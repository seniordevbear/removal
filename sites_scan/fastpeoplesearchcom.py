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

def fastpeoplesearchcom(dataRow, website_name, in_user_email, run_mode) : 
    state = dataRow["State"]
    print(state.capitalize())
    if state.capitalize() in usaStateDictionary :
        state = usaStateDictionary[state.capitalize()].lower()
    else :
        state = "ny"
    fName = dataRow["Name"].split()[0].lower() # split string based on space to get first name
    lName = dataRow["Name"].split()[-1].lower()# split string based on space to get last name
    city = dataRow["City"]
    screenshot_save_path = screentShotDir + "\\FastPeopleSearchCom_" + fName + "-" + lName + ".png"
    page = ChromiumPage()
    print("fastpeoplesearch1")
    url = f"https://www.fastpeoplesearch.com/name/{fName}-{lName}_{city}-{state}"
    page.get(url)
    print("fastpeoplesearch2")
    sleep(5)
    
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
            
    sleep(5)
    result_container = page.eles("tag:div@@class=people-list")
    if len(result_container) == 0:
        print("No results found.")
        page.quit()
        return "Not Found"
    else:
        element = result_container[0]
        page.run_js('arguments[0].setAttribute("style", "border: 5px solid red;")', element)
        sleep(4)
        page.get_screenshot(screenshot_save_path)
        page.quit()
        print("Success Confirmation API is sent successfully!")
        return screenshot_save_path