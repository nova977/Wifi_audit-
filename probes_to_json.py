from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Elt, RadioTap
from scapy.error import Scapy_Exception
import json
import os
import argparse
from helpers import load_probes

# Read the pcap prefix
parser = argparse.ArgumentParser(description="Parse probe capture")

parser.add_argument(
    "-f", "--file", required=True,
    help="Prefix file containing the PCAP name"
)

args = parser.parse_args()

with open(args.file, "r") as file:
    pcap_file = file.read().rstrip()

file_prefix = os.path.splitext(pcap_file)[0]

print("[*] PCAP file:", pcap_file)
print("[*] JSON output will be:", f"{file_prefix}.json")

# packets = rdpcap("/home/frank/kismet.pcap")
packets = rdpcap(pcap_file)
#packets = PcapNgReader(pcap_file)

results = []

def freq_to_channel(freq):
    if freq is None:
        return None
    if freq == 2484:
        return 14
    if 2412 <= freq <= 2472:
        return (freq - 2407) // 5
    if 5180 <= freq <= 5885:
        return (freq - 5000) // 5
    return None

# Enumerate packets for IDs
for pkt_id, pkt in enumerate(packets):
    try:
        if not pkt.haslayer(Dot11):
            continue
    except Scapy_Exception:
        continue

    dot11 = pkt[Dot11]

    channel = None
    frequency = None
    try:
        if pkt.haslayer(RadioTap):
            frequency = getattr(pkt[RadioTap], "ChannelFrequency", None)
            channel = freq_to_channel(frequency)
    except Exception:
        channel = None

    # Determine MAC randomization note
    src_note = ""
    if dot11.addr2:
        try:
            first_byte = int(dot11.addr2.split(":")[0], 16)
            if first_byte & 0b10:  # locally administered bit
                src_note = "Likely Randomized"
        except ValueError:
            pass

    # SSID extraction
    ssid = "<hidden>"
    if pkt.haslayer(Dot11Elt):
        elt = pkt[Dot11Elt]
        if elt.ID == 0 and elt.info:
            ssid = elt.info.decode(errors="ignore")
            if ssid == "":
                ssid = "<hidden>"

    # Probe request
    if dot11.type == 0 and dot11.subtype == 4:
        results.append({
            "id": pkt_id,
            "frame_type": "probe_request",
            "src": dot11.addr2,
            "src_note": src_note,
            "dst": dot11.addr1,
            "ssid": ssid,
            "timestamp": float(pkt.time),
            "channel": channel
        })

    # Probe response
    elif dot11.type == 0 and dot11.subtype == 5:
        results.append({
            "id": pkt_id,
            "frame_type": "probe_response",
            "src": dot11.addr2,
            "dst": dot11.addr1,
            "ssid": ssid,
            "timestamp": float(pkt.time),
            "channel": channel
        })

# Write JSON file
with open(f"{file_prefix}.json", "w") as f:
    json.dump(results, f, indent=4)

print(f"Extracted {len(results)} probe frames → {file_prefix}.json")




# json_file = f"{file_prefix}.json"
# print(json_file)
# probes = load_probes(json_file)
# print(probes)