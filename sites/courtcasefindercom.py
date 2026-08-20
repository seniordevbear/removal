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


def courtcasefindercom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try :     
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        screenshot_save_path = screentShotDir + "\CourtcasefinderCom_" + fName + "-" + lName + ".png"
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

        if run_mode == "headless" :
            options.headless()
            
        page = ChromiumPage(addr_or_opts=options)

        # Open the target website
        
        page.get("https://courtcasefinder.com/optout")

        sleep(random.uniform(3, 5))

        fName_input = page.ele("tag:input@@id:fname")
        fName_input.click()
        print("typing the first name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(fName_input, fName)

        lName_input = page.ele("tag:input@@id:lname")
        lName_input.click()
        print("typing the last name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(lName_input, lName)

        state_select = page.ele("tag:select@@id:state")
        state_select.select.by_text(dataRow["State"])
        
        city_input = page.ele("tag:input@@id:city")
        city_input.click()
        print("typing the city name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(city_input, dataRow["City"])

        submit_button = page.ele("tag:button@@type=submit")
        submit_button.click()

        sleep(2)

        checkbox = page.ele("tag:input@@id=notrobl")
        checkbox.click()

        sleep(5)

        current_year = now.year
        birth_year = dataRow["Birth Year"]
        age = current_year - birth_year
        print(age)

        tbody_element = page.ele("tag:tbody")
        print(tbody_element)

        rows = tbody_element.eles("tag:tr")
        
        
        if len(rows) > 0 :
            rows[0].ele("tag:input@@type=checkbox").click()
            sleep(1)
            rows[0].ele("tag:button@@type=submit").click()
            
            email_input = page.ele("tag:input@@id=DataRemovalFormModel_email")
            email_input.click()
            print("typing the email name...")
            sleep(random.uniform(0.1,0.5))
            _human_type2(email_input, generate_email(dataRow["Name"]))

            comment_textarea = page.ele("tag:textarea@@id=DataRemovalFormModel_comment")
            comment_textarea.click()
            
            sleep(random.uniform(0.1,0.5))
            _human_type2(comment_textarea, 'I want to remove my info.')

            apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
            solver = TwoCaptcha(apiKey)
            print("Captcha is solving...")
            try :
                site_key = "6LcB808UAAAAAAqr91WUtrhYLaBAXkCTPZbxilo5"
                site_url = page.url
                result = solver.recaptcha(site_key, site_url)
                print("Captcha is solved.")
                print(result["code"])
                Code = result["code"]
            except Exception as e:
                print("Error: ", str(e))


            iframe_container = page.ele("tag:iframe@@title=reCAPTCHA")
            print(iframe_container)
            recaptcha_input_token = iframe_container.ele("tag:input@@id=recaptcha-token")
            recaptcha_input_token.set.attr("value", Code)

            textarea_token = page.ele("tag:textarea@@id=g-recaptcha-response")
            print(textarea_token)
            textarea_token.set.innerHTML(Code)

            iframe_container1 = page.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
            recaptcha_input_token1 = iframe_container1.ele("tag:input@@id=recaptcha-token")
            print(recaptcha_input_token1)
            recaptcha_input_token1.set.attr("value", Code)

            submit_button_final = page.ele("tag:button@@type=submit")
            submit_button_final.click()

            sleep(1)
            
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