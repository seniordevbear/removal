from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import random
import os, datetime, pyautogui, requests
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

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    email_input = page.ele("tag:input@@id=wpforms-208196-field_2")
    email_input.clear()
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))


    address_input = page.ele("tag:input@@id=wpforms-208196-field_7")
    address_input.clear()
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])


    street_input = page.ele("tag:input@@id=wpforms-208196-field_7-address2")
    street_input.clear()
    street_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(street_input, dataRow["Street"])


    city_input = page.ele("tag:input@@id=wpforms-208196-field_7-city")
    city_input.clear()
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    state_element = page.ele("tag:select@@id=wpforms-208196-field_7-state")
    state_element.select.by_text(dataRow["State"])

    zip_input = page.ele("tag:input@@id=wpforms-208196-field_7-postal")
    zip_input.clear()
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

def eprodirectcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\EprodirectCom_" + fName + "-" + lName + ".png"

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
        page.get("https://www.eprodirect.com/do-not-sell-my-personal-information/")

        fill_input_data(page, dataRow)

        sleep(1)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        try :
            site_key = "6LdqRqwUAAAAABZBL31NV_-kI7WHlBsEMTJ_35sR"
            site_url = "https://www.eprodirect.com/do-not-sell-my-personal-information/"
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

        # submit_button = page.ele("tag:button@@id=wpforms-submit-208196")
        # submit_button.click()

        form_container = page.ele("tag:form@@id=wpforms-form-208196")
        form_container.run_js("this.submit();")
        
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