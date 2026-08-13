# thatsthemcom.py - REWRITTEN 2026-05-28
# Old: 0/107 prod success. Current form at https://thatsthem.com/optout
# has clean id-attributed fields (name, street, city, state-select, zip,
# email, phone) and a single "Submit Opt-Out Request" button. Old
# selectors likely targeted obsolete IDs.
import os, datetime
from time import sleep
from lib.broker_helpers import (
    safe_chromium_for_broker, dismiss_common_consents,
    find_input, find_button, safe_select, screenshot_step, log_step,
)
from lib.common import generate_email


def thatsthemcom(dataRow, website_name, in_user_email, run_mode):
    broker = "thatsthemcom"
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
            page.get("https://thatsthem.com/optout")
            sleep(3)
            screenshot_step(page, broker, "01_landed")
            dismiss_common_consents(page, broker)
            sleep(0.5)

            find_input(page, "tag:input@@id=name", "tag:input@@name=name").input(dataRow["Name"])
            find_input(page, "tag:input@@id=street", "tag:input@@name=street").input(dataRow.get("Address", ""))
            find_input(page, "tag:input@@id=city", "tag:input@@name=city").input(dataRow.get("City", ""))
            safe_select(page, "tag:select@@id=state", dataRow.get("State", ""))
            find_input(page, "tag:input@@id=zip", "tag:input@@name=zip").input(str(dataRow.get("Zipcode", "")))
            find_input(page, "tag:input@@id=email", "tag:input@@name=email").input(generate_email(dataRow["Name"]))
            phone = dataRow.get("Phone Number", "")
            if phone:
                find_input(page, "tag:input@@id=phone", "tag:input@@name=phone").input(phone)

            log_step(broker, "form filled")
            screenshot_step(page, broker, "02_filled")

            find_button(
                page,
                "tag:button@@text()=Submit Opt-Out Request",
                "tag:button@@type=submit",
            ).click()
            log_step(broker, "submitted")
            sleep(4)
            screenshot_step(page, broker, "03_submitted")

            try:
                page.get_screenshot(screenshot_save_path)
            except Exception:
                pass
    except Exception as e:
        log_step(broker, f"OUTER FAILURE: {e}")

    return screenshot_save_path
