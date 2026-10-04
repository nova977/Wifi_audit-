import subprocess
import sys
import os
import argparse
import re
import time


def kill_PID():
    subprocess.run(["sudo", "pkill", "-f", "airodump-ng"])
    subprocess.run(["sudo", "pkill", "-f", "aireplay-ng"])



def convert_to_text(file_cap, new_file):
    if not file_cap or not os.path.isfile(file_cap):
        print("Error: capture file not found.")
        sys.exit(1)
    result = subprocess.run(
    f"sudo aircrack-ng {file_cap} > {new_file} 2>&1",
    shell=True,
    check=True
)
    if result.returncode != 0:
        print("ERROR: aircrack-ng did not run correctly")
        sys.exit(1)
    else:
        print("Aircrack ran correctly")




def main():

    parser = argparse.ArgumentParser(
        description="Handshake detection in a .cap file"
    )
    parser.add_argument(
        "-f", "--file", required=True,
        help=".TXT File containing the prefix of the CAP File containing the handshake"
    )
    parser.add_argument(
        "-d", "--dir", required=True,
        help="The parent dir"
    )

    parser.add_argument(
        "--scan", required=True,
        help="Active Scan + Aireplay running (y/n)"
    )


    args = parser.parse_args()
    if not os.path.exists(args.file):
        sys.exit("Error: prefix file not found")

    filename, file_extension = os.path.splitext(args.file)
    if file_extension == ".cap":
        cap_txt_file = f"{args.file}.txt"
        convert_to_text(file_cap=args.file, new_file=cap_txt_file)
        with open(cap_txt_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        matches = re.findall(r"WPA \((\d+) handshake", content)

        if any(int(m) > 0 for m in matches):
            print("[+] VALID HANDSHAKE DETECTED")
        else:
            print("[+] NO VALID HANDSHAKE FOUND")

        # Cleanup
        if os.path.exists(cap_txt_file):
            os.remove(cap_txt_file)

        exit()

    else:
        pass


    with open(args.file, "r") as f:
        prefix = f.read().strip()

    print("Prefix read:", prefix)

    # ✅ Step 2: Build capture filename
    cap_file = f"/home/frank/pi_pinap/{prefix}-01.cap"
    print(cap_file)

    if not os.path.exists(cap_file):
        sys.exit(f"Error: capture file not found: {cap_file}")

    print("Capture file:", cap_file)

    # ✅ Step 3: Convert to text
    new_file = cap_file + ".txt"
    convert_to_text(cap_file, new_file)

    if args.scan == "n":
    # ✅ Step 4: Detect handshake
        with open(new_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        matches = re.findall(r"WPA \((\d+) handshake", content)

        if any(int(m) > 0 for m in matches):
            print("[+] VALID HANDSHAKE DETECTED")
        else:
            print("[+] NO VALID HANDSHAKE FOUND")

        # Cleanup
        if os.path.exists(new_file):
            os.remove(new_file)

    else:
        handshake = False
        while not handshake:
            # Reconvert updated cap each time
            if os.path.exists(new_file):
                os.remove(new_file)
            convert_to_text(cap_file, new_file)

            # Read new output
            with open(new_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            matches = re.findall(r"WPA \((\d+) handshake", content)

            if any(int(m) > 0 for m in matches):
                print("[+] VALID HANDSHAKE DETECTED")
                print("[+] Killing Airmon & Aireplay Processes...")
                with open(os.path.join(args.dir, "handshake.flag"), "w") as file:
                    file.write("Found")
                kill_PID()
                #sys.exit(0)
                handshake = True

            else:
                print("[+] NO VALID HANDSHAKE FOUND")
                time.sleep(2)


if __name__ == "__main__":
    main()



