# lib/safe_browser.py — context manager that GUARANTEES the ChromiumPage is
# quit, even if the broker raises mid-flow.
#
# Why this exists: the typical broker pattern is
#
#     def acxiomcom(data, ...):
#         try:
#             ...
#             page = ChromiumPage(addr_or_opts=options)   # line 161
#             ...
#         except Exception as e:
#             ...
#         page.quit()                                      # line 236
#
# If anything raises BEFORE line 161, `page` is undefined and line 236 throws
# `NameError: name 'page' is not defined` — which (a) escapes the broker,
# (b) leaks the chromium process if it had started, and (c) hides the real
# error from logs. This shows up in our metrics as inexplicable broker
# failures + chromium process count creeping up over hours.
#
# Usage in a refactored broker:
#
#     from lib.safe_browser import safe_chromium
#     def mybroker(data, ...):
#         with safe_chromium(arguments=[...], run_mode=run_mode) as page:
#             page.get(URL)
#             ...
#         return screenshot_path
#
# The context manager owns the lifecycle. The browser will be quit whether
# the broker returned normally or raised.
import contextlib
import logging

log = logging.getLogger("pd.safe_browser")


@contextlib.contextmanager
def safe_chromium(arguments=None, run_mode="non-headless", add_extension=None, use_proxy=False):
    """Yields a ChromiumPage configured with the given args, guarantees
    .quit() on exit.

    arguments:     list of CLI args to pass to chromium
    run_mode:      "headless" | "non-headless"
    add_extension: path to a chromium extension to load (or None)
    use_proxy:     if True, wire up lib.proxies.get_proxy_extension()
    """
    from DrissionPage import ChromiumPage, ChromiumOptions

    options = ChromiumOptions()
    for arg in (arguments or []):
        options.set_argument(arg)
    options = options.auto_port()
    if add_extension:
        options.add_extension(add_extension)
    if use_proxy:
        from lib.proxies import get_proxy_extension
        try:
            options.add_extension(get_proxy_extension())
        except Exception:
            log.exception("safe_chromium: proxy extension load failed; continuing without proxy")
    if run_mode == "headless":
        options.headless()

    page = ChromiumPage(addr_or_opts=options)
    try:
        yield page
    finally:
        try:
            page.quit()
        except Exception:
            log.exception("safe_chromium: page.quit() raised; chromium may be leaked")
