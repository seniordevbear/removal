from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
import re

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
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

def fill_input_data(page, dataRow) : 
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    email_input = page.ele("tag:input@@id=Email")
    email_input.click()
    print("typing the email name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    sleep(0.5)
    checkbox_element = page.ele("tag:input@@class=big-checkbox")
    print(checkbox_element)
    checkbox_element.run_js("this.click();")


def nuwbercom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + r"\NuwberCom_" + fName + "-" + lName + ".png"

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
        options = get_chromium_options(arguments).auto_port()
        if run_mode == "headless" :
            options.headless()
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)

        page.get("https://nuwber.com/")
        sleep(1)

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

        fullName_input = page.ele("tag:input@@id=search-panel_name")
        fullName_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(fullName_input, dataRow["Name"])

        city_state = dataRow["City"] + ", " + usaStateDictionary[dataRow["State"]]
        city_state_input = page.ele("tag:input@@id=search-panel_state")
        city_state_input.click()
        print("typing the city and state name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(city_state_input, city_state)

        search_section = page.ele("tag:section@@class:home-heading")
        search_button = search_section.ele("tag:button@@type=submit@@text()=Search")
        print(search_button)
        search_button.click()
       
        try :
            page.wait.ele_displayed("tag:input@@id=fcra-check")
            accept_checkbox = page.ele("tag:input@@id=fcra-check")
            print(accept_checkbox)
            accept_checkbox.click()
            sleep(1)
            section_content = page.ele('tag:section@@class=content')
            print(section_content)
            accept_button = section_content.ele("tag:button@@class:common-button")
            print(accept_button)
            accept_button.click()
        except :
            pass

        search_page = page.ele("tag:div@@id=search-page")
        people_list = search_page.eles("tag:div@@class=result-block")

        current_year = now.year
        birth_year = dataRow["Birth Year"]
        age = current_year - birth_year

        if len(people_list) > 0 :
            profile_url = people_list[0].ele("tag:a").attr("href")            
                
            page.get("https://nuwber.com/removal/link")
            sleep(2)

            profile_url_input = page.ele("tag:input@@id=removebylink-link")
            profile_url_input.click()
            print("typing the profile url...")
            sleep(random.uniform(0.1,0.5))
            _human_type2(profile_url_input, profile_url)
            
            submit_button = page.ele("tag:input@@value=Opt out")
            submit_button.click()                

            sleep(1)
            email_input = page.ele("tag:input@@id=removebylink-email")
            email_input.click()
            print("typing the profile url...")
            sleep(random.uniform(0.1,0.5))
            _human_type2(email_input, generate_email(dataRow["Name"]))

            remove_btn = page.ele("tag:button@@text()=Remove")
            remove_btn.click()                            
        
    
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