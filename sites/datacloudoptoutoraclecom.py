from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from DrissionPage.common import Keys

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)

print(screentShotDir)

os.makedirs(screentShotDir, exist_ok=True)
usaStateDictionary = { 'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY' }

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
    element.input(Keys.ENTER)

def make_standard_num(num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name
    
    sleep(1)
    div_container = page.ele("tag:div@@class=ot-form-wrapper")
    print(div_container)
    iframe_container = div_container.ele("tag:iframe")
    print(iframe_container)

    state_select = iframe_container.ele("tag:div@@id:000000001004")
    state_select.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(state_select, dataRow["State"])

    request_man = iframe_container.ele("tag:div@@id:000000001001")
    request_man.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(request_man, "Consumer")

    request_type = iframe_container.ele("tag:div@@id:000000001005")
    request_type.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(request_type, "Delete My Information")
    
    
    fName_input = iframe_container.ele("tag:input@@aria-label=Enter First Name")
    fName_input.input(fName)


    lName_input = iframe_container.ele("tag:input@@aria-label=Enter Last Name")
    lName_input.input(lName)

    email_input = iframe_container.ele("tag:input@@aria-label=Enter Email")
    email_input.input(generate_email(dataRow["Name"]))
    
    detail_textarea = iframe_container.ele("tag:textarea@@id:000000001006")
    detail_textarea.input("I want to remove my info.")

    sleep(0.5)

    checkbox = iframe_container.ele("tag:div@@id:000000001007")
    print(checkbox)
    checkbox.click()

def datacloudoptoutoraclecom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name

        screenshot_save_path = screentShotDir + "\DataCloudOptoutOracleCom_" + fName + "-" + lName + ".png"

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
        page.get("https://www.oracle.com/legal/data-privacy-inquiry-form/")

       
        sleep(1)

        div_container = page.ele("tag:div@@class=ot-form-wrapper")
        print(div_container)
        page.wait.eles_loaded("tag:iframe")
        iframe_container = div_container.ele("tag:iframe")
        print(iframe_container)
        page.wait(10) 
        
        sleep(1)     

        fill_input_data(page, dataRow)
        sleep(7)
        submit_button = iframe_container.ele("tag:button@@text()=Submit Request")
        print(submit_button)
        submit_button.run_js("this.click()")

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

    page.quit()

    return screenshot_save_path