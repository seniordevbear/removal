import random
import threading

_PATCH_LOCK = threading.Lock()
_PATCHED = False


def enable_automation_delays() -> None:
    """
    Add small randomized delays only between typed characters.
    Avoid extra waits before clicks/page actions.
    """
    global _PATCHED

    if _PATCHED:
        return

    with _PATCH_LOCK:
        if _PATCHED:
            return

        from DrissionPage._units.actions import Actions

        original_actions_type = Actions.type

        def actions_type_with_delay(self, keys, interval=0):
            # Keep delays small and only for typing cadence.
            mixed_interval = max(interval, random.uniform(0.02, 0.07))
            return original_actions_type(self, keys, interval=mixed_interval)

        Actions.type = actions_type_with_delay
        _PATCHED = True
