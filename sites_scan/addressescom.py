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

def addressescom(dataRow, website_name, in_user_email, run_mode) :
    page = ChromiumPage()
    try:
        state = dataRow["State"]
        print(state.capitalize())
        if state.capitalize() in usaStateDictionary :
            state = usaStateDictionary[state.capitalize()].lower()
        else :
            state = "ny"
        fName = (dataRow["Name"].split()[0]).lower() # split string based on space to get first name
        lName = (dataRow["Name"].split()[-1]).lower()# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\\AddressesCom_" + fName + "-" + lName + ".png"
        url = f"https://www.addresses.com/people/{fName}+{lName}/{state}/"
        page.get(url)
        sleep(2)
            
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
        page.ele("tag:div@@id=checkbox").click()
        sleep(5)
        people_container = page.ele("tag:div@@class=people-container")
        if people_container:
            result = page.eles("tag:div@@class=person")
            if result:
                print(result)
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
    except Exception as e:
        print("Error Confirmation API is failed: ", str(e))
        page.quit()
        return "Not Found"