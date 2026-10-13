from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from lib.broker_helpers import missing_pii, submission_verdict, unique_shot_path
import re
from urllib.parse import urlencode
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha

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

def spokeocom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        # Two customers can share a name - users 893 and 894 are both
        # Christopher Mayes and both ran spokeo on 2026-10-12 - so the name
        # alone is not a unique filename. unique_shot_path adds thread name,
        # microseconds and a random suffix, the same way shot() does.
        screenshot_save_path = unique_shot_path(screentShotDir, "SpokeoCom", fName, lName)
                
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
        
        # A search with no city, no state and no usable phone returns everyone
        # in the country with this name, and the code below opts out whichever
        # profile happens to sort first. On 2026-10-12 eleven of thirty-two
        # searches ran that way (phone=+1, city=, state=), so the "removal" was
        # a coin toss that could just as easily have de-listed a stranger.
        # Refuse the search instead; step 5 asks for the data we are missing.
        city = (dataRow.get("City") or "").strip()
        state = (dataRow.get("State") or "").strip()
        phone_digits = re.sub(r"\D", "", str(dataRow.get("Phone Number") or ""))
        if phone_digits.startswith("1"):
            phone_digits = phone_digits[1:]
        has_phone = len(phone_digits) == 10

        if not (city and state) and not has_phone:
            missing = []
            if not city:
                missing.append("City")
            if not state:
                missing.append("State")
            if not has_phone:
                missing.append("Phone Number")
            raise missing_pii(*missing)

        params = {}
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if has_phone:
            params["phone"] = "+1" + phone_digits

        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        url = "https://www.spokeo.com/search/%s-%s" % (fName, lName)
        if params:
            url += "?" + urlencode(params)
        print(url)
        page.get(url)

        sleep(random.uniform(3, 5))

        sleep(10)

        # `age` was computed from Birth Year, printed, and then never read.
        # An empty Birth Year therefore threw ValueError("invalid literal for
        # int() with base 10: ''") and failed the whole removal for a number
        # nothing used - 95 times on 2026-10-12 alone. Keep it as a log line
        # when we have it, and carry on when we do not.
        birth_year = str(dataRow.get("Birth Year") or "").strip()
        if birth_year.isdigit():
            print("age about %d" % (now.year - int(birth_year)))
        else:
            print("no birth year on file; cannot narrow by age")

        search_result_div = page.ele("tag:div@@id=name-search-results-list", timeout=15)
        if not search_result_div:
            raise RuntimeError(
                "spokeocom: no search-results list on the page for %s %s "
                "(blocked, captcha, or layout change)" % (fName, lName))
        rows = search_result_div.eles("tag:div@@role=listitem")

        # Until now an empty result list skipped the whole opt-out and fell
        # straight into the "Success Confirmation" block below, which took a
        # screenshot of the empty search page and returned it as a completed
        # removal. Nothing was ever submitted on those runs.
        print("%d candidate profiles" % len(rows))
        if not rows:
            raise RuntimeError(
                "spokeocom: no profile matched %s %s with the location we hold "
                "- nothing was submitted" % (fName, lName))

        if True:
            profile_url = rows[0].ele("tag:a").attr("href")
            print(profile_url)
            sleep(1)
            page.get("https://www.spokeo.com/optout")
            sleep(3)

            page.wait.ele_displayed("tag:iframe@@title=reCAPTCHA")
            sleep(60)

            url_input = page.ele("tag:input@@name=url")
            url_input.click()
            sleep(random.uniform(0.1, 0.5))
            _human_type2(url_input, profile_url)

            email_input = page.ele("tag:input@@name=email")
            email_input.click()
            sleep(random.uniform(0.1, 0.5))
            _human_type2(email_input, generate_email(dataRow["Name"]))
            
            iframe_container = page.ele("tag:iframe@@title=reCAPTCHA")
            print(iframe_container)
            rc_anchor_container = iframe_container("tag:div@@id=rc-anchor-container")
            print(rc_anchor_container)
            rc_anchor_container.click()

            sleep(2)
            page.wait.ele_displayed("tag:iframe@@title=recaptcha challenge expires in two minutes")
            sleep(1)
            iframe_container1 = page.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
            audio_button = iframe_container1.ele("tag:button@@id=recaptcha-audio-button")

            print(audio_button)
            audio_button.click()
            audio_source = iframe_container1.ele("tag:audio@@id=audio-source").attr("src")
            print(audio_source)

            response = requests.get(audio_source)
            with open(("__downloaded_%d.mp3" % __import__("threading").get_ident()), "wb") as file:
                file.write(response.content)

            sleep(1)

            apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
            solver = TwoCaptcha(apiKey)
            print("Captcha is solving...")
            try :
                result = solver.audio(("__downloaded_%d.mp3" % __import__("threading").get_ident()), lang="en")
                print("Captcha is solved.")
                print(result["code"])
                Code = result["code"]
            except Exception as e:
                # Without this the failed solve fell through to _human_type2(..., Code)
                # and raised NameError, which reads as a code bug rather than
                # "2captcha could not solve it".
                raise RuntimeError("spokeocom: audio captcha not solved: %s" % e)
            audio_reponse_input = iframe_container1.ele("tag:input@@id=audio-response")
            _human_type2(audio_reponse_input, Code)

            verify_btn = iframe_container1.ele("tag:button@@id=recaptcha-verify-button")
            verify_btn.click()

            sleep(5)

            submit_button = page.ele("tag:button@@text()=OPT OUT")
            submit_button.click()

            # The click alone was treated as proof. Read the rendered page and
            # let it say so, the same way the other round-6 scripts do.
            submission_verdict(
                page, "spokeocom",
                success_phrases=(
                    "we have received your opt out request",
                    "check your email",
                    "confirmation email",
                    "opt out request",
                ),
            )

        sleep(1)

        try :
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("screenshot failed: ", str(e))
        
    except Exception as e:
        print(e)
        try :
            if page is not None:
                page.get_screenshot(screenshot_save_path)
        except Exception as e2:
            print("failure screenshot failed: ", str(e2))
        raise

    finally:
        if page is not None:
            try:
                page.quit()
            except Exception:
                pass

    return screenshot_save_path