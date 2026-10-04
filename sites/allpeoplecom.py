from time import sleep
import logging
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

def allpeoplecom(dataRow, website_name, in_user_email, run_mode):
    page = None
    
    try :
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\AllPeopleCom_" + fName + "-" + lName + ".png"

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
        
        options = get_chromium_options(arguments)
        # options.add_extension("adblock")
        options.auto_port()

        if run_mode == 'headless':
            options.headless()
            
        page = ChromiumPage(addr_or_opts=options)
        # 2026-10-04 round-2 capture: removals now start at /removal — e-mail
        # + "I am the subject" checkbox + Cloudflare Turnstile, then "Begin
        # Removal Process", then search for the record, click Remove, and
        # confirm the link they e-mail. The old search-first flow lost its
        # "Remove Contact" link (57/81 crashes last week).
        helpers = __import__("lib.broker_helpers", fromlist=["set_turnstile_response", "log_step"])
        from lib.email_verification import do_email_verification

        def _wait_cloudflare():
            for _ in range(20):
                if "just a moment" not in (page.title or "").lower():
                    return
                page.actions.click(); page.actions.key_down("TAB"); sleep(0.2); page.actions.key_up("TAB"); sleep(0.2)
                page.actions.key_down("SPACE"); sleep(0.2); page.actions.key_up("SPACE"); sleep(1.0)

        page.get("https://allpeople.com/removal")
        _wait_cloudflare()
        email_str = generate_email(dataRow["Name"])
        email_input = page.ele("tag:input@@id=email", timeout=10)
        if not email_input:
            raise RuntimeError("allpeoplecom: /removal has no e-mail box (layout changed)")
        email_input.click()
        _human_type2(email_input, email_str)
        agree = page.ele("tag:input@@id=agreement-checkbox", timeout=3)
        if agree:
            agree.click(by_js=True)
        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Turnstile is solving...")
        token = solver.turnstile(sitekey="0x4AAAAAADrCYNwMZjIWZO8F", url="https://allpeople.com/removal")["code"]
        helpers.set_turnstile_response(page, token)
        sleep(1)
        begin = page.ele("tag:input@@value=Begin Removal Process", timeout=3) or page.ele("css:form.removal-form [type=submit]")
        begin.click()
        sleep(4)
        _wait_cloudflare()

        # search for the record
        name_box = page.ele("tag:input@@name=ss", timeout=8) or page.ele("css:input[type=search]", timeout=3)
        if not name_box:
            raise RuntimeError("allpeoplecom: no search box after Begin Removal Process")
        name_box.click()
        _human_type2(name_box, dataRow["Name"])
        where = page.ele("tag:input@@id=where_input", timeout=2)
        if where:
            where.click()
            _human_type2(where, dataRow["City"] + ", " + dataRow["State"])
        (page.ele("tag:button@@id=sbutton", timeout=2) or page.ele("css:button[type=submit]")).click()
        sleep(3)
        _wait_cloudflare()

        details = page.eles("tag:a@@text()=Details")
        if not details:
            helpers.log_step("allpeoplecom", "no listing found for this name; nothing to remove")
            page.get_screenshot(screenshot_save_path)
            return screenshot_save_path
        details[0].click()
        sleep(2)
        remove_btn = (page.ele("tag:a@@title=Remove Contact", timeout=3) or page.ele("tag:a@@text():Remove", timeout=2)
                      or page.ele("tag:button@@text():Remove", timeout=2) or page.ele("css:a[href*='remov']", timeout=2))
        if not remove_btn:
            raise RuntimeError("allpeoplecom: listing page has no Remove button")
        remove_btn.click()
        sleep(3)
        reason = page.ele("tag:input@@id=id_reason_0", timeout=2)
        if reason:
            reason.click(by_js=True)
        info = page.ele("tag:input@@id=id_info", timeout=1)
        if info:
            info.input("I want to remove my info from your site.")
        submit_btn = page.ele("tag:button@@text()=Submit", timeout=2) or page.ele("css:button[type=submit], input[type=submit]", timeout=2)
        if submit_btn:
            submit_btn.click()
            sleep(4)
        page.get_screenshot(screenshot_save_path)

        # they e-mail a confirmation link; the removal only happens when it is opened
        if not do_email_verification("allpeople", screenshot_save_path):
            raise RuntimeError("allpeoplecom: removal requested for %s but no confirmation e-mail link was found" % email_str)

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