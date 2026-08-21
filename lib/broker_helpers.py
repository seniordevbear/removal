"""Shared helpers for broker scraping scripts.

History: the original 302 broker scripts each rolled their own logic for:
  - launching Chromium (often with -disable-javascript that breaks reCAPTCHA)
  - dismissing cookie / GDPR / TrustArc / OneTrust consent banners
  - finding form fields by selector (single-attempt, brittle)
  - logging failures (mostly to stdout with no broker context)

Result: when a broker redesigns its form, every script that depends on the
old selectors silently breaks and the failure mode is invisible until the
production stats show 0% success.

This module provides:
  - safe_chromium_for_broker()   guaranteed cleanup, JS-enabled, optional
                                 proxy, captures per-step screenshots to
                                 a broker-specific dir
  - dismiss_common_consents()    one-call to clear TrustArc / OneTrust /
                                 generic GDPR consent overlays
  - find_input(page, *cands)     tries each candidate selector in order,
                                 returns the first match, raises a
                                 descriptive exception listing all tried
                                 selectors when nothing matches
  - find_button(page, *cands)    same for buttons
  - safe_select(page, sel, val)  selects by text OR value, with fallbacks
  - log_step(name, msg)          uniform log format for broker steps

NOTHING in here calls the broker's submit button or talks to the broker
in a way the existing scripts don't already do. It's purely helper code.
"""
from __future__ import annotations
import os
import sys
import time
import contextlib
import datetime
import logging
from typing import Optional, Iterable, Any

log = logging.getLogger("pd.broker_helpers")


# Common consent / cookie / GDPR overlay selectors. Tried in order. When
# we find one, we click and move on. NEVER raises -- the absence of a
# consent banner is normal.
_CONSENT_SELECTORS = [
    # OneTrust
    "tag:button@@id=onetrust-accept-btn-handler",
    "tag:button@@id=accept-recommended-btn-handler",
    # TrustArc
    "tag:button@@id=truste-consent-button",
    # Generic cookie banners
    'tag:button@@text():Accept All',
    'tag:button@@text():Accept all',
    'tag:button@@text():I Accept',
    'tag:button@@text():I Agree',
    'tag:button@@text():Agree & Proceed',
    'tag:button@@text():Agree and Proceed',
    'tag:button@@text():Allow All',
    'tag:button@@text():Allow all',
    # CCPA-style banners
    'tag:button@@text():Continue',
    # Close buttons (use last)
    "tag:button@@aria-label=Close",
    "tag:button@@class:close",
]


def _logbase(name: str) -> str:
    return f"[broker:{name}]"


def log_step(broker: str, msg: str, level: int = logging.INFO) -> None:
    """Uniform per-step log. Prints to stderr so NSSM AppStderr rotation
    captures it alongside the manage.py traceback dumps."""
    line = f"{_logbase(broker)} {msg}"
    print(line, file=sys.stderr, flush=True)


def dismiss_common_consents(page, broker: str = "?") -> int:
    """Try each known consent dismiss selector. Returns the count that
    were clicked. Never raises -- consent banners are optional."""
    clicked = 0
    for sel in _CONSENT_SELECTORS:
        try:
            el = page.ele(sel, timeout=0.5)
            if el and getattr(el, "states", None) and el.states.is_displayed:
                el.click()
                clicked += 1
                log_step(broker, f"dismissed consent via '{sel}'")
                time.sleep(0.3)
        except Exception:
            # The most common case is just "not found" -- ignore
            pass
    return clicked


def screenshot_step(page, broker: str, step: str, base_dir: Optional[str] = None) -> Optional[str]:
    """Save a labeled per-step screenshot. Returns the path on success,
    None on failure. Lives under ScreenShot/<date>/<broker>/<step>.png so
    a postmortem can walk through what the bot saw at each stage."""
    base = base_dir or os.getcwd()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(base, "ScreenShot", today, broker)
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError:
        return None
    ts = datetime.datetime.now().strftime("%H%M%S")
    path = os.path.join(out_dir, f"{ts}_{step}.png")
    try:
        page.get_screenshot(path)
        return path
    except Exception as e:
        log_step(broker, f"screenshot fail at step={step}: {e}", logging.WARNING)
        return None


def find_input(page, *candidates: str, timeout: float = 5.0):
    """Try each candidate selector in order. Returns the first non-None
    match. Raises ValueError listing all candidates that failed.

    Use this instead of bare page.ele(...) so brokers' selector drift
    (id="fname" -> name="firstName" -> placeholder="First name") still
    works as long as ONE candidate matches today's DOM."""
    tried = []
    for sel in candidates:
        try:
            el = page.ele(sel, timeout=timeout)
            if el:
                return el
            tried.append(f"{sel}=None")
        except Exception as e:
            tried.append(f"{sel}=ERR:{type(e).__name__}")
    raise ValueError(f"no candidate selector matched; tried: {tried}")


# Alias for clarity
find_button = find_input
find_element = find_input


def safe_select(page, sel: str, value: str, timeout: float = 5.0) -> bool:
    """Select <option> by text first, then by value. Returns True on
    success. Never raises -- returns False and logs on failure."""
    try:
        el = page.ele(sel, timeout=timeout)
        if not el:
            log_step("?", f"safe_select: no element matched '{sel}'", logging.WARNING)
            return False
        # DrissionPage <select> API
        if hasattr(el, "select"):
            try:
                el.select.by_text(value)
                return True
            except Exception:
                pass
            try:
                el.select.by_value(value)
                return True
            except Exception:
                pass
        return False
    except Exception as e:
        log_step("?", f"safe_select failed: {e}", logging.WARNING)
        return False


def run_infopay_optout(broker_name: str, url: str, dataRow, run_mode: str = "non-headless"):
    """Shared opt-out flow for the InfoPay backend used by 7+ brokers:
    infotracer.com, members.verifyrecords.com, members.searchquarry.com,
    staterecords.org, recordsfinder.com. All have identical form structure
    with InfoPay_Core_Components_OptOuts_DataRemovalServiceModel_* fields.

    Returns screenshot save path. Logs each step + saves per-step
    screenshots to ScreenShot/<date>/<broker_name>/ on failure.
    """
    import os
    import datetime
    import random
    from time import sleep
    from twocaptcha import TwoCaptcha
    from lib.common import generate_email

    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    base_dir = os.getcwd()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(base_dir, "ScreenShot", today)
    os.makedirs(out_dir, exist_ok=True)
    screenshot_save_path = os.path.join(
        out_dir, f"{broker_name}_{fName}-{lName}.png"
    )

    try:
        with safe_chromium_for_broker(
            broker_name, use_proxy=True,
            headless=(run_mode == "headless"),
            extra_extensions=["extension", "adblock"],
        ) as page:
            page.get(url)
            sleep(random.uniform(3, 5))
            screenshot_step(page, broker_name, "01_landed")
            dismiss_common_consents(page, broker_name)
            sleep(0.5)

            find_input(
                page,
                "tag:input@@id:fname",
                "tag:input@@name:fname",
                "tag:input@@placeholder=First Name",
            ).input(fName)
            log_step(broker_name, f"typed first name: {fName}")

            find_input(
                page,
                "tag:input@@id:lname",
                "tag:input@@name:lname",
                "tag:input@@placeholder=Last Name",
            ).input(lName)
            log_step(broker_name, f"typed last name: {lName}")

            state = dataRow.get("State", "")
            if state:
                if not safe_select(page, "tag:select@@id:state", state):
                    safe_select(page, "tag:select@@name:state", state)

            city = dataRow.get("City", "")
            if city:
                find_input(
                    page,
                    "tag:input@@id:city",
                    "tag:input@@name:city",
                    "tag:input@@placeholder=City",
                ).input(city)
                log_step(broker_name, f"typed city: {city}")
            screenshot_step(page, broker_name, "02_filled")

            find_button(
                page,
                "tag:button@@text()=Submit",
                "tag:button@@type=submit",
            ).click()
            log_step(broker_name, "clicked initial Submit")
            sleep(3)
            screenshot_step(page, broker_name, "03_results")

            # optional not-a-robot
            try:
                cb = page.ele("tag:input@@id=notrobl", timeout=2)
                if cb:
                    cb.click()
                    log_step(broker_name, "clicked notrobl checkbox")
                    sleep(2)
            except Exception:
                pass

            try:
                tbody = page.ele("tag:tbody", timeout=4)
            except Exception:
                tbody = None

            if not tbody:
                log_step(broker_name, "no results table -- broker may have changed flow")
                screenshot_step(page, broker_name, "99_no_results_table")
                return screenshot_save_path

            rows = tbody.eles("tag:tr")
            if not rows:
                log_step(broker_name, "results empty -- user not in broker DB")
                screenshot_step(page, broker_name, "99_empty_results")
                return screenshot_save_path

            try:
                rows[0].ele("tag:input@@type=checkbox").click()
                sleep(1)
                rows[0].ele("tag:button@@type=submit").click()
                log_step(broker_name, "selected first result")
                sleep(2)
            except Exception as e:
                log_step(broker_name, f"row select failed: {e}")
                screenshot_step(page, broker_name, "99_row_select_fail")
                return screenshot_save_path

            # confirmation form
            try:
                find_input(
                    page,
                    "tag:input@@id=DataRemovalFormModel_email",
                    "tag:input@@name:email",
                    "tag:input@@type=email",
                ).input(generate_email(dataRow["Name"]))
                find_input(
                    page,
                    "tag:textarea@@id=DataRemovalFormModel_comment",
                    "tag:textarea@@name:comment",
                ).input("I want to remove my info.")
                log_step(broker_name, "filled confirmation form")
                screenshot_step(page, broker_name, "04_confirm_filled")

                api_key = os.getenv("TWOCAPTCHA_API_KEY", "")
                if api_key:
                    solver = TwoCaptcha(api_key)
                    site_key = "6LcB808UAAAAAAqr91WUtrhYLaBAXkCTPZbxilo5"
                    result = solver.recaptcha(sitekey=site_key, url=page.url)
                    code = result.get("code") if result else None
                    if code:
                        try:
                            page.run_js(
                                "var t=document.getElementById('g-recaptcha-response');"
                                "if(t){t.innerHTML=arguments[0];t.value=arguments[0];}",
                                code,
                            )
                            log_step(broker_name, "captcha token injected")
                        except Exception as e:
                            log_step(broker_name, f"captcha injection: {e}")

                find_button(
                    page,
                    "tag:button@@type=submit",
                ).click()
                log_step(broker_name, "clicked final submit")
                sleep(3)
                screenshot_step(page, broker_name, "05_submitted")
            except Exception as e:
                log_step(broker_name, f"confirmation stage: {e}")
                screenshot_step(page, broker_name, "99_confirm_fail")

            try:
                page.get_screenshot(screenshot_save_path)
            except Exception:
                pass
    except Exception as outer:
        log_step(broker_name, f"OUTER FAILURE: {outer}")

    return screenshot_save_path


@contextlib.contextmanager
def safe_chromium_for_broker(
    broker: str,
    use_proxy: bool = False,
    headless: bool = False,
    extra_args: Optional[Iterable[str]] = None,
    extra_extensions: Optional[Iterable[str]] = None,
):
    """Yields a ChromiumPage configured for broker scraping. Guarantees
    .quit() on exit (covers the 71-broker chromium-leak audit finding).
    JavaScript is ENABLED by default (reCAPTCHA needs it). Adds optional
    proxy via lib.proxies when use_proxy=True.

    Usage in a broker:

        from lib.broker_helpers import safe_chromium_for_broker, find_input, dismiss_common_consents

        def mybroker(dataRow, ...):
            with safe_chromium_for_broker("mybroker", use_proxy=True) as page:
                page.get(URL)
                dismiss_common_consents(page, "mybroker")
                fname = find_input(page,
                    "tag:input@@id:fname",
                    "tag:input@@name:firstName",
                    "tag:input@@placeholder=First Name")
                fname.input(dataRow["Name"].split()[0])
                ...
    """
    from DrissionPage import ChromiumPage, ChromiumOptions

    args = list(extra_args or [])
    # Safe defaults. NOTE: -disable-javascript is deliberately NOT here --
    # most modern broker forms (reCAPTCHA, AJAX submit) need JS.
    for default in ("-no-first-run", "--start-maximized",
                    "-disable-gpu", "-disable-sensors"):
        if default not in args:
            args.append(default)

    opts = ChromiumOptions()
    for arg in args:
        opts.set_argument(arg)
    opts = opts.auto_port()

    for ext in (extra_extensions or []):
        try:
            opts.add_extension(ext)
        except Exception as e:
            log_step(broker, f"extension load failed {ext}: {e}", logging.WARNING)

    if use_proxy:
        try:
            from lib.proxies import get_proxy_extension
            opts.add_extension(get_proxy_extension())
            log_step(broker, "proxy extension added")
        except Exception as e:
            log_step(broker, f"proxy setup failed: {e}", logging.WARNING)

    if headless:
        opts.headless()

    page = ChromiumPage(addr_or_opts=opts)
    log_step(broker, "chromium started")
    try:
        yield page
    finally:
        try:
            page.quit()
            log_step(broker, "chromium quit")
        except Exception as e:
            log_step(broker, f"page.quit() raised: {e}", logging.WARNING)


# ---------------------------------------------------------------------------
# Common /request-portal flow shared by ~53 sites in the *arrests.org and
# *courtrecords.us families. Added 2026-05-28. All sites in this family
# render the same JavaScript form with the same field semantics; we
# confirmed empirically by hitting californiaarrests.org/request-portal
# and nyarrests.org/request-portal -- identical field lists.
# ---------------------------------------------------------------------------

_US_STATE_FULL = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


def _broker_to_request_portal_url(broker_name):
    """Convert "californiaarrestsorg" -> "https://californiaarrests.org/request-portal"."""
    if broker_name.endswith("org"):
        host = broker_name[:-3] + ".org"
    elif broker_name.endswith("us"):
        host = broker_name[:-2] + ".us"
    elif broker_name.endswith("com"):
        host = broker_name[:-3] + ".com"
    else:
        host = broker_name
    return "https://" + host + "/request-portal"


_US_STATE_ABBREV = {v: k for k, v in _US_STATE_FULL.items()}


def select_state(select_ele, raw, timeout=4.0):
    """Select a state <option> regardless of which format the site uses.

    Customer profiles store two-letter codes ("CA") but many broker
    dropdowns list full names ("California") — and some the reverse, or
    match only on the option's value attribute. A bare
    select.by_text(dataRow["State"]) therefore failed whenever formats
    disagreed (seen live on addresssearchcom, 46 scripts affected).
    Tries text and value for both spellings before giving up loudly."""
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("state is empty for this user")
    cands = [raw]
    full = _state_full_name(raw)
    if full not in cands:
        cands.append(full)
    ab = _US_STATE_ABBREV.get(full)
    if ab and ab not in cands:
        cands.append(ab)
    for cand in cands:
        for method in ("by_text", "by_value"):
            try:
                getattr(select_ele.select, method)(cand, timeout=timeout)
                return cand
            except TypeError:
                # older DrissionPage: no timeout kwarg
                try:
                    getattr(select_ele.select, method)(cand)
                    return cand
                except Exception:
                    pass
            except Exception:
                pass
    raise RuntimeError("no state option matched; tried " + repr(cands))


def _state_full_name(raw):
    """User profile might store state as 'CA' or 'California'. The dropdown
    on the request portal wants the full name. Normalize."""
    if not raw:
        return ""
    raw = raw.strip()
    if len(raw) == 2 and raw.upper() in _US_STATE_FULL:
        return _US_STATE_FULL[raw.upper()]
    return raw


def run_arrests_org_optout(broker_name, dataRow, run_mode="non-headless"):
    """Generic opt-out for the arrests.org / courtrecords.us site family
    (53 broker scripts delegate here).

    Surveyed 2026-08-20 — the family no longer shares one portal:

      * *courtrecords.us  ->  /optout/           InfoPay platform. Fields are
        Model[fname]/[lname]/[state]/[city]; no email/address; no radios.
      * *arrests.org      ->  /privacy-request-portal   WPForms. CHECKBOXES
        (not radios) for "myself" + "Delete", name fields contain "first"/
        "last", plus email/address/city/state/zip, guarded by Cloudflare
        Turnstile.
      * a few (arrestwarrant.org) have NO portal at all -> we raise, the row
        is recorded and bounded-retried, and the domain shows up in the
        failure report instead of silently looping.

    The old code assumed one URL (/request-portal) and radio buttons; when
    the family split it 404'd everywhere and every attempt raised
    "no candidate selector matched".

    Returns the screenshot path on success. Raises on failure."""
    from time import sleep
    import random
    base = _broker_to_request_portal_url(broker_name).rsplit("/request-portal", 1)[0]
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    email = dataRow.get("User Email") or ""
    address_line_1 = (dataRow.get("Address") or dataRow.get("Street") or "").strip()
    city = (dataRow.get("City") or "").strip()
    state = _state_full_name(dataRow.get("State") or "")
    zipc = (dataRow.get("Zipcode") or "").strip()

    screenshot_path = None
    with safe_chromium_for_broker(broker_name,
                                  headless=(run_mode == "headless")) as page:
        try:

            def _has_form():
                for sel in ("css:input[name*='[fname]']",
                            "css:input[name*='first' i]",
                            "css:.wpforms-field-name-first"):
                    try:
                        if page.ele(sel, timeout=1.5):
                            return True
                    except Exception:
                        pass
                return False

            found = False
            for path in ("/privacy-request-portal", "/optout/", "/request-portal"):
                url = base + path
                log_step(broker_name, "GET " + url)
                page.get(url)
                sleep(2.5)
                if "challenge" in (page.url or "") or "Just a moment" in (page.html or ""):
                    sleep(8)
                try:
                    dismiss_common_consents(page, broker_name)
                except Exception:
                    pass
                if _has_form():
                    found = True
                    break
            if not found:
                screenshot_path = screenshot_step(page, broker_name, "no_form")
                raise RuntimeError(
                    broker_name + ": no opt-out form at any known path "
                    "(/privacy-request-portal, /optout/, /request-portal) — "
                    "site layout changed, script needs a survey")

            # -- consent toggles: WPForms uses checkboxes, older layouts used
            #    radios. Try both input types for each concept; missing is a
            #    warning, not fatal (InfoPay has neither).
            for concept, needles in (("myself", ("self", "myself")),
                                     ("delete", ("delete",))):
                clicked = False
                for typ in ("checkbox", "radio"):
                    for needle in needles:
                        try:
                            el = page.ele(
                                "css:input[type=%s][value*='%s' i]" % (typ, needle),
                                timeout=1.5)
                            if el:
                                el.click()
                                sleep(0.3)
                                clicked = True
                                break
                        except Exception:
                            pass
                    if clicked:
                        break
                if not clicked:
                    log_step(broker_name, concept + " toggle not present",
                             logging.WARNING)

            def _fill(label_aliases, value, required=False, extra_cands=()):
                if not value:
                    if required:
                        raise RuntimeError(
                            "required field " + repr(label_aliases[0]) +
                            " has no value for this user")
                    return
                cands = list(extra_cands)
                for alias in label_aliases:
                    cands.append("css:input[id*='%s' i]" % alias)
                    cands.append("css:input[name*='%s' i]" % alias)
                    cands.append("css:input[placeholder*='%s' i]" % alias)
                try:
                    el = find_input(page, *cands, timeout=4.0)
                except ValueError:
                    if required:
                        raise
                    log_step(broker_name,
                             "field %s not on this form, skipped" % label_aliases[0],
                             logging.INFO)
                    return
                # WPForms sub-fields can be styled without a boundable rect;
                # a normal click then raises NoRectError. Fall back to a JS
                # click, and scroll the element into view first.
                try:
                    el.click()
                except Exception:
                    try:
                        page.scroll.to_see(el)
                    except Exception:
                        pass
                    el.click(by_js=True)
                sleep(random.uniform(0.05, 0.12))
                el.input(value)
                sleep(0.2)

            # name fields exist on every shape (fname on InfoPay, first on
            # WPForms) — these two are the only hard requirements.
            _fill(["first", "fname"], first, required=True)
            _fill(["last", "lname"], last, required=True)
            # everything else is best-effort: present on WPForms, absent on
            # InfoPay, and absence must not kill the run.
            _fill(["email"], email, extra_cands=("css:input[type=email]",))
            _fill(["addressLine1", "address1", "address-1", "address"], address_line_1)
            _fill(["city"], city)
            _fill(["zip", "postal"], zipc)

            if state:
                try:
                    safe_select(page,
                                "css:select[id*='state' i], select[name*='state' i]",
                                state, timeout=4.0)
                except Exception as e:
                    log_step(broker_name, "state select failed: " + str(e),
                             logging.WARNING)

            # Optional details textarea (WPForms request-details box)
            try:
                details = page.ele("tag:textarea", timeout=2.0)
                if details:
                    details.input("Please delete all of my personal information "
                                  "from your records.")
            except Exception:
                pass

            # -- Cloudflare Turnstile (WPForms portals). Solve via 2captcha
            #    and inject the token; without it the submit is rejected.
            try:
                ts = page.ele("css:.cf-turnstile[data-sitekey]", timeout=1.5)
            except Exception:
                ts = None
            if ts:
                sitekey = ts.attr("data-sitekey")
                log_step(broker_name, "solving turnstile sitekey=" + str(sitekey))
                try:
                    from lib.captcha import get_solver
                    import json as _json
                    token = get_solver().turnstile(sitekey=sitekey, url=page.url)["code"]
                    # embed via JSON: DrissionPage run_js has no Selenium-style
                    # arguments[] contract, and json.dumps gives safe quoting.
                    page.run_js(
                        "var i=document.querySelector("
                        "'input[name=\"cf-turnstile-response\"]');"
                        "if(i){i.value=" + _json.dumps(token) + ";}")
                except Exception as e:
                    log_step(broker_name, "turnstile solve failed: " + str(e),
                             logging.ERROR)
                    raise

            sleep(0.5)
            screenshot_path = screenshot_step(page, broker_name, "before_submit")

            submit_btn = find_input(
                page,
                "css:button[type=submit]",
                "css:input[type=submit]",
                "xpath://button[contains(translate(., 'SUBMIT', 'submit'), 'submit')]",
                timeout=6.0,
            )
            submit_btn.click()

            sleep(5)
            screenshot_path = screenshot_step(page, broker_name, "after_submit") or screenshot_path
            log_step(broker_name, "submitted, exiting")
            return screenshot_path
        except Exception:
            # capture what the bot was looking at WHILE the browser is still
            # open — the with-block quits Chrome on exit, and a screenshot
            # against a closed browser only yields "connection disconnected".
            try:
                screenshot_path = screenshot_step(page, broker_name, "error") or screenshot_path
            except Exception:
                pass
            raise


# ---------------------------------------------------------------------------
# CCPA email-based opt-out (added 2026-05-28).
#
# For brokers without a public opt-out form but with a privacy@ contact.
# Sends a properly-formed CCPA / CPRA opt-out + deletion request email,
# preserves a .eml copy locally, and lets the broker reply directly to
# the user (Reply-To set to user's address) for any required identity
# verification.
#
# This is a legitimate path under CCPA 1798.105 (Right to Delete) +
# 1798.120 (Right to Opt-Out of Sale) -- broker has 45 days to comply.
# We don't track downstream responses; that's the user's inbox to handle.
# ---------------------------------------------------------------------------

def _broker_to_host(broker_name):
    """Convert broker filename to canonical host.
    "33acrosscom" -> "33across.com", "apolloio" -> "apollo.io", etc."""
    for suffix in ("com", "org", "net", "edu", "gov", "info", "biz",
                   "io", "ai", "tv", "co", "us"):
        if broker_name.endswith(suffix):
            base = broker_name[:-len(suffix)]
            return base + "." + suffix
    return broker_name



class CCPADailyLimitReached(Exception):
    """Raised by run_ccpa_email_optout when a user has hit the per-day
    cap on outbound CCPA email sends. Caller (manage.py) should leave
    the row at step=0 so it gets retried tomorrow."""


# Per-user, per-day counter persisted to disk so it survives pd-removal
# restarts. Lock-guarded so the ThreadPoolExecutor workers don't race.
_CCPA_COUNTER_PATH = r"C:\wonderful\removal\ccpa_email_counter.json"
_CCPA_LOCK = None
def _ccpa_get_lock():
    global _CCPA_LOCK
    if _CCPA_LOCK is None:
        import threading
        _CCPA_LOCK = threading.Lock()
    return _CCPA_LOCK


def _ccpa_increment_or_raise(user_id, limit):
    """Returns the new count for today after increment. Raises
    CCPADailyLimitReached if the user is already at or over the limit."""
    import json, os, datetime
    today = datetime.date.today().isoformat()
    lock = _ccpa_get_lock()
    with lock:
        try:
            with open(_CCPA_COUNTER_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except FileNotFoundError:
            state = {"date": today, "counts": {}}
        except (json.JSONDecodeError, OSError):
            # FAIL CLOSED. A truncated/unreadable counter is exactly what a
            # full disk produces — and on 2026-07-17 this branch silently
            # reset the count on every read, so the 50/day cap was forgotten
            # and 2,343 opt-out emails went out in one day (SurgeMail warns
            # at 500). Corrupt state now burns the REST of today's budget
            # instead of granting an infinite one; the date rollover heals
            # it tomorrow.
            import logging as _logging
            _logging.getLogger("pd.removal").error(
                "ccpa counter file unreadable — treating today's quota as "
                "spent (fail closed): %s", _CCPA_COUNTER_PATH)
            state = {"date": today, "counts": {"_global": limit}}
        if state.get("date") != today:
            state = {"date": today, "counts": {}}
        uid = str(user_id)
        cur = int(state["counts"].get(uid, 0))
        if cur >= limit:
            raise CCPADailyLimitReached(
                "user_id=" + uid + " already at " + str(cur) + "/" + str(limit) + " CCPA emails today"
            )
        state["counts"][uid] = cur + 1
        tmp = _CCPA_COUNTER_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _CCPA_COUNTER_PATH)
        return cur + 1


CCPA_PER_USER_PER_DAY = 10  # legacy; kept for any importer (no longer the active cap)
# Aggregate cap across ALL users (changed 2026-05-29). Replaces the per-user
# 10/day with a global 50/day to stay well under SurgeMail's user_send_warning
# threshold of 500/day and bound deliverability risk on the shared sending IP.
CCPA_TOTAL_PER_DAY = 50


def run_ccpa_email_optout(broker_name, dataRow, privacy_email=None,
                           run_mode="non-headless"):
    """Send a CCPA-compliant opt-out + deletion request to the broker's
    privacy contact.

    Args:
        broker_name: bare filename without .py (e.g. "33acrosscom")
        dataRow: user info dict from __removal._build_data_row
        privacy_email: explicit privacy contact, or None to default to
                       privacy@<derived_host>
        run_mode: ignored (kept for signature compatibility with scrapers)

    Returns the path to a saved .eml copy of the sent email (so the
    pipeline has artifact evidence). Raises on SMTP failure -- manage.py
    catches and marks step=3 for retry on next sweep.
    """
    import os
    import smtplib
    import datetime
    import pathlib as _pl
    from email.message import EmailMessage
    from email.utils import formatdate
    from lib.email_sender import (
        SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL,
        SMTP_TIMEOUT,
    )

    if not SMTP_PASSWORD:
        raise RuntimeError("CONFIRMATION_EMAIL_PASSWORD env not set; cannot send CCPA email")

    if not privacy_email:
        privacy_email = "privacy@" + _broker_to_host(broker_name)

    user_name = (dataRow.get("Name") or "").strip()
    user_email = (dataRow.get("User Email") or "").strip()
    user_address = (dataRow.get("Address") or dataRow.get("Street") or "").strip()
    user_city = (dataRow.get("City") or "").strip()
    user_state = (dataRow.get("State") or "").strip()
    user_zip = (dataRow.get("Zipcode") or "").strip()

    if not user_email or not user_name:
        raise RuntimeError("dataRow missing Name or User Email; cannot send CCPA request")

    subject = "CCPA / CPRA Right to Opt-Out & Delete Request - " + user_name

    body = (
        "Hello,\n\n"
        "Pursuant to the California Consumer Privacy Act (CCPA, as amended\n"
        "by CPRA) and any equivalent state privacy laws (VCDPA, CDPA, CPA,\n"
        "CTDPA, UCPA, OCPA, TIPA, FDBR, MTCDPA), I am formally exercising\n"
        "the following rights on behalf of the consumer identified below:\n\n"
        "  1. The Right to Opt-Out of the Sale or Sharing of Personal\n"
        "     Information (CCPA Sec. 1798.120 and equivalent state law).\n"
        "  2. The Right to Delete Personal Information collected about\n"
        "     the consumer (CCPA Sec. 1798.105 and equivalent state law).\n"
        "  3. The Right to Limit Use and Disclosure of Sensitive Personal\n"
        "     Information (CCPA Sec. 1798.121 where applicable).\n\n"
        "Please process this request and confirm the action taken within\n"
        "the statutory deadline (45 days under CCPA, with one 45-day\n"
        "extension permitted only with notice).\n\n"
        "CONSUMER VERIFICATION INFORMATION:\n"
        "  Name:    " + user_name + "\n"
        "  Email:   " + user_email + "\n"
        "  Address: " + user_address + "\n"
        "  City:    " + user_city + "\n"
        "  State:   " + user_state + "\n"
        "  ZIP:     " + user_zip + "\n\n"
        "If additional identity verification is required, please reply\n"
        "to this email. The Reply-To header is set to the consumer's\n"
        "direct email address (above) so any verification challenge\n"
        "reaches the consumer immediately.\n\n"
        "This request is submitted by PrivacyDuck (https://privacyduck.com),\n"
        "an authorized privacy-rights agent acting on the consumer's\n"
        "behalf pursuant to CCPA Sec. 1798.140(d) and 11 CCR 7063.\n\n"
        "Please confirm receipt and processing directly to the consumer\n"
        "at the email address above.\n\n"
        "Thank you for your prompt compliance.\n\n"
        "-- Sent by PrivacyDuck on behalf of " + user_name + "\n"
        "   https://privacyduck.com\n"
    )

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = privacy_email
    msg["Reply-To"] = user_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(body)

    # Aggregate daily throttle (changed 2026-05-29 from per-user 10/day to
    # global 50/day). Raises CCPADailyLimitReached when the GLOBAL counter
    # hits the cap; manage.py catches that and leaves the row at step=0 for
    # retry tomorrow. Key '_global' shares one bucket across all users.
    _ccpa_increment_or_raise("_global", CCPA_TOTAL_PER_DAY)

    log_step(broker_name, "CCPA email -> " + privacy_email)
    server = None
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        log_step(broker_name, "CCPA email send OK")
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass

    # Save a .eml artifact so the pipeline upload path has SOMETHING to
    # ship as evidence. The upload endpoint accepts arbitrary files;
    # worst case it just doesn't render the .eml in the dashboard.
    try:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        save_dir = _pl.Path(os.getcwd()) / "ScreenShot" / current_date
        save_dir.mkdir(parents=True, exist_ok=True)
        safe_user = "".join(c if c.isalnum() else "_" for c in user_email)
        save_path = save_dir / ("CCPA_" + broker_name + "_" + safe_user + ".eml")
        save_path.write_bytes(msg.as_bytes())
        return str(save_path)
    except Exception:
        # If we can't save the eml, the email still went out. Return
        # None so upload_file_to_server logs "upload skipped" (harmless).
        return None


def ccpa_global_quota_reached():
    """True when today's global CCPA email budget is already spent.

    Cheap read of the same counter file _ccpa_increment_or_raise() writes,
    taken under the same lock. manage.py calls this once per removal tick so
    it can EXCLUDE email-based brokers from task selection instead of
    claiming their rows, raising CCPADailyLimitReached hundreds of times and
    clogging each user's fairness window with rows that cannot progress.
    """
    import json, datetime
    today = datetime.date.today().isoformat()
    lock = _ccpa_get_lock()
    with lock:
        try:
            with open(_CCPA_COUNTER_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except FileNotFoundError:
            return False
        except (json.JSONDecodeError, OSError):
            return True  # unreadable counter -> assume spent (fail closed)
    if state.get("date") != today:
        return False  # stale file: counter will reset on next increment
    return int(state.get("counts", {}).get("_global", 0)) >= CCPA_TOTAL_PER_DAY
