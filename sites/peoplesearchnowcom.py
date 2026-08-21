from time import sleep
import logging
import os, datetime, pyautogui, requests, sys, random
from cloudsolver.CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from lib.email_verification import do_email_verification

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
os.makedirs(screentShotDir, exist_ok=True)

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

def peoplesearchnowcom(dataRow, website_name, in_user_email, run_mode):
    page = None
    
    try :
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\PeopleSearchNowCom_" + fName + "-" + lName + ".png"

        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        arguments = [
            "-no-first-run",
            "--start-maximized",
            "-force-color-profile=srgb",
            "-metrics-recording-only",
            "-password-store=basic",
            "-use-mock-keychain",
            "-export-tagged-pdf",
            "-no-default-browser-check",
            "-disable-background-mode",
            "-enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions",
            "-disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage",
            "-deny-permission-prompts",
            "-disable-gpu",
            "-accept-lang=en-US",
        ]
        
        options = get_chromium_options(arguments).add_extension("extension")
        options.add_extension("adblock")
        options.auto_port()

        if run_mode == 'headless':
            options.headless()
            
        page = ChromiumPage(addr_or_opts=options)

        url="https://www.peoplesearchnow.com/opt-out"
        page.get(url)

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

        understand_checkbox = page.ele("tag:input@@id=iUnderstand")
        understand_checkbox.click()
        sleep(1)
        agree_checkbox = page.ele("tag:input@@id=iAgree")
        agree_checkbox.click()        

        email_input = page.ele("tag:input@@id=emailForOptout")
        email_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(email_input, generate_email(dataRow["Name"]))


        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        try :
            site_key = "6Lf3hJYeAAAAACzzrK8vMrDvVbOwFZXqDh68Ut1v"
            site_url = "https://www.peoplesearchnow.com/opt-out"
            result = solver.recaptcha(site_key, site_url)
            print("Captcha is solved.")
            print(result["code"])
            Code = result["code"]
        except Exception as e:
            print("Error: ", str(e))


        iframe_container = page.ele("tag:iframe@@title=reCAPTCHA")
        recaptcha_input_token = iframe_container.ele("tag:input@@id=recaptcha-token")
        recaptcha_input_token.set.attr("value", Code)

        textarea_token = page.ele("tag:textarea@@id=g-recaptcha-response")
        textarea_token.set.innerHTML(Code)

        iframe_container1 = page.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
        recaptcha_input_token1 = iframe_container1.ele("tag:input@@id=recaptcha-token")
        recaptcha_input_token1.set.attr("value", Code)

        form_container = page.ele("tag:form@@id=fio")      
        page.run_js("arguments[0].submit();", form_container)

        # sleep(2)
        
        fullName_input = page.ele("tag:input@@name=name")
        fullName_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(fullName_input, dataRow["Name"])

        city_input = page.ele("tag:input@@name=city")
        city_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(city_input, dataRow["City"])

        state_select = page.ele("tag:select@@name=state")
        __import__("lib.broker_helpers", fromlist=["select_state"]).select_state(state_select, dataRow["State"])

        fio_form = page.ele("tag:form@@name=fio")
        search_btn = fio_form.eles("tag:button")
        print(len(search_btn))
        print(search_btn[0])
        print(search_btn[1])
        search_btn[0].click()
        
        # page.run_js("arguments[0].click();", search_btn[0])

        # try:
        #     sleep(1)

        #     bypasser = CloudflareBypasser(page)
        #     bypasser.bypass()
        # except Exception as e:
        #     pass

        sleep(1)
        details_btn = page.eles("tag:a@@text()=view all info")
        if len(details_btn) > 0 :
            details_btn[0].click()

            sleep(0.5)
            remove_btn = page.ele("tag:a@@title=Remove Record")
            remove_btn.click()            

            # sleep(15)
            # privacy_name = "PeopleSearchNow Support"
            # do_email_verification(privacy_name)

        
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
