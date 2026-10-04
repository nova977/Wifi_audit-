import subprocess
import csv
import re
import os
import signal
from datetime import datetime
import json
from collections import defaultdict
import shutil
import psutil
import time
import socket
import traceback

DEPENDENCIES = {
    "Recon": {
        "tools": ["iw", "ttyd"],
        "scripts": ["parser2.py"]
    },
    "Handshake Capture": {
        "tools": ["aireplay-ng", "airodump-ng", "aircrack-ng"],
        "scripts": [os.path.join("Handshake_detection", "handshake_detector.py"), "wpa3.py"]
    },
    "Wireless Landscape": {
        "tools": ["airodump-ng"],
        "scripts": ["airo_csv_parser.py"]
    },
    "Probes": {
        "tools": ["kismet", "tcpdump", "scapy"],
        "scripts": ["probes_to_json.py", "probe_cap.py"]
    },
    "Beacon Flood": {
        "tools": ["scapy"],
        "scripts": ["beacons.py"]
    },
    "WAP": {
        "tools": ["dnsmasq", "iw", "hostapd"],
        "scripts": []
    }
}



################# SMALL TEST ################

def fetch_wifi_data():
    """
    SAFE data extractor for live UI polling.
    NO subprocess, NO deletes, NO redirects.
    """

    running = is_running()
    state = load_state()

    # No capture started
    if not os.path.exists("prefix.txt"):
        return {
            "running": running,
            "grouped_aps": {},
            "unassociated_clients": [],
            "elapsed_time": "0s",
        }

    # Select prefix file

    with open("prefix.txt") as f:
        csv_file = f.read().strip()

    json_file = f"{os.path.splitext(csv_file)[0]}.json"
    json_path = os.path.join(os.getcwd(), "capture", json_file)

    data = {}
    if os.path.exists(json_path):
        data = load_json(json_path)

    aps = data.get("access_points", [])
    grouped_aps = group_aps_by_ssid(aps)
    unassociated_clients = get_unassociated_clients(data)

    # elapsed time
    elapsed_time = "0s"
    if running and state.get("started_at"):
        started = datetime.fromisoformat(state["started_at"])
        elapsed_seconds = int((datetime.now() - started).total_seconds())
        mins, secs = divmod(elapsed_seconds, 60)
        elapsed_time = f"{mins}m {secs}s" if mins else f"{secs}s"

    return {
        "running": running,
        "grouped_aps": grouped_aps,
        "unassociated_clients": unassociated_clients,
        "elapsed_time": elapsed_time,
    }

###############################################




##############" LOGS##############"
def tail_file(path):
    with open(path, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue

            # Force proper newline for SSE
            line = line.rstrip("\n")
            yield f"data: {line}\n\n"
##########################################




#########AUTH UGLY PANNEL ############################
# helpers.py
from flask import request, Response
from functools import wraps

# ---- SINGLE USER CREDENTIALS ----
USER = "admin"
PASSWORD = "1234"


def check_auth(username, password):
    return username == USER and password == PASSWORD


def authenticate():
    """Return 401 so browser shows login popup"""
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="Restricted"'},
    )


def requires_auth(route_function):
    """Decorator to protect a route"""
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        auth = request.authorization

        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()

        return route_function(*args, **kwargs)

    return wrapper




###########"END OF AUTH#########################"

#######GET FILES################################
#Detect all capture files on the system
#Return a list of file paths

data = {}

def iterate_dir(root):
    for dirpath, dirnames, filenames in os.walk(root):
        for file in filenames:
            print(file)
            full_path = os.path.join(dirpath, file)

            ext = os.path.splitext(file)[1].lower()
            if ext in (".pcap", ".pcapng", ".cap"):

                match = re.search(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}", file)
                if match:
                    timestamp = match.group(0)
                    data[full_path] = timestamp
                    print(full_path, "->", timestamp)

def get_files():
    iterate_dir(os.getcwd())
    print(data)

#get_files()


def has_internet(host="1.1.1.1", port=53, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except:
        return False


def has_internet_int(interface, host="1.1.1.1", port=53, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)

        s.setsockopt(socket.SOL_SOCKET, 25, interface.encode())  # SO_BINDTODEVICE

        s.connect((host, port))
        s.close()
        #print(f"Yes for {interface}")
        return True
    except:
        #print(f"No for {interface}")
        return False


def get_interfaces():
    interfaces = []

    # Get all interfaces using 'ip link'
    try:
        ip_output = subprocess.check_output(['ip', 'link'], text=True)
        # Each interface block starts with a number: "1: lo: ..."
        for line in ip_output.splitlines():
            m = re.match(r'^\d+: (\S+): <(.+)>', line)
            if m:
                iface = m.group(1).rstrip(':')
                interfaces.append(iface)
                #flags = m.group(2).split(',')
                #interfaces[iface] = {}
    except Exception as e:
        print(f"Error getting interfaces: {e}")
        return {}

    for i in interfaces:
        if "Docker" or "lo" in i:
            interfaces.remove(i)
    return interfaces



def get_cpu_ram():
    cpu = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()
    return {
        "cpu": cpu,
        "ram_percent": mem.percent,
        "ram_used": round(mem.used / (1024**3), 2),
        "ram_total": round(mem.total / (1024**3), 2)
    }


def is_ssh_running():
    # systemd check (most modern Linux)
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "ssh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if result.stdout.decode().strip() == "active":
            return True
    except:
        pass

    # fallback: check sshd process
    return any("sshd" in p.name() for p in psutil.process_iter())


def has_internet(host="1.1.1.1", port=53, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except:
        return False


def get_unassociated_clients(json_data):
    return json_data.get("unassociated_clients", [])

def load_json(filename):
    """Load JSON data from a file."""
    with open(filename, "r") as f:
        return json.load(f)

def group_aps_by_ssid(access_points):
    """Group APs by SSID (or BSSID if hidden)."""
    grouped = {}
    for ap in access_points:
        key = ap["essid"] if ap["essid"] != "<hidden>" else ap["bssid"]
        grouped.setdefault(key, []).append(ap)
    return grouped

def get_band(channel):
    """Return the band string based on channel."""
    ch = int(channel)
    if 1 <= ch <= 14:
        return "2.4 GHz"
    return "5 GHz"

def format_security(security):
    """Format security information as a string."""
    privacy = security.get("privacy", "")
    cipher = security.get("cipher", "")
    auth = security.get("authentication", "")
    parts = [part for part in [privacy, cipher, auth] if part]
    return ", ".join(parts) if parts else "None"




STATE_FILE = "capture_state.json"

DEFAULT_STATE = {
    "mode": None,        # "tcpdump" | "kismet" | None
    "pid": None,
    "started_at": None,
    "prefix": None
}

# ----------------------------
# STATE IO
# ----------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return DEFAULT_STATE.copy()

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_STATE.copy()

    # Ensure all keys exist
    for key in DEFAULT_STATE:
        state.setdefault(key, DEFAULT_STATE[key])

    return state


def save_state(state):
    """
    Persist capture state to disk.
    """
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ----------------------------
# STATE MUTATORS
# ----------------------------
def set_state(mode, pid, prefix):
    """
    Record a newly started capture.
    """
    state = {
        "mode": mode,
        "pid": pid,
        "started_at": datetime.now().isoformat(),
        "prefix": prefix
    }
    save_state(state)


def clear_state():
    state = load_state()
        # Only clear runtime info
    state["pid"] = None
    state["started_at"] = None

        # Keep mode and prefix
    save_state(state)


# ----------------------------
# PROCESS CHECKS
# ----------------------------
def is_running():
    """
    Check if the recorded capture process is still alive.
    """
    state = load_state()
    pid = state.get("pid")

    if not pid:
        return False

    try:
        os.kill(pid, 0)  # does not kill, just checks existence
        return True
    except OSError:
        return False


def stop_capture(sig=signal.SIGTERM):
    """
    Stop the running capture process (if any) and clear state.
    """
    state = load_state()
    pid = state.get("pid")

    if pid:
        try:
            os.kill(pid, sig)
        except OSError:
            pass

    clear_state()




def run(cmd):
    subprocess.run(cmd, shell=True)




def get_current_channel(interface):
    # Run iwlist and capture both stdout and stderr
    result = subprocess.run(
        f"iwlist {interface} channel",
        shell=True,
        capture_output=True,
        text=True
    )
    output = result.stdout + "\n" + result.stderr  # combine both

    channels = [int(ch) for ch in re.findall(r'Channel (\d+)', output)]
    current = channels[-1]
    del channels[-1]

    return current, channels


def set_channel(interface, channel):
    run(f"sudo iw dev {interface} set channel {channel}")


def tool_exist(command_name):
    if shutil.which(command_name):
        return True
    else:
        return False


# helpers.py
def check_dependencies(dep_map):
    missing_tools = []
    missing_scripts = []
    tool_pages = {}    # tool -> list of pages using it
    script_pages = {}  # script -> list of pages using it

    for page, deps in dep_map.items():
        # check tools
        for tool in deps["tools"]:
            if not tool_exist(tool):
                if tool not in missing_tools:
                    missing_tools.append(tool)
                tool_pages.setdefault(tool, []).append(page)

        # check scripts
        for script in deps["scripts"]:
            if not os.path.exists(script):
                if script not in missing_scripts:
                    missing_scripts.append(script)
                script_pages.setdefault(script, []).append(page)

    return missing_tools, missing_scripts, tool_pages, script_pages





def monitor(nic):
    run(f"sudo ip link set {nic} down")
    run(f"sudo iw dev {nic} set type monitor")
    run(f"sudo ip link set {nic} up")

def manage(nic):
    run(f"sudo ip link set {nic} down")
    run(f"sudo iw dev {nic} set type managed")
    run(f"sudo ip link set {nic} up")


def kill_PID():
    subprocess.run(["sudo", "pkill", "-f", "airodump-ng"])
    subprocess.run(["sudo", "pkill", "-f", "aireplay-ng"])
    try:
        subprocess.run(["sudo", "pkill", "-f", "handshake_detector.py"])
    except:
        pass


def get_nics():
    nics = []

    # Get list of interfaces and their mode
    iw_output = subprocess.check_output("iw dev", shell=True, text=True)
    current_iface = None
    iface_modes = {}
    for line in iw_output.splitlines():
        line = line.strip()
        if line.startswith("Interface"):
            current_iface = line.split()[1]
        elif current_iface and line.startswith("type"):
            mode = line.split()[1]
            iface_modes[current_iface] = mode
            current_iface = None

    # Parse lsusb for all devices
    lsusb_output = subprocess.check_output("lsusb", shell=True, text=True)
    lsusb_lines = lsusb_output.splitlines()

    for iface, mode in iface_modes.items():
        # Resolve the USB device path
        try:
            device_path = os.readlink(f"/sys/class/net/{iface}/device")
            # The USB ID is like 'usb1/1-1.4' → we take the last part '1-1.4'
            usb_id = device_path.split('/')[-1]
        except Exception:
            usb_id = None

        # Find matching lsusb line
        name = "Unknown"
        if usb_id:
            for line in lsusb_lines:
                # match by USB bus:device ID (simpler)
                if usb_id in line or line.startswith("Bus"):
                    # Example line: "Bus 001 Device 004: ID 0bda:8813 Realtek Semiconductor Corp. RTL8814AU 802.11a/b/g/n/ac Wireless Adapter"
                    parts = line.split("ID")
                    if len(parts) > 1:
                        name = parts[1].strip()
                        break

        nics.append({
            "name": iface,
            "mode": mode,
            "chipset": name
        })

    return nics

def load_networks():
    try:
        with open("networks.json") as f:
            nets = json.load(f)
            nets.sort(key=lambda n: n.get("signal", -100), reverse=True)
            for n in nets:
                n.pop("capabilities", None)
            return nets
    except Exception:
        return None


def load_scan_time():
    try:
        return datetime.fromtimestamp(os.path.getmtime("networks.json")).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def get_voltage():
    try:
        out = subprocess.check_output("vcgencmd get_throttled", shell=True, text=True)
        undervoltage = "0x50000" in out or "0x50005" in out
        voltage = 5.0 if not undervoltage else 4.7
        return voltage, undervoltage
    except Exception:
        return "Not available", False


def get_temperature():
    try:
        out = subprocess.check_output(
            "vcgencmd measure_temp",
            shell=True,
            text=True
        ).strip()
        # output looks like: temp=48.2'C
        temp = float(out.split('=')[1].replace("'C", ""))
        return temp
    except Exception:
        return "Temperature Not Available"




def Kill_probe_capture():
    run("sudo pkill -f tcpdump")

def Kill_probe_kis_capture():
    run("sudo pkill -f kismet")



def load_probes(probe_file):
    if not probe_file or not os.path.exists(probe_file):
        return []

    try:
        with open(probe_file) as f:
            probes = json.load(f)
            probes.sort(key=lambda p: p.get("timestamp", 0))
            return probes
    except Exception:
        return []



#######GET card information ###########

def get_iface_bands_shell():
    nics = get_nics()
    iface_bands = {}

    for nic in nics:
        iface = nic["name"]

        try:
            output = subprocess.check_output(
                f"iwlist {iface} channel",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            continue  # interface might be down or not wireless

        # Extract frequencies like: "2.412 GHz"
        freqs = re.findall(r'([\d\.]+)\s*GHz', output)

        bands = set()
        for f in freqs:
            f = float(f)
            if f < 3:
                bands.add(2.4)
            elif f < 6:
                bands.add(5.0)
            else:
                bands.add(6.0)

        # Sort and store
        iface_bands[iface] = sorted(list(bands))

    return iface_bands


######################### WAP ############################
def load_wap_config(config_file):
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    return {}


def save_wap_config(config_file, config):
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)

import textwrap
def convert_to_hostapd_format(config_file_path):
    data = load_wap_config(config_file=config_file_path)
    iface = data.get("iface", "wlan0")
    ssid = data.get("ssid", "TestAP")
    channel = data.get("channel", "6")
    psk = data.get("psk", "12345678")
    security = data.get("sec", "wpa2")

    if security == "wpa3":
        auth_algs = 1
        wpa = 2
        wpa_key_mgmt = "SAE"
    elif security == "none":
        auth_algs = 1
        wpa = 0
        wpa_key_mgmt = ""
    else:  # wpa2 default
        auth_algs = 1
        wpa = 2
        wpa_key_mgmt = "WPA-PSK"

    hostapd_config = textwrap.dedent(f"""
    interface={iface}
    driver=nl80211
    ssid={ssid}
    hw_mode=g
    channel={channel}
    country_code=FR
    ieee80211n=1
    wmm_enabled=1
    auth_algs={auth_algs}
    wpa={wpa}
    wpa_passphrase={psk}
    wpa_key_mgmt={wpa_key_mgmt}
    wpa_pairwise=CCMP
    rsn_pairwise=CCMP
    """)

    return hostapd_config



def get_iface_info(iface):
    try:
        output = subprocess.check_output(['ip', 'add', 'show', iface], text=True)
    except subprocess.CalledProcessError:
        return None, None

    mac = re.search(r'link/ether\s+([0-9a-f:]{17})', output)
    ip  = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)

    mac = mac.group(1) if mac else None
    ip  = ip.group(1) if ip else None

    return mac, ip


def find_dnsmasq_conf():
    dir = os.getcwd()
    example_config_path = os.path.join(dir, "dnsmasq_example_config.txt")
    if os.path.exists(example_config_path):
        return example_config_path
    else:
        return None


def convert_to_dnsmasq_format(config_file_path):
    data = load_wap_config(config_file=config_file_path)
    iface = data.get("iface", "wlan0")
    _, ip = get_iface_info(iface)


    dnsmasq_conf = f"""
interface={iface}
bind-interfaces
dhcp-range = 192.168.50.10, 192.168.50.100, 12h
dhcp-option = 3, 192.168.50.1  # Gateway
dhcp-option = 6, 192.168.50.1  # DNS server (you)
dhcp-leasefile=/var/lib/misc/dnsmasq-ap1.leases

############################
# UPSTREAM DNS
############################
no-resolv
server = 8.8.8.8
server = 1.1.1.1

############################
# YOUR PRIVATE DNS OVERRIDE
############################
# Force your domain to your server
address = / google.com / 192.168.50.1
# address=/lab.internal/192.168.50.100


# Configuration file for dnsmasq.
"""

    return dnsmasq_conf


def find_dnsmasq_config_name():
    file = "/etc/dnsmasq.conf"
    if os.path.exists(file):
        return True
    else:
        return False



def check_dnsmasq_syntax(file):
    result = subprocess.run(
        ["dnsmasq", "--test", "-C", file],
        capture_output=True,
        text=True
    )

    output = result.stdout + result.stderr

    return result.returncode == 0, output


    ######################### WAP Info###########################"




################ Create the WAP state #############################


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
    state[service]["started_at"] = datetime.now().isoformat()
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


def stop_ap(sig=signal.SIGTERM):
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

###################################################################


##########GET Clients ##########
import subprocess

import time




def get_connected_clients(lease_file):
    """
    Parse dnsmasq DHCP leases.

    Returns:
    [
        {
            "mac": "...",
            "ip": "...",
            "hostname": "...",
            "lease_expires": 1753301000,
            "lease_remaining": 842,
            "connected": True
        }
    ]
    """

    devices = []

    try:
        with open(lease_file) as f:

            now = int(time.time())

            for line in f:

                parts = line.split()

                if len(parts) < 4:
                    continue

                expiry = int(parts[0])
                mac = parts[1]
                ip = parts[2]
                hostname = parts[3] if parts[3] != "*" else "Unknown"

                remaining = max(0, expiry - now)

                devices.append({
                    "mac": mac,
                    "ip": ip,
                    "hostname": hostname,
                    "lease_expires": expiry,
                    "lease_remaining": remaining,
                    "connected": remaining > 0
                })

    except FileNotFoundError:
        pass

    return devices
###########################################

################### DNS Records: #################"

import os
import subprocess


def get_dns():
    pcap_path = os.path.expanduser("/home/frank/pi_pinap/wap/dns_capture.pcap")
    txt_output = os.path.expanduser("/home/frank/pi_pinap/wap/output.txt")
    parser_script = os.path.expanduser("/home/frank/pi_pinap/wap/dns_test.py")
    json_output = os.path.expanduser("/home/frank/pi_pinap/wap/dns.json")

    # Quick pre-flight check to save you debugging time
    if not os.path.exists(pcap_path):
        print(f"Error: Target file {pcap_path} does not exist yet.")
        return

    print("Running tcpdump extraction safely...")

    tcpdump_cmd = f"sudo tcpdump -l -r {pcap_path} -n > {txt_output}"

    # We remove check=True and use a try/except block to absorb truncation errors
    try:
        result = subprocess.run(
            tcpdump_cmd, shell=True, capture_output=True, text=True
        )

        if result.returncode != 0:
            print(
                f"Warning: tcpdump finished with exit code {result.returncode}."
            )
            print(f"Details: {result.stderr.strip()}")
            # We don't return here because even if tcpdump errored due to a
            # partial trailing packet, it likely still successfully extracted hundreds of valid lines!

    except Exception as e:
##        print(f"An unexpected process error occurred: {e}")
        return

    print(
        f"Proceeding to parse whatever data was recovered into {json_output}..."
    )

    # Launch your parsing script against the generated file
    subprocess.Popen(
        ["sudo", "python3", parser_script, txt_output, json_output]
    )
