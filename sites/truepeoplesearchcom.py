from time import sleep
import logging
import os, datetime, pyautogui, requests, sys, random
from cloudsolver.CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from DrissionPage.common import Keys
from lib.email_verification import do_email_verification

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)

print(screentShotDir)

os.makedirs(screentShotDir, exist_ok=True)

usaStateDictionary = { 'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY' }

def _human_type2(element , text: str) -> None:
    """
    Types in a way reminiscent of a human, with a random delay in between 50ms to 100ms for every character
    :param element: Input element to type text to
    :param text: Input to be typed
    """

    for c in text:
        element.input(c)

        sleep(random.uniform(0.05, 0.1))

def get_chromium_options(arguments: list) -> ChromiumOptions:
    """
    Configures and returns Chromium options.
    
    :param browser_path: Path to the Chromium browser executable.
    :param arguments: List of arguments for the Chromium browser.
    :return: Configured ChromiumOptions instance.
    """
    options = ChromiumOptions()
    # options.set_argument('--auto-open-devtools-for-tabs', 'true') # we don't need this anymore
    for argument in arguments:
        options.set_argument(argument)
    return options


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


def truepeoplesearchcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\TruePeopleSearchCom_" + fName + "-" + lName + ".png"

        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        #Launch Website
        arguments = [
            "-no-first-run",
            "--start-maximized",
            # "--incognito",
            "-disable-javascript",
            "-disable-gpu",
            "-disable-sensors",
        ]

        port_arr = [
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10008",
            "10009",
            "10010"
        ]

        random_number = random.randint(0, 9)

        username = os.getenv("SMARTPROXY_USER", "")
        password = os.getenv("SMARTPROXY_PASSWORD", "")
        endpoint = os.getenv("SMARTPROXY_ENDPOINT", "isp.smartproxy.com")
        port = port_arr[random_number]

        proxy_extension = proxies(username, password, endpoint, port)

        options = get_chromium_options(arguments).auto_port().add_extension("extension")

        options.add_extension("adblock")

        if run_mode == "headless" :
            options.headless()
        
            
        page = ChromiumPage(addr_or_opts=options)

        page.get("https://www.truepeoplesearch.com/removal")

        fill_input_data(page, dataRow)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        site_key = "8c6693a8-2959-420f-ba6c-474f2460a6cf"
        url = "https://www.truepeoplesearch.com/removal"

        solver = TwoCaptcha(apiKey)

        print("Captcha is solving.....")
        try:
            result = solver.hcaptcha(sitekey=site_key, url=url)
            
            Code = result['code']
            # print(result)
            print("Captcha is solved")
            print(result)
        except Exception as e:
            print(e)

        captcha_iframe = page.ele("tag:iframe@@title=Widget containing checkbox for hCaptcha security challenge")

        captcha_iframe.set.attr("data-hcaptcha-response", Code)

        form_container = page.ele("tag:form@@role=form")

        g_textarea = page.ele("tag:textarea@@name=g-recaptcha-response")
        # g_textarea.set.attr("value", Code)
        g_textarea.set.innerHTML(Code)

        h_textarea = page.ele("tag:textarea@@name=h-captcha-response")
        # h_textarea.set.attr("value", Code)
        h_textarea.set.innerHTML(Code)

        begin_button = page.ele("tag:button@@text()=Begin Removal")
        print(begin_button)
        sleep(random.uniform(0.1, 0.5))
        begin_button.click()

        sleep(5)

        fullName_input = page.ele("tag:input@@name=Name")
        fullName_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(fullName_input, dataRow["Name"])

        city_state_input = page.ele("tag:input@@name=CityStateZip")
        city_state_input.click()
        print("typing the city...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(city_state_input, dataRow["City"]+", "+ __import__("lib.broker_helpers", fromlist=["state_abbrev"]).state_abbrev(dataRow["State"]))

        search_btn = page.ele("tag:button@@id=btnSubmit-d-n")
        search_btn.click()

        sleep(5)

        current_year = now.year
        birth_year = dataRow["Birth Year"]
        age = current_year - birth_year

        body_element = page.ele("tag:body")
        div_container = body_element.children()[2]
        cards =div_container.eles("tag:div@@class=card card-body shadow-form card-summary pt-3")

        if len(cards) > 0 :
            info_row = cards[0].children()[0]
            info_row.click()
            sleep(2)
            remove_btn = page.ele("tag:a@@text()=Remove This Record")
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