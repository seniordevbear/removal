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

def blockshoppercom(dataRow, website_name, in_user_email, run_mode) : 
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name
    screenshot_save_path = screentShotDir + "\\BlockShopperCom_" + fName + "-" + lName + ".png"
    page = ChromiumPage()
    url = f"https://blockshopper.com/search?type=locations&q={fName}"
    page.get(url)
    sleep(5)
    page.get_screenshot(screenshot_save_path)
    page.quit()

    return screenshot_save_path