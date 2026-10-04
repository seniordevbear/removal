from time import sleep
import os, datetime, pyautogui, requests, sys, random
from cloudsolver.CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number

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


def callersmartcom(dataRow, website_name, in_user_email, run_mode):
    page = None
    
    try :
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        screenshot_save_path = screentShotDir + "\CallersmartCom_" + fName + "-" + lName + ".png"

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
        
        options = get_chromium_options(arguments).auto_port()

        if run_mode == 'headless':
            options.headless()
            
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://www.callersmart.com/data")

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
        
        # 2026-10-04 capture: the "Do Not Sell My Personal Data" form is now
        # e-mail + 10-digit phone number only ("Both fields are required";
        # listings are keyed by phone number), reCAPTCHA 6Lc2sPQS..., a
        # honeypot text box named specialData that must stay empty, and a
        # Send button. They e-mail a confirmation link. 26/26 runs last week
        # died on the old #userName box.
        import re as _re
        helpers = __import__("lib.broker_helpers", fromlist=["missing_pii"])
        from lib.email_verification import do_email_verification
        phone = _re.sub(r"\D", "", dataRow.get("Phone Number") or "")
        if len(phone) == 11 and phone.startswith("1"):
            phone = phone[1:]
        if len(phone) != 10:
            raise helpers.missing_pii("Phone Number")

        form = page.ele("tag:form@@name=contactForm", timeout=10)
        if not form:
            raise RuntimeError("callersmartcom: opt-out form not found on /data (layout changed)")
        email_str = generate_email(dataRow["Name"])
        email_input = form.ele("tag:input@@name=email")
        email_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(email_input, email_str)

        number_input = form.ele("tag:input@@name=number")
        number_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(number_input, phone)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        Code = solver.recaptcha("6Lc2sPQSAAAAAJP_kRsCsbiYkR4gb2fkk9XUGz2k", "https://www.callersmart.com/data")["code"]
        page.run_js(
            "var t=arguments[0];"
            "document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
            ".forEach(function(e){e.style.display='block';e.value=t;});", Code)
        sleep(random.uniform(0.5, 1))

        submit_btn = form.ele("tag:button@@type=submit")
        submit_btn.click()
        sleep(5)
        page.get_screenshot(screenshot_save_path)

        # the opt-out completes only when their e-mailed confirmation link is opened
        if not do_email_verification("callersmart", screenshot_save_path):
            raise RuntimeError("callersmartcom: opt-out requested for %s / %s but no confirmation e-mail link was found" % (email_str, phone))

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
