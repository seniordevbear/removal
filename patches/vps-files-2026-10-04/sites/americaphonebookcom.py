from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
os.makedirs(screentShotDir, exist_ok=True)

def get_chromium_options(arguments: list) -> ChromiumOptions:
    """
    Configures and returns Chromium options.
    
    :param browser_path: Path to the Chromium browser executable.
    :param arguments: List of arguments for the Chromium browser.
    :return: Configured ChromiumOptions instance.
    """
    options = ChromiumOptions()
    # options.no_imgs(True)
    # options.no_imgs(True).mute(True).no_js(True)
    # options.set_argument('--auto-open-devtools-for-tabs', 'true') # we don't need this anymore
    for argument in arguments:
        options.set_argument(argument)
    return options

def _human_type2(element , text: str) -> None:
    """
    Types in a way reminiscent of a human, with a random delay in between 50ms to 100ms for every character
    :param element: Input element to type text to
    :param text: Input to be typed
    """

    for c in text:
        element.input(c)

        sleep(random.uniform(0.05, 0.1))

def make_standard_num(num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret

def fill_input_data(page, dataRow) : 
    # 2026-10-04 survey: contact.php no longer has a removal form. The site
    # says "CLICK REMOVE NEXT TO THE LISTING YOU WANT REMOVED": reverse-search
    # the phone number, then click the Remove link beside the listing.
    import re as _re
    helpers = __import__("lib.broker_helpers", fromlist=["missing_pii", "log_step"])
    phone = _re.sub(r"\D", "", dataRow.get("Phone Number") or "")
    if len(phone) == 11 and phone.startswith("1"):
        phone = phone[1:]
    if len(phone) != 10:
        raise helpers.missing_pii("Phone Number")

    page.get("http://americaphonebook.com/")
    sleep(random.uniform(1, 2))
    phone_input = page.ele("tag:input@@name=number")
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, phone)
    search_form = page.ele("tag:form@@name=searchform2")
    search_form.ele("tag:input@@type=submit").click()
    sleep(3)

    if "no match in our free White Pages database" in (page.html or ""):
        helpers.log_step("americaphonebookcom", "number not listed; nothing to remove")
        return "not_listed"

    remove_link = page.ele("tag:a@@text():Remove", timeout=5) or page.ele("tag:a@@href:remov", timeout=2)
    if not remove_link:
        raise RuntimeError("americaphonebookcom: listing page has no Remove link (layout changed)")
    remove_link.click()
    sleep(3)
    return "removed"

def americaphonebookcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\AmericaphonebookCom_" + fName + "-" + lName + ".png"

        arguments = [
            "-no-first-run",
            "--start-maximized",
            "-disable-javascript",
            "-disable-gpu",
            "-disable-sensors",
        ]

        options = get_chromium_options(arguments).auto_port()

        if run_mode == "headless" :
            options.headless()
        
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        fill_input_data(page, dataRow)

        try :
            # response = requests.get(sucessConfirmationApi, timeout=10)
            print("Success Confirmation API is sent successfully!")
            sleep(5)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Success Confirmation API is failed: ", str(e))

        
    except Exception as e:
        try :
            # response = requests.get(errorConfirmationApi, timeout=10)
            print("Error Confirmation API is sent successfully!")
            sleep(5)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Error Confirmation API is failed: ", str(e))
        raise

    finally:
        if page is not None:
            try:
                page.quit()
            except Exception:
                pass

    return screenshot_save_path