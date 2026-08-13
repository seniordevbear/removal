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

def allpeoplecom(dataRow, website_name, in_user_email, run_mode) : 
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name
    screenshot_save_path = screentShotDir + "\\AllPeopleCom_" + fName + "-" + lName + ".png"
    page = ChromiumPage()
    url = f"https://allpeople.com/search?ss={fName}+{lName}+&ss-e=&ss-p=&ss-i=&where={dataRow['City']}%2C+{dataRow['State']}&industry-auto=&where-auto="
    page.get(url)
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
    is_search = page.ele("tag:h3@@style=font-size: 12px; color: #577594;")
    if not is_search:
        print("Search OK")
        search_results = page.eles("tag:div@@class=rev-flex rev-flex-s")
        if search_results:
            result = search_results[0]
            page.run_js('arguments[0].setAttribute("style", "border: 5px solid red;")', result)
            sleep(4)
            page.get_screenshot(screenshot_save_path)
            page.quit()
            print("Success Confirmation API is sent successfully!")
            return screenshot_save_path
    else:
        print("No results found.")
        page.quit()
        return "Not Found"