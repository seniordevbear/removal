from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests

from twocaptcha import TwoCaptcha

apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
solver = TwoCaptcha(apiKey)

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

    email_input = page.ele("tag:input@@name=email")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, dataRow["User Email"])

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

    address_input = page.ele("tag:input@@name=address")
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])

    city_input = page.ele("tag:input@@name=city")
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    state_input = page.ele("tag:input@@name=state")
    state_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(state_input, dataRow["State"])
   
    zip_input = page.ele("tag:input@@name=zip")
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    human_input = page.ele("tag:input@@name=prove_you_are_human")
    human_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(human_input, "25")

def giantpartnerscom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\GiantPartnersCom_" + fName + "-" + lName + ".png"
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
        page.get("https://giantpartners.com/do-not-sell-my-personal-info-all-other-states/")

        sleep(2)

        fill_input_data(page, dataRow)

        print('Captcha is solving....')
        try:
          sitekey = "6Ld_ad8ZAAAAAAqr0ePo1dUfAi0m4KPkCMQYwPPm"

          url = "https://giantpartners.com/do-not-sell-my-personal-info-all-other-states/"
          
          result = solver.recaptcha(sitekey=sitekey, url=url)
        #   print(result)
          Code=result['code']

          print('Captcha is solve. Code:',Code)
        except Exception as e:
          pass
        iframe_container = page.ele("tag:iframe@@id=hs-form-iframe-0")
        sleep(0.5)
        form_container = iframe_container.ele("tag:form")
        print(form_container)
        sleep(0.5)
        recaptcha_iframe_container = iframe_container.ele("tag:iframe@@title=reCAPTCHA")
        print(recaptcha_iframe_container)
        sleep(0.5)
        recaptcha_response_textarea = form_container.ele("tag:textarea@@id=g-recaptcha-response")
        recaptcha_response_textarea.set.innerHTML(Code)
        print(recaptcha_response_textarea)

        recaptcha_token = recaptcha_iframe_container.ele("tag:input@@id=recaptcha-token")
        recaptcha_token.set.attr("value", Code)
        sleep(0.5)

        recaptcha_response_input = form_container.ele("tag:input@@id=hs-recaptcha-response")
        recaptcha_response_input.set.attr("value", Code)
        print(recaptcha_response_input)

        sleep(0.5)
        div_container = page.ele("tag:div@@id=hs-outer-captcha-target-0")
        print(div_container)
        sleep(0.5)
        div_temp = div_container.ele("tag:div@@class=grecaptcha-badge")
        sleep(0.5)
        textarea_1 = div_temp.ele("tag:textarea@@id=g-recaptcha-response")
        textarea_1.set.innerHTML(Code)
        print(textarea_1)

        form_container.run_js("this.submit()")

        
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