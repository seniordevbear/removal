from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
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
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    page.wait.ele_displayed("tag:form@@id=gform_5")

    sleep(5)
    form_container = page.ele("tag:form@@id=gform_5")
    page.wait.ele_displayed("tag:input@@id=input_5_12_3")
    sleep(1)
    fName_input = form_container.ele("tag:input@@id=input_5_12_3")
    print(fName_input)
    fName_input.run_js("this.click();")
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    sleep(2)

    lName_input = form_container.ele("tag:input@@name=input_12.6")
    lName_input.run_js("this.click()")
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    address_input = form_container.ele("tag:input@@name=input_13.1")
    address_input.run_js("this.click();")
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])

    city_input = form_container.ele("tag:input@@name=input_13.3")
    city_input.run_js("this.click();")
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    state_input = form_container.ele("tag:input@@name=input_13.4")
    state_input.run_js("this.click();")
    sleep(random.uniform(0.1,0.5))
    _human_type2(state_input, dataRow["State"])

    zip_input = form_container.ele("tag:input@@name=input_13.5")
    zip_input.run_js("this.click();")
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))
    
    country_select = form_container.ele("tag:select@@name=input_13.6")
    country_select.select.by_text("United States")

    email_input = form_container.ele("tag:input@@name=input_8")
    email_input.run_js("this.click();")
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    phone_input = form_container.ele("tag:input@@name=input_15")
    phone_input.run_js("this.click();")
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, generate_phone_number())

    checkbox_element = form_container.ele("tag:input@@name=input_16.1")
    checkbox_element.run_js("this.click();")

def gostratacom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\GostrataCom_" + fName + "-" + lName + ".png"
        
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
        page = ChromiumPage(options)
        page.get("https://www.gostrata.com/do-not-sell-my-personal-information/")

        sleep(random.uniform(1, 2))

        fill_input_data(page, dataRow)

        submit_button = page.ele("tag:input@@id=gform_submit_button_5")
        submit_button.click()

        
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