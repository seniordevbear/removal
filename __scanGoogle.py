# __scanGoogle.py — orchestration entry for kind=3 (Google search scan).
# Mirrors __scan.py, but imports from sites_scan_google.
import importlib
import sys
import traceback


class ModuleMissing(Exception):
    pass


def _build_data_row(email, firstname, lastname, city, zip, state, age):
    name_full = "{} {}".format((firstname or "").strip(), (lastname or "").strip()).strip()
    return {
        "Verification Email": "webremovals@privacypros.com",
        "User Email": email or "",
        "Title": "Ms.",
        "Name": name_full,
        "Age": age if age else "",
        "Birth Day": "", "Birth Month": "", "Birth Year": "",
        "Address": "", "Area Code": "", "Phone Number": "",
        "Street": "", "Apartment": "",
        "City": city or "", "State": state or "", "Zipcode": zip or "",
        "County": "", "Advertising Id": "", "Job Title": "",
        "Business Name": "", "LinkedIn Profile": "", "Status": "",
    }


def _import_module(target_domain):
    module_name = "sites_scan_google." + target_domain
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        if getattr(e, "name", None) == module_name:
            raise ModuleMissing(target_domain) from e
        raise


def google_scan(sio, target_domain, req_id, user_id, email, firstname,
                lastname, city, zip, state, age):
    data_row = _build_data_row(email, firstname, lastname, city, zip, state, age)
    try:
        module = _import_module(target_domain)
    except ModuleMissing:
        print(
            "[GOOGLE_SCAN_MODULE_MISSING] req_id={} user_id={} domain={}".format(
                req_id, user_id, target_domain
            ),
            file=sys.stderr,
            flush=True,
        )
        raise
    fn = getattr(module, target_domain, None)
    if not callable(fn):
        raise AttributeError(
            "sites_scan_google.{}: no callable named '{}'".format(target_domain, target_domain)
        )
    try:
        return fn(data_row, "website", data_row["User Email"], run_mode="non-headless")
    except ModuleNotFoundError as e:
        if str(e).startswith("sites_scan_google."):
            print(
                "[GOOGLE_SCAN_MODULE_MISSING_INVOKE] req_id={} user_id={} domain={}".format(
                    req_id, user_id, target_domain
                ),
                file=sys.stderr,
                flush=True,
            )
            raise ModuleMissing(target_domain) from e
        raise
    except Exception:
        print(
            "[GOOGLE_SCAN_BROKER_RAISED] req_id={} user_id={} domain={}".format(
                req_id, user_id, target_domain
            ),
            file=sys.stderr,
        )
        traceback.print_exc()
        raise
