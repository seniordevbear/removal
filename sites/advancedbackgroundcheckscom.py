from time import sleep
import os, datetime, pyautogui, requests, sys, random
from cloudsolver.CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from lib.email_verification import do_email_verification
from lib.broker_helpers import user_age

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


def advancedbackgroundcheckscom(dataRow, website_name, in_user_email, run_mode):
    page = None
    
    try :
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\AdvancedBackgroundChecksCom_" + fName + "-" + lName + ".png"
        
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
        options.add_extension("adblock")
        options.auto_port()

        if run_mode == 'headless':
            options.headless()
            
        page = ChromiumPage(addr_or_opts=options)

        # 2026-10-04 round-2 capture: /removal is a 404. The opt-out now starts
        # at /opt-out: "I am" (subject), first/last name, e-mail, reCAPTCHA
        # (6LdYzess...), honeypot input name=company that must stay empty.
        # They e-mail a link to the real opt-out form; we open it from the
        # confirmation mailbox and fill whatever it asks for.
        helpers = __import__("lib.broker_helpers", fromlist=["log_step", "find_input", "safe_select"])
        from lib.email_verification import do_email_verification

        url = "https://www.advancedbackgroundchecks.com/opt-out"
        page.get(url)
        for _ in range(20):
            if "just a moment" not in (page.title or "").lower():
                break
            page.actions.click(); page.actions.key_down("TAB"); sleep(0.2); page.actions.key_up("TAB"); sleep(0.2)
            page.actions.key_down("SPACE"); sleep(0.2); page.actions.key_up("SPACE"); sleep(1.0)

        fName = dataRow["Name"].split()[0]
        lName = dataRow["Name"].split()[-1]
        mode = page.ele("tag:select@@id=mode", timeout=10)
        if not mode:
            raise RuntimeError("advancedbackgroundcheckscom: /opt-out form not found (layout changed)")
        mode.select.by_value("subject")
        email_str = generate_email(dataRow["Name"])
        for fid, val in (("sfn", fName), ("sln", lName), ("semail", email_str)):
            el = page.ele("tag:input@@id=" + fid)
            el.click()
            sleep(random.uniform(0.1, 0.4))
            _human_type2(el, val)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        Code = solver.recaptcha("6LdYzessAAAAACnQqZugXee4rNpMsD-6X1paSkS8", url)["code"]
        page.run_js(
            "var t=arguments[0];"
            "document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
            ".forEach(function(e){e.style.display='block';e.value=t;});", Code)
        sleep(1)
        page.ele("css:form button[type=submit]").click()
        sleep(5)
        page.get_screenshot(screenshot_save_path)

        def _fill_optout_form(tab):
            # The e-mailed link opens the actual opt-out form. Its fields have
            # not been captured yet, so match by id/name/placeholder.
            def box(aliases):
                cands = []
                for a in aliases:
                    cands += ["css:input[id*='%s' i]" % a, "css:input[name*='%s' i]" % a, "css:input[placeholder*='%s' i]" % a]
                try:
                    return helpers.find_input(tab, *cands, timeout=2.0)
                except ValueError:
                    return None
            filled = 0
            for aliases, val in ((("first", "fname"), fName), (("last", "lname"), lName),
                                 (("address", "street"), dataRow.get("Address") or ""),
                                 (("city",), dataRow.get("City") or ""),
                                 (("zip", "postal"), str(dataRow.get("Zipcode") or "")),
                                 (("age",), str(dataRow.get("Age") or ""))):
                el = box(aliases)
                if el and val:
                    el.click(); el.input(val); filled += 1
            try:
                helpers.safe_select(tab, "css:select[id*='state' i], select[name*='state' i]", dataRow.get("State") or "", timeout=2.0)
            except Exception:
                pass
            btn = tab.ele("css:button[type=submit], input[type=submit]", timeout=3)
            if not filled or not btn:
                raise RuntimeError("advancedbackgroundcheckscom: e-mailed opt-out form not recognised (filled %d boxes, submit=%s) — capture it" % (filled, bool(btn)))
            btn.click()
            sleep(5)
            tab.get_screenshot(screenshot_save_path)

        if not do_email_verification("advancedbackgroundchecks", screenshot_save_path, after_click=_fill_optout_form, to_address=email_str):
            raise RuntimeError("advancedbackgroundcheckscom: opt-out link requested but no e-mail link was found")

        sleep(2)
        
        page.wait.ele_displayed("tag:input@@id=search-name-name")
        fullName_input = page.ele("tag:input@@id=search-name-name")
        fullName_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(fullName_input, dataRow["Name"])

        city_state = dataRow["City"] + ", " + __import__("lib.broker_helpers", fromlist=["state_abbrev"]).state_abbrev(dataRow["State"])
        city_state_input = page.ele("tag:input@@id=search-name-address")
        city_state_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(city_state_input, city_state)

        current_year = now.year
        birth_year = dataRow["Birth Year"]
        age = user_age(dataRow)  # int-safe; IncompletePII if no birth year/age

        age_input = page.ele("tag:input@@id=search-name-age")
        age_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(age_input, str(age))

        search_btn = page.ele("tag:button@@name=search")
        search_btn.click()

        details_btn = page.eles("tag:a@@text()=View Details")
        if len(details_btn) > 0 :
            details_btn[0].click()

            sleep(0.5)
            remove_btn = page.ele("tag:a@@title=Remove this record")
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
            print("Error Confirmation API is sent successfully!",e)
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

