from scapy.all import *
from scapy.layers.dot11 import *
import time, argparse, random

def fake_mac():
    return "02:%02x:%02x:%02x:%02x:%02x" % tuple(random.randint(0,255) for _ in range(5))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True)
    parser.add_argument("-i", "--interface", required=True)
    args = parser.parse_args()

    with open(args.file) as f:
        ssids = [l.strip() for l in f if l.strip()]

    frames = []
    for ssid in ssids:
        mac = fake_mac()
        dot11 = Dot11(type=0, subtype=8,
                      addr1="ff:ff:ff:ff:ff:ff",
                      addr2=mac,
                      addr3=mac)
        beacon = Dot11Beacon(cap="ESS")
        essid = Dot11Elt(ID="SSID", info=ssid)
        rates = Dot11Elt(ID="Rates", info=b"\x82\x84\x8b\x96")
        ds = Dot11Elt(ID="DSset", info=chr(1))

        frames.append(RadioTap()/dot11/beacon/essid/rates/ds)

    #iface = "wlan0mon"
    print(f"Broadcasting {len(frames)} SSIDs")

    while True:
        for frame in frames:
            sendp(frame, iface=args.interface, verbose=False)
        time.sleep(0.1)

if __name__ == "__main__":
    main()