from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests, sys
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha

api_key = os.getenv("TWOCAPTCHA_API_KEY", "")
solver = TwoCaptcha(api_key)

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
    
    state_select = page.ele("tag:select@@id=ccpa_state")
    print(state_select)
    state_select.select.by_text(dataRow["State"])

    fName_input = page.ele("tag:input@@name=firstname")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    lName_input = page.ele("tag:input@@name=lastname")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)
    
    form_container = page.ele("tag:form@@id=step2_form")
    email_str = generate_email(dataRow["Name"])
    email_input = form_container.ele("tag:input@@name=email")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, email_str)

    detail_textarea = form_container.ele("tag:textarea@@name=message")
    detail_textarea.click()
    print("typing the message...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(detail_textarea, "I want to remove my info")

    checkbox1 = form_container.ele("tag:input@@value=All specific information related to me that Social Catfish has in its possession.")
    checkbox1.click()
    sleep(1)
    checkbox2 = form_container.ele("tag:input@@value=Some of the specific information related to me that Social Catfish in its possession, please give specifics below.")
    checkbox2.click()
    sleep(1)
    checkbox3 = form_container.ele("tag:label@@id=third_party_option")
    checkbox3.click()
    sleep(1)
    checkbox4 = form_container.ele("tag:label@@class:state_chk")
    checkbox4.click()

def socialcatfishcom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\SocialcatFishCom_" + fName + "-" + lName + ".png"
        
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        arguments = [
            "-no-first-run",
            "--start-maximized",
            # "--incognito",
            "-disable-javascript",
            "-disable-gpu",
            "-disable-sensors",
        ]

        options = get_chromium_options(arguments).auto_port().add_extension("adblock")
        if run_mode == "headless" :
            options.headless()
        
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://socialcatfish.com/opt-out/?id=request_delete")

        sleep(random.uniform(1, 2))       

        fill_input_data(page, dataRow)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        
        print("captcha solving...")
        try :
            site_key = "0x4AAAAAABBx2maaNn3YHtY1"
            url = page.url
            result = solver.turnstile(sitekey=site_key, url=url)
            code = result["code"]
            print(code)
        except Exception as e:
            print("Error: ", str(e))

        token_input = page.ele('tag:input@@name=cf-turnstile-response')
        print(token_input)
        token_input.set.attr("value", code)
        
        sleep(1)
        
        submit_button = page.ele("tag:a@@id=ccpa_delete")
        submit_button.click()

        
        try :
            # response = requests.get(sucessConfirmationApi, timeout=10)
            print("Success Confirmation API is sent successfully!")
            sleep(10)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Success Confirmation API is failed: ", str(e))
        
    except Exception as e:
        try :
            # response = requests.get(errorConfirmationApi, timeout=10)
            print("Error Confirmation API is sent successfully!")
            sleep(10)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Error Confirmation API is failed: ", str(e))

    page.quit()

    return screenshot_save_path