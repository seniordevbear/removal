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
    screenshot_save_path = screentShotDir + "\SpokeoCom_" + fName + "-" + lName + ".png"
    page = ChromiumPage()
    url = f"https://www.spokeo.com/search/{fName}-{lName}"
    page.get(url)
    sleep(1)
    page.get_screenshot(screenshot_save_path)
    page.quit()

    return screenshot_save_path