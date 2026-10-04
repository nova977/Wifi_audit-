#!/usr/bin/env python3
import csv
import json
import argparse
import sys
import os


def parse_wifi_csv(filename):
    aps = {}
    clients = []
    parsing_clients = False

    with open(filename, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)

        for row in reader:
            if not row or len(row) < 2:
                continue

            # Detect start of client section
            if row[0].strip() == "Station MAC":
                parsing_clients = True
                continue

            # ================= ACCESS POINTS =================
            if not parsing_clients:
                if row[0].strip() == "BSSID":
                    continue

                bssid = row[0].strip()
                first_seen = row[1].strip()
                last_seen = row[2].strip()
                channel = row[3].strip()
                privacy = row[5].strip()
                cipher = row[6].strip()
                auth = row[7].strip()
                power = row[8].strip()
                essid = row[13].strip() if len(row) > 13 and row[13].strip() else "<hidden>"

                aps[bssid] = {
                    "bssid": bssid,
                    "essid": essid,
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                    "channel": channel,
                    "power": power,
                    "security": {
                        "privacy": privacy,
                        "cipher": cipher,
                        "authentication": auth
                    },
                    "clients": []
                }

            # ================= CLIENTS =================
            else:
                station = row[0].strip()
                first_seen = row[1].strip()
                last_seen = row[2].strip()
                power = row[3].strip()
                bssid = row[5].strip()

                client = {
                    "station": station,
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                    "power": power,
                    "bssid": None if "(not associated)" in bssid else bssid
                }

                clients.append(client)

    # Link clients to APs
    for c in clients:
        if c["bssid"] and c["bssid"] in aps:
            aps[c["bssid"]]["clients"].append(c)

    return {
        "access_points": list(aps.values()),
        "unassociated_clients": [c for c in clients if c["bssid"] is None]
    }


def main():
    parser = argparse.ArgumentParser(description="Parse airodump-ng CSV to JSON")
    parser.add_argument("csvfile", help="Path to airodump CSV file")
    parser.add_argument("-o", "--output", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    if args.csvfile:
        pass
    else:
        print(f"File not Found {args.csvfile}")
        sys.exit()

    data = parse_wifi_csv(args.csvfile)
    json_data = json.dumps(data, indent=4)


    if args.output:
        if not os.path.exists(os.path.join(os.getcwd(), "capture")):
            os.makedirs(os.path.join(os.getcwd(), "capture"))
        new_dir = os.path.join(os.getcwd(), "capture")

        output_path = os.path.join(new_dir, args.output)
        with open(output_path, "w") as f:
            f.write(json_data)
        print(f"[+] JSON written to {args.output}")
    else:
        print(json_data)


if __name__ == "__main__":
    main()
