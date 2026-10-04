#!/usr/bin/env python3
import re
import json
import sys
from collections import defaultdict

def freq_to_channel(freq):
    freq = float(freq)
    if 2412 <= freq <= 2472:
        return int((freq - 2407) / 5)
    if freq == 2484:
        return 14
    if 5000 <= freq <= 5900:
        return int((freq - 5000) / 5)
    return None

def parse_scan(file_path):
    networks = []
    current = None

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip()

            # New BSS
            m = re.match(r"BSS ([0-9a-f:]{17})\(on (\S+)\)", line)
            if m:
                if current:
                    networks.append(current)
                current = defaultdict(lambda: None)
                current["bssid"] = m.group(1)
                current["interface"] = m.group(2)
                current["security"] = set()
                continue

            if current is None:
                continue

            # SSID
            if line.strip().startswith("SSID:"):
                current["ssid"] = line.split("SSID:", 1)[1].strip()

            # Frequency
            if line.strip().startswith("freq:"):
                freq = line.split("freq:", 1)[1].strip()
                current["frequency_mhz"] = float(freq)
                current["channel"] = freq_to_channel(freq)

            # Signal
            if line.strip().startswith("signal:"):
                current["signal_dbm"] = float(line.split("signal:", 1)[1].split()[0])

            # Last seen
            if line.strip().startswith("last seen:"):
                current["last_seen"] = line.split("last seen:", 1)[1].strip()

            # Beacon interval
            if line.strip().startswith("beacon interval:"):
                current["beacon_interval"] = line.split("beacon interval:", 1)[1].strip()

            # Capabilities
            if line.strip().startswith("capability:"):
                current["capabilities"] = line.split("capability:", 1)[1].strip()

            # Security detection
            if line.strip().startswith("WEP"):
                current["security"].add("WEP")

            if line.strip().startswith("WPA:"):
                current["security"].add("WPA")

            if line.strip().startswith("RSN:"):
                current["security"].add("WPA2")

            if "SAE" in line:
                current["security"].add("WPA3")

        if current:
            networks.append(current)

    # Normalize security + add IDs
    for idx, net in enumerate(networks, start=1):
        net["id"] = idx  # <-- ENUMERATION HERE

        if not net["security"]:
            net["security"] = {"OPEN"}

        net["security"] = ", ".join(sorted(net["security"]))

    return networks


def print_results(networks):
    print("=" * 140)
    print(f"{'ID':<4} {'SSID':<25} {'BSSID':<18} {'Ch':<4} {'Freq(MHz)':<9} {'Signal':<8} {'Security':<15} {'Last seen'}")
    print("=" * 140)

    for n in networks:
        print(
            f"{n['id']:<4} "
            f"{(n['ssid'] or '<hidden>'):<25} "
            f"{n['bssid']:<18} "
            f"{str(n['channel']):<4} "
            f"{str(n['frequency_mhz']):<9} "
            f"{str(n['signal_dbm']):<8} "
            f"{n['security']:<15} "
            f"{n.get('last_seen', '')}"
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 wifi_scan_parser.py scan.txt")
        sys.exit(1)

    networks = parse_scan(sys.argv[1])
    print_results(networks)

    # --- JSON export ---
    with open("networks.json", "w", encoding="utf-8") as f:
        json.dump(networks, f, indent=4)

    print("\nSaved parsed networks to networks.json")
