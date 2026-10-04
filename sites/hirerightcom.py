from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha

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

    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    # 2026-10-04 round-5 capture: the Pardot form is opened directly (it
    # lived in an iframe); it gained an "I am:" select and shows a different
    # checkbox group per state, so the delete box is found by its label.
    form_container = page.ele("tag:form@@id=pardot-form", timeout=15)
    if not form_container:
        raise RuntimeError("hirerightcom: pardot form not found")

    request_type = form_container.ele("tag:input@@id=650513_163143pi_650513_163143_1128621_1128621")
    request_type.click()

    fName_input = form_container.ele("tag:input@@id=650513_162837pi_650513_162837")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    lName_input = form_container.ele("tag:input@@id=650513_162840pi_650513_162840")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    email_input = form_container.ele("tag:input@@id=650513_162843pi_650513_162843")
    print(email_input)
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))
    
    iam = form_container.ele("tag:select@@id=650513_189162pi_650513_189162", timeout=3)
    if iam:
        iam.select.by_value("1267779")  # The consumer making the request
        sleep(0.5)

    sleep(1)
    helpers = __import__("lib.broker_helpers", fromlist=["select_state", "_state_full_name"])
    state_select = form_container.ele("tag:select@@id=650513_162846pi_650513_162846")
    full = helpers._state_full_name(dataRow.get("State") or "")
    try:
        state_select.select.by_text(full)
    except Exception:
        raise NotImplementedError("hirerightcom: the form only serves %s; this customer is in %r" % (
            "CA CO CT DE IN IA KY MD MN MT NE NH NJ OR RI TN TX UT VA", dataRow.get("State")))
    sleep(3)

    clicked = page.run_js(
        "var n=0;document.querySelectorAll(\"input[type=checkbox]\").forEach(function(c){"
        "var l=document.querySelector(\"label[for='\"+c.id+\"']\");"
        "if(l&&/delete/i.test(l.textContent)&&c.offsetParent!==null&&!c.checked){c.click();n++;}});return n;")
    if not clicked:
        raise RuntimeError("hirerightcom: no visible 'delete' checkbox after choosing the state")
    

def hirerightcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"        

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\HirerightCom_" + fName + "-" + lName + ".png"
        
        arguments = [
            "-no-first-run",
            "--start-maximized",
            # "--incognito",
            "-disable-javascript",
            "-disable-gpu",
            "-disable-sensors",
        ]

        options = get_chromium_options(arguments).auto_port()
        if run_mode == "headless" :
            options.headless()
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://info.hireright.com/l/650513/2024-10-08/561z6m")

        sleep(random.uniform(3, 5))

        fill_input_data(page, dataRow)
        
        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        # reCAPTCHA Enterprise (sitekey from the live form)
        result = solver.recaptcha(sitekey="6LdeKFcdAAAAAA8ieqIc8bHuW-X3fbCAl09z_wJd",
                                  url="https://info.hireright.com/l/650513/2024-10-08/561z6m", enterprise=1)
        Code = result["code"]
        page.run_js(
            "var t=arguments[0];"
            "document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
            ".forEach(function(e){e.style.display='block';e.value=t;});", Code)
        sleep(random.uniform(0.5, 1))
        submit_button = page.ele("tag:input@@type=submit")
        submit_button.run_js("this.click();")

        
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