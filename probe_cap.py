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



def capture_kis(interface, file):
    print("\n[*] Launching attack (Ctrl+C to stop)...")

    dump = subprocess.Popen(
        ["sudo", "kismet", "-c", interface , "--no-ncurses", "--log-types", "pcapng", "-t", file])

    # processes.extend(dump)

    dump.wait()



def capture(interface, file):
    print("\n[*] Launching attack (Ctrl+C to stop)...")

    dump = subprocess.Popen(
        ["tcpdump", "-i", interface,
         "type", "mgt", "subtype", "probe-req", "or", "subtype", "probe-resp",
         "-w", file])


    #processes.extend(dump)

    dump.wait()


# ---------- Main ----------
def main():

    parser = argparse.ArgumentParser(
        description="Probe Capture"
    )
    parser.add_argument(
        "-i", "--interface", required=True,
        help="Monitor mode interface (default: wlan0mon)"
    )

    parser.add_argument(
        "-f", "--file", required=True,
        help=".PCAP file to save capture"
    )

    parser.add_argument(
        "-k", "--kismet", action="store_true",
        help="If specified the capture runs with kismet (no live output in the UI like TCPDUMP)"
    )

    args = parser.parse_args()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    if args.kismet:
        file_prefix = f"{args.file}_{timestamp}"
        file_kismet_prefix = f"{args.file}_{timestamp}.pcapng"
        print(file_kismet_prefix)
        with open("probe_prefix2.txt", "w") as file:
            file.write(file_kismet_prefix)
        capture_kis(interface= args.interface,file=file_prefix)

    else:
        file_prefix = f"{args.file}_{timestamp}.pcap"
        with open("probe_prefix.txt", "w") as file:
            file.write(file_prefix)

        capture(interface= args.interface,file=file_prefix)




if __name__ == "__main__":
    main()
