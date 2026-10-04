import json
import os
from datetime import datetime
import signal


STATE_FILE2 = os.path.join("wap", "wap_state.json")

DEFAULT_STATE = {
    "hostapd": {"pid": None, "started_at": None, "config_file": None},
    "dnsmasq": {"pid": None, "started_at": None, "config_file": None}
}


def load_state_2():
    if not os.path.exists(STATE_FILE2):
        return DEFAULT_STATE.copy()
    try:
        with open(STATE_FILE2, "r") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_STATE.copy()
    for key in DEFAULT_STATE:
        state.setdefault(key, DEFAULT_STATE[key])
    return state

def save_state_2(state):
    with open(STATE_FILE2, "w") as f:
        json.dump(state, f)


def set_state_2(service, pid, config_file):
    """
    Record a newly started service (e.g. 'hostapd' or 'dnsmasq').
    """
    if service not in DEFAULT_STATE:
        raise ValueError(f"Unknown service: {service!r}. Must be one of {list(DEFAULT_STATE)}")
    state = load_state_2()
    state[service]["pid"] = pid
    state[service]["started_at"] = datetime.datetime.now().isoformat()
    state[service]["config_file"] = config_file
    save_state_2(state)


def clear_state_2():
    """
    Clear runtime info for all services.
    """
    state = load_state_2()
    for service in DEFAULT_STATE:
        state[service]["pid"] = None
        state[service]["started_at"] = None
    save_state_2(state)

def is_running_2():
    """
    Check if ALL service processes are still alive.
    """
    state = load_state_2()
    for service in DEFAULT_STATE:
        pid = state[service].get("pid")
        if not pid:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False
    return True


def stop_capture_ap(sig=signal.SIGTERM):
    """
    Stop the running capture process (if any) and clear state.
    """
    state = load_state_2()
    pid = state.get("pid")

    if pid:
        try:
            os.kill(pid, sig)
        except OSError:
            pass

    clear_state_2()

set_state_2("hostapd", 331, "test.conf")
state = load_state_2()
running = is_running_2()
print(running)
print(state)

clear_state_2()
state2 = load_state_2()
print(state2)
print(is_running_2())
