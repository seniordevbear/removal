from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import datetime
import time
import os
import random
import shutil
from urllib.parse import quote
from urllib.parse import urljoin
from urllib.request import urlretrieve
from urllib.error import HTTPError, URLError


def get_chromium_options(arguments: list) -> ChromiumOptions:
    options = ChromiumOptions()
    for argument in arguments:
        options.set_argument(argument)
    return options


def _human_pause(min_s: float = 0.06, max_s: float = 0.20) -> None:
    sleep(random.uniform(min_s, max_s))


def _human_settle(page: ChromiumPage) -> None:
    # Lightly mimic reading/settling behavior and trigger lazy-loaded sections.
    try:
        page.scroll.to_see('tag:body')
    except Exception:
        pass
    _human_pause(0.08, 0.24)


def _human_after_action(page: ChromiumPage) -> None:
    _human_pause(0.08, 0.28)
    try:
        page.scroll.down(random.randint(120, 360))
        _human_pause(0.05, 0.18)
        page.scroll.up(random.randint(80, 220))
    except Exception:
        pass
    _human_pause(0.06, 0.20)


def _find_first(page: ChromiumPage, selectors: list[str]):
    for sel in selectors:
        try:
            ele = page.ele(sel, timeout=1)
            if ele:
                return ele
        except Exception:
            continue
    return None


def _human_pause(min_s: float = 0.06, max_s: float = 0.20) -> None:
    sleep(random.uniform(min_s, max_s))


def _human_scroll(page: ChromiumPage) -> None:
    try:
        page.scroll.down(random.randint(200, 700))
    except Exception:
        pass
    _human_pause(0.15, 0.5)
    try:
        page.scroll.up(random.randint(80, 260))
    except Exception:
        pass
    _human_pause(0.15, 0.45)


def _click_with_retries(page: ChromiumPage, selectors: list[str], retries: int = 4, wait_after: float = 1.0) -> bool:
    for _ in range(retries):
        _human_scroll(page)
        if _click_if_found(page, selectors, wait_after=wait_after):
            return True
    return False


def _fill_with_retries(page: ChromiumPage, selectors: list[str], value: str, retries: int = 3) -> bool:
    for _ in range(retries):
        _human_pause(0.15, 0.45)
        if _fill_if_found(page, selectors, value):
            return True
    return False


def _ensure_checkbox_checked(page: ChromiumPage, selectors: list[str], retries: int = 4) -> bool:
    for _ in range(retries):
        ele = _find_first(page, selectors)
        if not ele:
            _human_pause(0.15, 0.4)
            continue
        try:
            checked = str(ele.attr('checked') or '').lower()
            if checked and checked != 'false':
                return True
        except Exception:
            pass
        try:
            ele.click()
            _human_pause(0.3, 0.8)
        except Exception:
            _human_pause(0.2, 0.5)
            continue
        try:
            checked = str(ele.attr('checked') or '').lower()
            if checked and checked != 'false':
                return True
        except Exception:
            # some custom checkbox UIs toggle underlying input asynchronously
            _human_pause(0.2, 0.5)
            return True
    return False


def _click_if_found(page: ChromiumPage, selectors: list[str], wait_after: float = 1.0) -> bool:
    ele = _find_first(page, selectors)
    if not ele:
        return False
    try:
        ele.click()
        sleep(wait_after)
        return True
    except Exception:
        return False


def _human_type_into_element(ele, value: str) -> None:
    for ch in str(value):
        ele.input(ch)
        sleep(random.uniform(0.02, 0.07))


def _fill_if_found(page: ChromiumPage, selectors: list[str], value: str) -> bool:
    if not value:
        return False
    ele = _find_first(page, selectors)
    if not ele:
        return False
    try:
        ele.clear()
    except Exception:
        pass
    try:
        ele.click()
        _human_type_into_element(ele, value)
        return True
    except Exception:
        return False


def _safe_pause(min_s: float = 0.08, max_s: float = 0.25) -> None:
    sleep(random.uniform(min_s, max_s))


def _check_if_found(page: ChromiumPage, selectors: list[str], wait_after: float = 0.5) -> bool:
    ele = _find_first(page, selectors)
    if not ele:
        return False
    try:
        # Best effort: some forms gate submit until consent checkboxes are ticked.
        if hasattr(ele, "states") and hasattr(ele.states, "is_checked") and ele.states.is_checked:
            return True
    except Exception:
        pass
    try:
        ele.click()
        sleep(wait_after)
        return True
    except Exception:
        return False


def _ensure_common_checkboxes(page: ChromiumPage) -> None:
    checkbox_selectors = [
        "tag:input@@type=checkbox",
        "tag:label@@text*=I agree",
        "tag:label@@text*=I accept",
        "tag:label@@text*=Terms",
        "tag:label@@text*=Privacy",
        "tag:button@@text()=I agree",
    ]
    # Try a few passes in case controls render lazily.
    for _ in range(2):
        _check_if_found(page, checkbox_selectors, wait_after=random.uniform(0.3, 0.7))
        _safe_pause(0.2, 0.5)


def _click_with_retries(
    page: ChromiumPage,
    selectors: list[str],
    tries: int = 3,
    retries: int | None = None,
    wait_after: float | None = None,
) -> bool:
    attempts = retries if retries is not None else tries
    pause_after = wait_after if wait_after is not None else random.uniform(1.0, 1.8)

    for i in range(attempts):
        _human_scroll(page)
        if _click_if_found(page, selectors, wait_after=pause_after):
            return True
        _safe_pause(0.4, 0.9)
        _ensure_common_checkboxes(page)
        print(f"[pimeyes-debug] click-retry={i + 1} selectors={selectors[:2]}")
    return False


def _upload_first_file_input(page: ChromiumPage, file_path: str) -> bool:
    if not file_path:
        return False
    file_inputs = page.eles("tag:input@@type=file") or []
    for inp in file_inputs:
        try:
            inp.input(file_path)
            return True
        except Exception:
            continue
    return False


def _accept_cookie_banner(page: ChromiumPage) -> None:
    _click_with_retries(
        page,
        [
            "tag:button@@text()=Accept all",
            "tag:button@@text()=Accept All",
            "tag:button@@text()=I agree",
            "tag:button@@text()=Allow all",
            "tag:button@@text()=Accept",
        ],
        wait_after=random.uniform(0.6, 1.0),
    )


def _write_login_debug(page: ChromiumPage, stage: str) -> tuple[str, str]:
    debug_dir = os.path.join(os.getcwd(), "ScreenShot", "debug")
    os.makedirs(debug_dir, exist_ok=True)
    ts = int(datetime.datetime.now().timestamp())
    safe_stage = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in stage)
    shot_path = os.path.join(debug_dir, f"pimeyes-login-{safe_stage}-{ts}.png")
    html_path = os.path.join(debug_dir, f"pimeyes-login-{safe_stage}-{ts}.html")

    try:
        page.get_screenshot(shot_path)
    except Exception:
        pass

    html = ""
    try:
        html = page.html or ""
    except Exception:
        html = ""

    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        pass

    current_url = ""
    try:
        current_url = page.url or ""
    except Exception:
        current_url = ""

    print(f"[pimeyes-debug] stage={stage} url={current_url}")
    print(f"[pimeyes-debug] screenshot={shot_path}")
    print(f"[pimeyes-debug] html={html_path}")
    return shot_path, html_path


def _login_pimeyes(page: ChromiumPage, email: str, password: str) -> None:
    print("[pimeyes-debug] stage=login:navigate:start")
    try:
        page.get("https://pimeyes.com/en/login", timeout=30)
    except Exception as e:
        print(f"[pimeyes-debug] stage=login:navigate:error error={e}")
        _write_login_debug(page, "login-navigate-error")
        raise

    print(f"[pimeyes-debug] stage=login:navigate:done url={page.url}")
    _human_settle(page)
    _accept_cookie_banner(page)
    _human_after_action(page)
    print("[pimeyes-debug] stage=login:cookie-checked")

    # PimEyes may show an entry CTA before actual login inputs are visible.
    _click_if_found(
        page,
        [
            "tag:a@@href*=login",
            "tag:a@@text()=Sign in",
            "tag:a@@text()=Log in",
            "tag:button@@text()=Sign in",
            "tag:button@@text()=Log in",
            "tag:button@@text()=Login",
        ],
        wait_after=random.uniform(0.8, 1.4),
    )
    _accept_cookie_banner(page)
    _human_pause(0.7, 1.7)
    _write_login_debug(page, "pre-login-fill")

    email_ok = _fill_with_retries(
        page,
        [
            "tag:input@@type=email",
            "tag:input@@autocomplete=username",
            "tag:input@@name*=email",
            "tag:input@@id*=email",
            "tag:input@@name=email",
            "tag:input@@id=email",
            "tag:input@@placeholder*=mail",
            "tag:input@@placeholder*=Email",
            "tag:input@@aria-label*=mail",
            "tag:input@@type=text",
        ],
        email,
    )
    password_ok = _fill_with_retries(
        page,
        [
            "tag:input@@type=password",
            "tag:input@@autocomplete=current-password",
            "tag:input@@name*=pass",
            "tag:input@@id*=pass",
            "tag:input@@name=password",
            "tag:input@@id=password",
            "tag:input@@placeholder*=Password",
            "tag:input@@aria-label*=Password",
        ],
        password,
    )
    if not email_ok or not password_ok:
        _write_login_debug(page, "login-form-missing")
        raise RuntimeError("PimEyes login form not found or incomplete.")

    _ensure_common_checkboxes(page)

    clicked = _click_with_retries(
        page,
        [
            "tag:button@@type=submit",
            "tag:input@@type=submit",
            "tag:button@@text()=Sign in",
            "tag:button@@text()=Log in",
            "tag:button@@text()=Login",
            "tag:button@@text()=Continue",
        ],
        tries=4,
    )
    if not clicked:
        _write_login_debug(page, "login-submit-missing")
        raise RuntimeError("Could not click PimEyes login button.")

    _human_after_action(page)
    _write_login_debug(page, "after-login-click")


def _run_search(page: ChromiumPage, face_image_path: str) -> None:
    page.get("https://pimeyes.com/en")
    _safe_pause(1.0, 1.8)
    _accept_cookie_banner(page)

    _human_scroll(page)
    uploaded = _upload_first_file_input(page, face_image_path)
    if not uploaded:
        raise RuntimeError("Could not upload face image for PimEyes search.")

    _safe_pause(1.2, 2.2)
    _ensure_common_checkboxes(page)
    _ensure_checkbox_checked(
        page,
        [
            "tag:input@@type=checkbox",
            "tag:input@@type=checkbox@@name*=consent",
            "tag:input@@type=checkbox@@name*=agree",
            "tag:input@@type=checkbox@@id*=agree",
        ],
        retries=3,
    )

    clicked_search = _click_with_retries(
        page,
        [
            "tag:button@@text()=Search",
            "tag:button@@text()=Start Search",
            "tag:button@@text()=Find",
            "tag:button@@type=submit",
            "tag:button@@id*=search",
            "tag:a@@text()=Search",
        ],
        tries=4,
    )
    if not clicked_search:
        _write_login_debug(page, "search-button-not-clicked")
        raise RuntimeError("Could not click PimEyes search button after upload.")

    _safe_pause(2.0, 3.2)


def _submit_opt_out_form(page: ChromiumPage, user_email: str) -> bool:
    print(f"[pimeyes-debug] stage=optout:url-before {page.url}")

    opt_out_urls = [
        "https://pimeyes.com/en/opt-out-request-form",
        "https://pimeyes.com/en/protect",
        "https://pimeyes.com/en/opt-out",
        "https://pimeyes.com/en/remove-me",
    ]
    for target in opt_out_urls:
        try:
            page.get(target, timeout=20)
            sleep(random.uniform(0.8, 1.4))
            _accept_cookie_banner(page)
            _human_settle(page)
            print(f"[pimeyes-debug] stage=optout:navigate url={page.url}")
            break
        except Exception as e:
            print(f"[pimeyes-debug] stage=optout:navigate-failed target={target} error={e}")

    _click_if_found(
        page,
        [
            "tag:a@@text()=Opt-Out Request",
            "tag:a@@text()=Opt-Out",
            "tag:a@@text()=Opt-out form",
            "tag:a@@text()=Opt out form",
            "tag:button@@text()=Opt-out form",
            "tag:button@@text()=Opt out form",
            "tag:a@@text()=Opt-out",
            "tag:a@@text()=Opt out",
            "tag:button@@text()=Opt-out",
            "tag:button@@text()=Opt out",
            "tag:a@@href*=opt",
            "tag:button@@href*=opt",
            "tag:a@@href*=opt-out-request-form",
        ],
        wait_after=random.uniform(1.0, 1.8),
    )

    _fill_with_retries(
        page,
        [
            "tag:input@@type=email",
            "tag:input@@name*=email",
            "tag:input@@id*=email",
            "tag:input@@placeholder*=mail",
        ],
        user_email,
    )

    _fill_with_retries(
        page,
        [
            "tag:textarea@@name*=reason",
            "tag:textarea@@id*=reason",
            "tag:textarea@@placeholder*=reason",
            "tag:textarea@@name*=message",
            "tag:textarea@@id*=message",
            "tag:textarea",
        ],
        "Please remove and suppress my face matches from PimEyes results.",
    )

    _ensure_common_checkboxes(page)

    submitted = _click_with_retries(
        page,
        [
            "tag:button@@type=submit",
            "tag:input@@type=submit",
            "tag:button@@text()=Submit",
            "tag:button@@text()=Send",
            "tag:button@@text()=Request",
            "tag:button@@text()=Opt-Out",
            "tag:button@@text()=Opt out",
            "tag:button@@text()=Continue",
            "tag:button@@text()=Next",
            "tag:button@@text()=Confirm",
        ],
        wait_after=random.uniform(1.5, 2.5),
    )

    _click_if_found(
        page,
        [
            "tag:button@@text()=Confirm",
            "tag:button@@text()=Done",
            "tag:button@@text()=Finish",
            "tag:button@@text()=OK",
        ],
        wait_after=random.uniform(0.8, 1.6),
    )

    _human_after_action(page)
    print(f"[pimeyes-debug] stage=optout:url-after {page.url}")
    return submitted


def _candidate_download_dirs() -> list[str]:
    dirs = [
        os.path.join(os.getcwd(), "downloads"),
        os.path.join(os.getcwd(), "Download"),
        os.path.join(os.getcwd(), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
    ]
    uniq = []
    for d in dirs:
        norm = os.path.normpath(d)
        if norm not in uniq:
            uniq.append(norm)
    return uniq


def _list_recent_files(paths: list[str]) -> list[tuple[float, str]]:
    out = []
    for folder in paths:
        if not os.path.isdir(folder):
            continue
        try:
            for name in os.listdir(folder):
                full = os.path.join(folder, name)
                if os.path.isfile(full):
                    out.append((os.path.getmtime(full), full))
        except Exception:
            continue
    out.sort(key=lambda x: x[0], reverse=True)
    return out


def _export_search_results(page: ChromiumPage) -> str:
    try:
        page.get("https://pimeyes.com/en/user/search", timeout=25)
    except Exception:
        pass
    _safe_pause(1.0, 2.0)
    _accept_cookie_banner(page)
    _ensure_common_checkboxes(page)

    # Some UIs hide export behind a menu (three dots / actions).
    _click_with_retries(
        page,
        [
            "tag:button@@aria-label*=More",
            "tag:button@@aria-label*=Actions",
            "tag:button@@text()=Actions",
            "tag:button@@text()=More",
            "tag:button@@text()=Menu",
        ],
        tries=2,
        wait_after=random.uniform(0.5, 1.2),
    )

    before = _list_recent_files(_candidate_download_dirs())
    baseline = max([t for t, _ in before], default=0.0)

    clicked = _click_with_retries(
        page,
        [
            "tag:button@@text()=Export",
            "tag:a@@text()=Export",
            "tag:button@@text()=Download",
            "tag:a@@text()=Download",
            "tag:button@@text()=Export results",
            "tag:button@@text()=Export Results",
            "tag:a@@text()=Export results",
            "tag:a@@text()=Export Results",
            "tag:button@@text()=Download CSV",
            "tag:button@@text()=Download PDF",
            "tag:a@@href*=export",
            "tag:a@@href*=download",
            "tag:button@@text()=Export all",
            "tag:button@@text()=Export All",
            "tag:a@@text()=Export all",
            "tag:a@@text()=Export All",
            "tag:button@@aria-label*=Export",
            "tag:a@@aria-label*=Export",
            "tag:button@@id*=export",
            "tag:button@@class*=export",
            "tag:a@@class*=export",
        ],
        tries=5,
    )
    if not clicked:
        raise RuntimeError("Could not find PimEyes export/download action.")

    _human_pause(0.6, 1.3)
    _click_if_found(
        page,
        [
            "tag:button@@text()=CSV",
            "tag:button@@text()=PDF",
            "tag:a@@text()=CSV",
            "tag:a@@text()=PDF",
            "tag:button@@text()=Confirm",
            "tag:button@@text()=Download",
        ],
        wait_after=random.uniform(1.0, 1.8),
    )

    picked = ""
    for _ in range(12):
        sleep(1.0)
        recent = _list_recent_files(_candidate_download_dirs())
        for mtime, file_path in recent:
            low = file_path.lower()
            if mtime <= baseline:
                continue
            if low.endswith('.crdownload') or low.endswith('.tmp'):
                continue
            picked = file_path
            break
        if picked:
            break

    if not picked:
        raise RuntimeError("Export was triggered but downloaded file was not found.")

    export_dir = os.path.join(os.getcwd(), "exports", "pimeyes")
    os.makedirs(export_dir, exist_ok=True)

    basename = os.path.basename(picked)
    dest = os.path.join(export_dir, basename)
    if os.path.exists(dest):
        stem, ext = os.path.splitext(basename)
        dest = os.path.join(export_dir, f"{stem}-{int(datetime.datetime.now().timestamp())}{ext}")

    shutil.move(picked, dest)
    print(f"[pimeyes-debug] stage=export:file {dest}")
    return dest


def _looks_like_url(value: str) -> bool:
    v = (value or "").strip().lower()
    return v.startswith("http://") or v.startswith("https://")


def _download_to_cache(source_url: str) -> str:
    cache_dir = os.path.join(os.getcwd(), "assets", "uploads", "specialinfo", "_remote_cache")
    os.makedirs(cache_dir, exist_ok=True)
    filename = quote(source_url, safe="")
    local_path = os.path.join(cache_dir, filename)
    if not os.path.exists(local_path):
        urlretrieve(source_url, local_path)
    return local_path


def _filename_candidates(face_filename: str) -> list[str]:
    base = (face_filename or "").strip()
    if not base:
        return []

    candidates = [base]
    common_exts = [".jpg", ".jpeg", ".png", ".webp"]
    if "." not in os.path.basename(base):
        for ext in common_exts:
            candidates.append(base + ext)
    return candidates


def _download_first_success(urls: list[str]) -> str:
    attempted = []
    for url in urls:
        attempted.append(url)
        try:
            return _download_to_cache(url)
        except (HTTPError, URLError):
            continue

    msg = "Remote face image download failed. Tried URLs:\n" + "\n".join(f"- {u}" for u in attempted)
    raise FileNotFoundError(msg)


def _resolve_face_image_path(face_image_path: str, face_filename: str) -> str:
    if face_image_path and os.path.exists(face_image_path):
        return face_image_path

    if _looks_like_url(face_image_path):
        return _download_first_success([face_image_path])

    base_url = (os.getenv("PD_FACE_IMAGE_BASE_URL", "") or os.getenv("FACE_IMAGE_BASE_URL", "")).strip()
    if base_url and face_filename:
        root = base_url if base_url.endswith("/") else base_url + "/"
        urls = []
        for name in _filename_candidates(face_filename):
            urls.append(urljoin(root, quote(name, safe="")))
            urls.append(urljoin(root, name))
        return _download_first_success(urls)

    return ""


def pimeyescom(dataRow, website_name, in_user_email, run_mode):
    """
    PimEyes account workflow automation.

    Required:
      - PIMEYES_PASSWORD env var
      - PIMEYES_EMAIL env var (optional; falls back to in_user_email/dataRow["User Email"])
      - Face image provided as local path, full URL, or via PD_FACE_IMAGE_BASE_URL + Face Filename

    Flow:
      sign in -> submit opt-out form -> search with uploaded face -> export results
    """
    face_image_path = dataRow.get("Face Image Path") or ""
    face_filename = dataRow.get("Face Filename") or ""
    user_email = (in_user_email or dataRow.get("User Email") or "").strip()
    login_email = (os.getenv("PIMEYES_EMAIL", "") or user_email).strip()
    login_password = os.getenv("PIMEYES_PASSWORD", "").strip()

    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    base_dir = os.getcwd()
    screenshot_dir = os.path.join(base_dir, "ScreenShot", current_date)
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_save_path = os.path.join(screenshot_dir, f"PimEyes-{int(now.timestamp())}.png")

    print("[pimeyes-debug] stage=resolve-face-image:start")
    resolved_face_image_path = _resolve_face_image_path(face_image_path, face_filename)
    print(f"[pimeyes-debug] stage=resolve-face-image:done path={resolved_face_image_path}")
    if not resolved_face_image_path or not os.path.exists(resolved_face_image_path):
        raise FileNotFoundError(
            "Face image not found locally and could not fetch from remote. "
            "Provide a valid local path, full image URL, or set PD_FACE_IMAGE_BASE_URL."
        )
    if not login_email:
        raise ValueError("Missing PimEyes login email (PIMEYES_EMAIL or user email).")
    if not login_password:
        raise ValueError("Missing PimEyes login password (PIMEYES_PASSWORD).")

    arguments = [
        "--start-maximized",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ]

    print("[pimeyes-debug] stage=browser-options:start")
    options = get_chromium_options(arguments).auto_port()
    if run_mode == "headless":
        options.headless()

    print("[pimeyes-debug] stage=browser-create:start")
    page = ChromiumPage(addr_or_opts=options)
    print("[pimeyes-debug] stage=browser-create:done")
    try:
        print("[pimeyes-debug] stage=login:start")
        _login_pimeyes(page, login_email, login_password)
        print("[pimeyes-debug] stage=login:done")
        print("[pimeyes-debug] stage=optout:start")
        optout_submitted = _submit_opt_out_form(page, login_email)
        print(f"[pimeyes-debug] stage=optout:done submitted={optout_submitted}")
        if not optout_submitted:
            _write_login_debug(page, "optout-submit-not-found")
            print("[pimeyes-debug] warn=optout-submit-not-found-continue")

        print("[pimeyes-debug] stage=search:start")
        _run_search(page, resolved_face_image_path)
        print("[pimeyes-debug] stage=search:done")

        print("[pimeyes-debug] stage=export:start")
        exported_path = _export_search_results(page)
        print(f"[pimeyes-debug] stage=export:done path={exported_path}")

        page.get_screenshot(screenshot_save_path)
        return screenshot_save_path
    finally:
        page.quit()
