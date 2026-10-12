"""Crunchbase — DataGrail privacy request centre (written 2026-10-12).

New broker from the gap list. preferences.crunchbase.com/form/opt_out is a
DataGrail form: first name, last name, e-mail, the requester's relationship
to the data subject, and two free-text fields for the profile URL and the
information concerned.
"""
import random
from time import sleep

from lib.broker_helpers import (
    safe_chromium_for_broker, screenshot_step, log_step, dismiss_common_consents,
    fill_field, click_safe, submission_verdict, missing_pii,
)
from lib.common import generate_email

URL = "https://preferences.crunchbase.com/form/opt_out"


def crunchbasecom(dataRow, website_name, in_user_email, run_mode):
    broker = "crunchbasecom"
    name = (dataRow.get("Name") or "").strip()
    email = (dataRow.get("User Email") or "").strip()
    if not name:
        raise RuntimeError(broker + ": no name on this profile")
    if not email:
        raise missing_pii("User Email")
    first, last = name.split()[0], name.split()[-1]

    with safe_chromium_for_broker(broker, headless=(run_mode == "headless")) as page:
        page.get(URL)
        sleep(5)
        try:
            dismiss_common_consents(page, broker)
        except Exception:
            pass

        fill_field(page, "tag:input@@name=first_name", first, timeout=12, broker=broker)
        fill_field(page, "tag:input@@name=last_name", last, broker=broker)
        fill_field(page, "tag:input@@name=email_address", email, broker=broker)

        # "Data subject's relationship" — I am the data subject.
        rel = page.ele("tag:input@@name=data_subject_relationship", timeout=4)
        if rel:
            try:
                rel.click()
                sleep(1)
                opt = page.ele("xpath://*[@role='option'][contains(translate(.,'MYSELF','myself'),'myself')]", timeout=3) \
                    or page.ele("xpath://li[contains(translate(.,'MYSELF','myself'),'myself')]", timeout=2)
                if opt:
                    opt.click()
            except Exception as e:
                log_step(broker, "relationship picker: %s" % e)

        fill_field(page, "tag:textarea@@name=additional_info",
                   "Please delete my personal information and do not sell or share it.",
                   required=False, broker=broker)
        profile = (dataRow.get("Profile URL") or "").strip()
        if profile:
            fill_field(page, "css:input[aria-label^='Please link the URL']", profile,
                       required=False, broker=broker)

        screenshot_step(page, broker, "before_submit")
        click_safe(page, "css:form button[type=submit]", broker=broker)
        sleep(4)
        submission_verdict(page, broker)
        return screenshot_step(page, broker, "after_submit")
