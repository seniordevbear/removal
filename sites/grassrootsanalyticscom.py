# grassrootsanalyticscom.py - REWRITTEN 2026-05-28
# Old: 0/108 prod success. Wix-built form with auto-generated IDs
# (input_comp-lu8kq...) but stable name= attributes:
# first-name, last-name, email, phone-number, city, street-address, state.
# Multiple "Submit" buttons exist (page has multiple forms in different
# sections); target the one inside the CCPA form via form context.
import os, datetime
from time import sleep
from lib.broker_helpers import (
    safe_chromium_for_broker, dismiss_common_consents,
    find_input, find_button, screenshot_step, log_step,
)
from lib.common import generate_email


def grassrootsanalyticscom(dataRow, website_name, in_user_email, run_mode):
    broker = "grassrootsanalyticscom"
    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    base_dir = os.getcwd()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(base_dir, "ScreenShot", today)
    os.makedirs(out_dir, exist_ok=True)
    screenshot_save_path = os.path.join(out_dir, f"{broker}_{fName}-{lName}.png")

    try:
        with safe_chromium_for_broker(
            broker, use_proxy=True,
            headless=(run_mode == "headless"),
            extra_extensions=["adblock"],
        ) as page:
            page.get("https://www.grassrootsanalytics.com/california-consumer-privacy-act-ccpa")
            sleep(3)
            screenshot_step(page, broker, "01_landed")
            dismiss_common_consents(page, broker)
            sleep(0.5)

            find_input(page, "tag:input@@name=first-name").input(fName)
            find_input(page, "tag:input@@name=last-name").input(lName)
            find_input(page, "tag:input@@name=email").input(generate_email(dataRow["Name"]))
            phone = dataRow.get("Phone Number", "")
            if phone:
                find_input(page, "tag:input@@name=phone-number").input(phone)
            find_input(page, "tag:input@@name=city").input(dataRow.get("City", ""))
            find_input(page, "tag:input@@name=street-address").input(dataRow.get("Address", ""))
            find_input(page, "tag:input@@name=state").input(dataRow.get("State", ""))
            log_step(broker, "filled CCPA form")
            screenshot_step(page, broker, "02_filled")

            # There are multiple Submit buttons (Wix multi-section page).
            # The CCPA form's submit is typically the last visible one.
            # Find ALL and click the one near the bottom of the page.
            buttons = page.eles("tag:button@@type=submit")
            if buttons:
                buttons[-1].click()
                log_step(broker, f"clicked submit ({len(buttons)} candidates)")
                sleep(3)
                screenshot_step(page, broker, "03_submitted")
            else:
                log_step(broker, "NO submit button found")

            try:
                page.get_screenshot(screenshot_save_path)
            except Exception:
                pass
    except Exception as e:
        log_step(broker, f"OUTER FAILURE: {e}")

    return screenshot_save_path
