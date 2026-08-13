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

def spokeocom(dataRow, website_name, in_user_email, run_mode) : 
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name
    screenshot_save_path = screentShotDir + "\\SpokeoCom_" + fName + "-" + lName + ".png"
    page = ChromiumPage()
    url = f"https://www.spokeo.com/search/{fName}-{lName}"
    page.get(url)
    sleep(5)
    result_container = page.eles("tag:div@@role=listitem")
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