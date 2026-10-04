from flask import render_template_string, request, redirect, url_for, flash, jsonify
import os
import ipaddress
import json
from datetime import datetime
import subprocess
from flask import Blueprint, Response, render_template_string
import re
import time



from helpers import (get_nics, get_voltage, run, load_networks, load_scan_time, get_temperature,
                     manage, monitor, kill_PID, load_probes, save_state,
                     load_state, set_state, tool_exist, is_running, stop_capture, load_json,
                     get_band, format_security, group_aps_by_ssid, get_unassociated_clients,
                     get_iface_bands_shell, has_internet, is_ssh_running, get_cpu_ram, check_dependencies, DEPENDENCIES,
                     get_current_channel, set_channel, requires_auth, tail_file, fetch_wifi_data, get_interfaces,
                     has_internet_int, load_wap_config, save_wap_config, convert_to_hostapd_format, get_iface_info,
                     find_dnsmasq_conf, convert_to_dnsmasq_format, check_dnsmasq_syntax,
                     set_state_2, clear_state_2, is_running_2, stop_ap, load_state_2, save_state_2,
                     get_connected_clients, get_dns



                     )

# set_state_2, clear_state_2, is_running_2, stop_capture_2, load_state_2, save_state_2

from templates import (INDEX_TEMPLATE, RECON_TEMPLATE, RECON_2, HANDSHAKE_TEMPLATE, PROBE_TEMPLATE,
                       PROBE_OUTPUT, WIFI_OUTPUT, WIRELESS_LANDSCAPE, BEACON_LAUNCHER,
                       SETTINGS, DISCOVER_TARGET, LOGS, WIFI_LIVE, WAP_TEMPLATE, WAP_STATUS)
from static_css import BASE_CSS



CURRENT_TARGET = None
SCAN_PREFIX = None
SCAN_RUNNING = False
processes = {}
HANDSHAKE_START_TIME = None
capture_process = None
capture_started_at = None
capture_stopped_at = None
PROBE_START_TIME = None
PROBE_STOP_TIME = None
TCPDUMP = False
KISMET = False
HANDSHAKE_FILE = None
HANDSHAKE_PREFIX = None
TARGET = None
SPECIFIC_TARGET_SELECTED = False
RESULTS_W_LANDS = False
last_wap_config = {}


def register(app):

    @app.route("/")
    #@requires_auth
    def index():
        nics = get_nics()
        voltage, undervoltage = get_voltage()
        temperature = get_temperature()
        bands = get_iface_bands_shell()
        ssh_status = is_ssh_running()
        internet = has_internet()
        FLAG_FILE = os.path.join(os.getcwd(),"handshake.flag")
        handshake_found = os.path.exists(FLAG_FILE)


        missing_tools, missing_scripts, tool_pages, script_pages = check_dependencies(DEPENDENCIES)

        return render_template_string(
            INDEX_TEMPLATE,
            css=BASE_CSS,
            nics=nics,
            voltage=voltage,
            undervoltage=undervoltage,
	        temperature=temperature,
            bands=bands,
            missing_tools=missing_tools,
            missing_scripts=missing_scripts,
            handshake_found=handshake_found,
            ssh_status=ssh_status,
            internet=internet,
            tool_pages=tool_pages,
            script_pages=script_pages,
            handshake_name=HANDSHAKE_FILE
        )


    ############## LOGS ############"


    @app.route("/logs/stream")
    def logs_stream():
        return Response(tail_file("flask.log"), mimetype="text/event-stream")

    @app.route("/logs")
    def logs_ui():
        return render_template_string(
            LOGS,
            css=BASE_CSS
        )









    @app.route("/sysinfo")
    def sysinfo_api():
        sys = get_cpu_ram()
        temp = get_temperature()

        return jsonify({
            "cpu": sys["cpu"],
            "ram": sys["ram_percent"],
            "temperature": temp
        })


    @app.route("/settings", methods=["GET", "POST"])
    def settings():
        nics = get_nics()
        bands = get_iface_bands_shell()

        monitor_mode = request.form.get("monitor")
        manage_mode = request.form.get("manage")
        iface = request.form.get("iface")
        change_channel_btn = request.form.get("change_channel")
        new_channel = request.form.get("set_channel")

        # Default interface on GET
        if not iface and nics:
            iface = nics[0]["name"]

        # Attach current channel and available channels to each NIC
        for nic in nics:
            nic_current, nic_available = get_current_channel(nic["name"])
            nic["current_channel"] = nic_current
            nic["available_channels"] = nic_available

        if request.method == "POST":
            if monitor_mode and iface:
                monitor(iface)
                flash(f"{iface} Now in Monitor Mode")

            if manage_mode and iface:
                manage(iface)
                flash(f"{iface} Now in Managed Mode")

            if change_channel_btn and iface and new_channel:
                set_channel(iface, new_channel)
                flash(f"{iface} switched to channel {new_channel}", "success")

            return redirect(url_for("settings"))

        return render_template_string(
            SETTINGS,
            css=BASE_CSS,
            nics=nics,
            bands=bands
        )






    @app.route("/wireless_landscape", methods=["GET", "POST"])
    def wifi_land():
        directory = os.getcwd()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"capture_{timestamp}"
        nics = get_nics()
        state = load_state()
        running = is_running()
        bands = get_iface_bands_shell()# <-- dict like {'phy0': ['2.4', '5.0']}

        if request.method == "POST":
            if "scan" in request.form and not running:
                print('SCAN CLICKED')
                iface = request.form.get("iface")
                if iface:
                    print(f"IFACE selected {iface} ")
                    print("Capabilities", bands[iface])
                    with open("prefix.txt", "w") as f:
                        f.write(f"{filename.strip()}-01.csv")
                    print(filename)
                    if bands[iface] == [2.4]:
                        print(f"Band is {bands[iface]} starting basic airodump capture")
                        p1 = subprocess.Popen(["sudo", "airodump-ng", iface, "-w", filename])
                        set_state("airodump", p1.pid, filename)
                        time.sleep(1)
                        flash(f"Scan started on {iface}", "success")
                        time.sleep(1)
                        return redirect(url_for("wifi_map"))

                    elif set(bands[iface]) == {2.4, 5.0}:
                        p1 = subprocess.Popen(["sudo", "airodump-ng", iface,"-b", "abg", "-w", filename])
                        set_state("airodump", p1.pid, filename)
                        time.sleep(1)
                        flash(f"Scan started on {iface}", "success")
                        time.sleep(1)
                        return redirect(url_for("wifi_map"))

                    elif not bands[iface]:
                        flash(f"No supported bands for {iface}", "error")

        return render_template_string(
            WIRELESS_LANDSCAPE,
            css=BASE_CSS,
            nics=nics,
            bands=bands
        )


################# LIVE OUTPUT TEST ############
    @app.route("/api/wifi_live")
    def api_wifi_live():
        return jsonify(fetch_wifi_data())

    @app.route("/wifi_live")
    def wifi_live_page():
        return render_template_string(WIFI_LIVE, css=BASE_CSS)

##########################################"




    @app.route("/wifi_output", methods=["GET", "POST"])
    def wifi_map():
        global SPECIFIC_TARGET_SELECTED
        global RESULTS_W_LANDS

        running = is_running()
        state = load_state()
        mode = state["mode"]
        print(os.getcwd())
        directory = os.getcwd()

        if os.path.exists(os.path.join(directory,"capture")):
            dir = os.listdir(os.path.join(directory, "capture"))
            if not len(dir) == 0:
                RESULTS_W_LANDS = True
        else:
            RESULTS_W_LANDS = False

        print("STATE OF RESULTS", RESULTS_W_LANDS)


        if os.path.exists("prefix_spec_target.txt"):
            SPECIFIC_TARGET_SELECTED = True
        else:
            SPECIFIC_TARGET_SELECTED = False

        print("SPEC TARGET ST", SPECIFIC_TARGET_SELECTED)

        if not os.path.exists("prefix.txt") and not os.path.exists("prefix_spec_target.txt"):
            return render_template_string(WIFI_OUTPUT, grouped_aps=[], unassociated_clients=[])

        if SPECIFIC_TARGET_SELECTED:
            with open("prefix_spec_target.txt", "r") as file:
                csv_file = file.read().strip()
                json_file = f"{os.path.splitext(csv_file)[0]}.json"
                prefix = os.path.splitext(csv_file)[0]
        else:
            with open("prefix.txt") as file:
                csv_file = file.read().strip()
            json_file = f"{os.path.splitext(csv_file)[0]}.json"
            prefix = os.path.splitext(csv_file)[0]

        if os.path.exists("prefix.txt"):
            with open("prefix.txt", "r") as file:
                content = file.read().strip()
                old_result_prefix = os.path.splitext(content)[0]

        print("CURRENT DATA:",json_file, csv_file, prefix)

        if request.method == "POST":
            if "stop" in request.form:
                stop_capture()
                flash("Capture stopped")
                print("STATE", state)
                return redirect(url_for("wifi_map"))

            # CLEAR button
            if "clear" in request.form and json_file:
                state["mode"] = None
                state["prefix"] = None
                state["json_generated"] = False
                save_state(state)



                if os.path.exists(os.path.join(os.getcwd(), "capture", json_file)):
                    os.remove(os.path.join(os.getcwd(), "capture", json_file))
                try:
                    os.remove(os.path.join(os.getcwd(), f"{old_result_prefix}.cap"))
                    os.remove(os.path.join(os.getcwd(), f"{old_result_prefix}.csv"))
                    os.remove(os.path.join(os.getcwd(), f"{old_result_prefix}.kismet.csv"))
                    os.remove(os.path.join(os.getcwd(), f"{old_result_prefix}.kismet.netxml"))
                    os.remove(os.path.join(os.getcwd(), f"{old_result_prefix}.log.csv"))
                except Exception as e:
                    print(f"Error removing capture files: {e}")

                if SPECIFIC_TARGET_SELECTED:
                    try:
                        os.remove(os.path.join(os.getcwd(), "prefix_spec_target.txt"))
                        os.remove(os.path.join(os.getcwd(), f"{prefix}.cap"))
                        os.remove(os.path.join(os.getcwd(), f"{prefix}.csv"))
                        os.remove(os.path.join(os.getcwd(), f"{prefix}.kismet.csv"))
                        os.remove(os.path.join(os.getcwd(), f"{prefix}.kismet.netxml"))
                        os.remove(os.path.join(os.getcwd(), f"{prefix}.log.csv"))
                    except Exception as e:
                        print(f"Error removing capture files: {e}")

                flash("Networks removed")
                return redirect(url_for("wifi_map"))


        started_at = None
        elapsed_time = "0s"
        if running and state["started_at"]:
            started = datetime.fromisoformat(state["started_at"])
            started_at = started.strftime("%Y-%m-%d %H:%M:%S")

            elapsed_seconds = int((datetime.now() - started).total_seconds())
            mins, secs = divmod(elapsed_seconds, 60)
            elapsed_time = f"{mins}m {secs}s" if mins else f"{secs}s"

        json_path = os.path.join(os.getcwd(), "capture", json_file)
        data = {}
        if mode == "airodump" and running:
            p2 = subprocess.Popen(["sudo", "python3", "airo_csv_parser.py", "-o", json_file, csv_file])


            ######## AIRO_CSV_PARSER writes automatically to /capture #########

        if os.path.exists(json_path):
            data = load_json(json_path)

        # Extract data safely
        aps = data.get("access_points", [])
        grouped_aps = group_aps_by_ssid(aps)
        unassociated_clients = get_unassociated_clients(data)


        # Render page
        return render_template_string(
            WIFI_OUTPUT,
            grouped_aps=grouped_aps,
            unassociated_clients=unassociated_clients,
            BASE_CSS=BASE_CSS,
            get_band=get_band,
            format_security=format_security,
            running=running,
            started_at=started_at,
            elapsed_time=elapsed_time,
            specific_target_selected=SPECIFIC_TARGET_SELECTED,
            results_w_lands=RESULTS_W_LANDS
        )




    @app.route("/discover_target", methods=["GET", "POST"])
    def discover_target():
        global TARGET
        nics = get_nics()
        bands = get_iface_bands_shell()
        state = load_state()
        running = is_running()


        ############# NEW_CAPTURE Files DATE/HOUR UPDATED################"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"capture_{timestamp}"
        print(filename)
        print(f"{filename.strip()}-01.csv") #####CSV file that will be capture
        ####################################################################


        if not os.path.exists("prefix.txt"):
            return render_template_string(WIFI_OUTPUT, grouped_aps=[], unassociated_clients=[])
        with open("prefix.txt") as file:
            csv_file = file.read().strip()
            ##### Reads the old csv file then computes to get the JSON


        ################### OLD CAP FILES USED TO SELECT TARGET DATA != NOW
        json_file = f"{os.path.splitext(csv_file)[0]}.json"
        print(json_file," OLD FILE to select target from")
        json_path = os.path.join(os.getcwd(), "capture", json_file)
        print(json_path)
        prefix = os.path.splitext(csv_file)[0]
        with open(json_path) as f:
            data = json.load(f)
        ##################################################################

        aps = []
        for i, ap in enumerate(data["access_points"]):
            ch = int(ap["channel"])
            freq = 2412 + (ch - 1) * 5

            aps.append({
                "id": i,
                "ssid": ap["essid"],
                "bssid": ap["bssid"],
                "channel": ch,
                "freq": freq,
                "power": ap["power"],
                "security": ap["security"]["privacy"]
            })
        # Handle selection
        if request.method == "POST":

            if "set_target" in request.form:
                ap_id = int(request.form["ap_id"])
                TARGET = aps[ap_id]
                json_str = json.dumps(TARGET, indent=4)
                with open("target2.txt", "w") as f:
                    f.write(json_str)


            #### TARGET Caracteristics for SCAN #########
            ssid = TARGET["ssid"]
            bssid = TARGET["bssid"]
            channel = TARGET["channel"]
            print(ssid, bssid, channel)
            ####################################

            scan = request.form.get("scan")
            if TARGET and scan and not running:
                iface = request.form.get("iface")
                if iface:
                    ########### Write the new file prefix ##############
                    with open("prefix_spec_target.txt", "w") as f:
                        f.write(f"{filename.strip()}-01.csv")
                    print(f"{filename.strip()}-01.csv", "The new filename")
                    ################################################

                    p1 = subprocess.Popen(["sudo", "airodump-ng", "-c", str(channel), "-w", str(filename), "--bssid", str(bssid), iface])
                    set_state("airodump", p1.pid, filename)
                    time.sleep(1)
                    flash(f"Scan started on {iface}", "success")
                    time.sleep(1)
                    return redirect(url_for("wifi_map"))



        return render_template_string(
            DISCOVER_TARGET,
            aps=aps,
            target=TARGET,
            css=BASE_CSS,
            nics=nics,
            bands=bands
        )






    @app.route("/handshake_status")
    def handshake_status():
        global CURRENT_TARGET, HANDSHAKE_START_TIME
        global HANDSHAKE_FILE
        global HANDSHAKE_PREFIX
        FLAG_FILE = "handshake.flag"
        directory = os.getcwd().strip()
        with open(f"{directory}/prefix.txt", "r") as f:
            HANDSHAKE_PREFIX = f"{f.read()}-01"
            cap_file = f"{f.read()}-01.cap"
        full_path_for_cap = os.path.join(os.getcwd(), cap_file)
        HANDSHAKE_FILE = full_path_for_cap
        print("PREFFFFIX", HANDSHAKE_PREFIX)


        handshake_found = os.path.exists(FLAG_FILE)
        pgrep = subprocess.run(["pgrep", "airodump-ng"], capture_output=True, text=True)
        capture_running = bool(pgrep.stdout.strip())

        target_ssid = CURRENT_TARGET["ssid"] if CURRENT_TARGET else None
        target = CURRENT_TARGET

        # Set elapsed time
        if capture_running and not handshake_found:
            if HANDSHAKE_START_TIME is None:
                HANDSHAKE_START_TIME = datetime.now()

            current_time = datetime.now()
            elapsed_seconds = int((current_time - HANDSHAKE_START_TIME).total_seconds())
            hrs = elapsed_seconds // 3600
            mins = (elapsed_seconds % 3600) // 60
            secs = elapsed_seconds % 60
            elapsed_time = f"{hrs}h {mins}m {secs}s" if hrs > 0 else f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
            capture_time = None  # Not captured yet
        else:
            elapsed_time = "0s"
            if handshake_found:
                HANDSHAKE_START_TIME = None
                # Get the timestamp of when handshake was captured
                capture_timestamp = datetime.fromtimestamp(os.path.getmtime(FLAG_FILE))
                capture_time = capture_timestamp.strftime("%Y-%m-%d %H:%M:%S")

                try:
                    os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.csv"))
                    os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.kismet.csv"))
                    os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.kismet.netxml"))
                    os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.log.csv"))
                    os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.cap.txt"))
                except Exception as e:
                    print(f"Error removing capture files: {e}")

            else:
                capture_time = None

        return render_template_string(
            HANDSHAKE_TEMPLATE,
            css=BASE_CSS,
            handshake_found=handshake_found,
            capture_running=capture_running,
            target_ssid=target_ssid,
            elapsed_time=elapsed_time,
            target=target,
            capture_time=capture_time,
            scan_prefix=SCAN_PREFIX,
            cap_file=cap_file,
            full_path_for_cap=full_path_for_cap

        )

    @app.route("/stop_handshake", methods=["POST"])
    def stop_handshake():
        global HANDSHAKE_START_TIME

        kill_PID()  # stop airodump / capture
        HANDSHAKE_START_TIME = None

        FLAG_FILE = "/home/frank/pi_pinap/handshake.flag"
        if os.path.exists(FLAG_FILE):
            os.remove(FLAG_FILE)
        try:
            os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.cap"))
            os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.csv"))
            os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.kismet.csv"))
            os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.kismet.netxml"))
            os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.log.csv"))
            os.remove(os.path.join(os.getcwd(), f"{HANDSHAKE_PREFIX}.cap.txt"))

        except Exception as e:
            print(f"Error removing capture files: {e}")

        return redirect(url_for("handshake_status"))


    @app.template_filter("datetimeformat")
    def datetimeformat(value):
        """Convert unix timestamp → HH:MM:SS"""
        return datetime.fromtimestamp(value).strftime("%H:%M:%S")




    @app.route("/recon", methods=["GET", "POST"])
    def recon():
        global CURRENT_TARGET
        nics = get_nics()
        networks = load_networks()
        scanned_at = load_scan_time()
        bands = get_iface_bands_shell()
        target = None
        if request.method == "POST":
            if "clear" in request.form:
                if os.path.exists("networks.json"):
                    os.remove("networks.json")
                networks = None
                scanned_at = None
                target = None
                CURRENT_TARGET = None


            elif "set_target" in request.form:
                selected_id = int(request.form.get("target_id"))
                target = next((n for n in networks if n["id"] == selected_id), None)
                print(target["bssid"])
                CURRENT_TARGET = target
                print(CURRENT_TARGET)
                json_str = json.dumps(CURRENT_TARGET, indent=4)
                with open("target.txt", "w") as f:
                    f.write(json_str)
                flash(f"Target Selected: {CURRENT_TARGET["ssid"]}")
                #return redirect(url_for("target", target_id=selected_id))


            else:
                iface = request.form.get("iface")
                if iface:
                    flash("[+] Iw Scan Finished")
                    run(f"iw dev {iface} scan > scan.txt")
                    run("python3 parser2.py scan.txt")
                    networks = load_networks()
                    print(networks)
                    scanned_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    #flash("IW Scan started")


        return render_template_string(
            RECON_TEMPLATE,
            css=BASE_CSS,
            nics=nics,
            networks=networks,
            scanned_at=scanned_at,
            target=target,
            bands=bands
        )

    @app.route("/networks")
    def view_json():
        try:
            with open("networks.json") as f:
                data = json.load(f)
        except Exception:
            data = []

        return render_template_string(
            """
            <!doctype html><html><head><title>networks.json</title>{{ css | safe }}</head>
            <body><pre>{{ data | tojson(indent=2) }}</pre></body></html>
            """,
            css=BASE_CSS,
            data=data
        )


    @app.route("/recon_2", methods=["GET", "POST"])
    def recon_2():
        global TARGET
        global SCAN_PREFIX
        scan_running = False
        FLAG_FILE = os.path.join(os.getcwd(), "handshake.flag")
        handshake_found = os.path.exists(FLAG_FILE)
        nics = get_nics()
        bands = get_iface_bands_shell()


        if request.method == "POST":
            iface = request.form.get("iface")
            print("Selected NIC:", iface)
            scan = request.form.get("advanced_scan")
            kill_ps = request.form.get("kill")
            if kill_ps:
                print("Killing Processes clicked")
                run("sudo airmon-ng check kill")


            if scan:
                if os.path.exists(FLAG_FILE):
                    os.remove(FLAG_FILE)

                scan_running = True
                pid1 = subprocess.run(["pgrep", "airodump-ng"], capture_output=True, text=True)
                pid1_output = pid1.stdout.strip()
                print(scan_running)
                print(iface)
                if CURRENT_TARGET:
                    bssid = CURRENT_TARGET["bssid"]
                    channel = CURRENT_TARGET["channel"]
                    essid = CURRENT_TARGET["ssid"]
                    print(bssid, essid, channel)
                elif TARGET:
                    bssid = TARGET["bssid"]
                    channel = TARGET["channel"]
                    essid = TARGET["ssid"]
                    print(bssid, essid, channel)


                p1 = subprocess.Popen([
                    "sudo", "python3", "wpa3.py",
                    "--bssid", str(bssid),
                    "-i", str(iface),
                    "--channel", str(channel),
                    "--essid", str(essid)
                ])

                time.sleep(5)

                p2 = subprocess.Popen([
                    "sudo", "python3", "/home/frank/pi_pinap/Handshake_detection/handshake_detector.py",
                    "-f", os.path.join(os.getcwd(), "prefix.txt"),
                    "--scan", "y", "--dir", os.getcwd()
                ])
                processes["scan"] = p1
                processes["detector"] = p2

                print("Both scripts launched in background!")
                flash("Scan Started...")
                time.sleep(2)

                return redirect(url_for("handshake_status"))


        return render_template_string(
            RECON_2,
            css=BASE_CSS,
            nics=nics,
            target=CURRENT_TARGET,
            target2=TARGET,
            scan_running=scan_running,
            handshake_found=handshake_found,
            bands=bands
        )







    @app.route("/probes_output", methods=["GET", "POST"])
    def render_probes():

        state = load_state()
        capture_running = is_running()
        mode = state["mode"]
        prefix = state["prefix"]

        # ----------------------------
        # FILES
        # ----------------------------
        json_file = None
        if mode == "tcpdump":
            with open("probe_prefix.txt", "r") as f:
                prefix = f.read().strip()
            json_file = f"{os.path.splitext(prefix)[0]}.json"

        if mode == "kismet":
            with open("probe_prefix2.txt", "r") as f:
                prefix = f.read().strip()
            #json_file = f"{os.path.splitext(prefix)[0]}.json"
            json_file = prefix.replace(".pcapng", "").replace(".pcap", "") + ".json"
        # ----------------------------
        # BUTTON HANDLING
        # ----------------------------
        #print(json_file)
        if request.method == "POST":

            # STOP button
            if "stop" in request.form:
                stop_capture()
                flash("Capture stopped")
                print("STATE", state)
                return redirect(url_for("render_probes"))

            # CLEAR button
            if "clear" in request.form and json_file:
                state["mode"] = None
                state["prefix"] = None
                state["json_generated"] = False
                save_state(state)

                cap_of_probes = f"{os.path.splitext(prefix)[0]}.pcap"
                cap_of_probes2 = f"{os.path.splitext(prefix)[0]}.pcapng"
                if os.path.exists(json_file):
                    os.remove(json_file)
                if os.path.exists(cap_of_probes):
                    os.remove(cap_of_probes)
                if os.path.exists(cap_of_probes2):
                    os.remove(cap_of_probes2)
                flash("Probes cleared")
                return redirect(url_for("render_probes"))

        # ----------------------------
        # ELAPSED TIME
        # ----------------------------
        started_at = None
        elapsed_time = "0s"

        print(capture_running, "CAPTURE RUNNING STATE")

        if capture_running and state["started_at"]:
            started = datetime.fromisoformat(state["started_at"])
            started_at = started.strftime("%Y-%m-%d %H:%M:%S")

            elapsed_seconds = int((datetime.now() - started).total_seconds())
            mins, secs = divmod(elapsed_seconds, 60)
            elapsed_time = f"{mins}m {secs}s" if mins else f"{secs}s"


        #if capture_running:
        if mode == "tcpdump" and capture_running:
            subprocess.run([
                "sudo", "python3", "probes_to_json.py",
                "-f", "probe_prefix.txt"
            ])

        elif mode == "kismet" and not capture_running:
            subprocess.run([
                "sudo", "python3", "probes_to_json.py",
                "-f", "probe_prefix2.txt"
            ])


        # ----------------------------
        # ALWAYS LOAD JSON
        # ----------------------------
        probes = load_probes(json_file)

        probe_requests = [p for p in probes if p.get("frame_type") == "probe_request"]
        probe_responses = [p for p in probes if p.get("frame_type") == "probe_response"]

        # probe_requests = probe_requests or []
        # probe_responses = probe_responses or []

        # ----------------------------
        # RENDER
        # ----------------------------
        return render_template_string(
            PROBE_OUTPUT,
            css=BASE_CSS,
            capture_running=capture_running,
            elapsed_time=elapsed_time,
            started_at=started_at,
            probe_requests=probe_requests,
            probe_responses=probe_responses
        )



    @app.route("/probes", methods=["GET", "POST"])
    def probes():

        directory = os.getcwd()
        #file = os.path.join(directory.strip(), "probes")
        file = "probes"
        print(file)
        nics = get_nics()

        state = load_state()
        print(state)
        #clear_state()
        #print(state)
        running = is_running()

        if request.method == "POST":

            # ----------------------------
            # START TCPDUMP
            # ----------------------------
            if "start_tcp" in request.form and not running:
                print("TCPFILE", file)
                iface = request.form.get("iface")
                if iface:
                    p1 = subprocess.Popen([
                        "sudo", "python3", "probe_cap.py",
                        "--file", file,
                        "-i", str(iface)
                    ])

                    set_state("tcpdump", p1.pid, file)
                    flash(f"TCPDUMP capture started on {iface}")

            # ----------------------------
            # START KISMET
            # ----------------------------
            elif "start_kis" in request.form and not running:
                iface = request.form.get("iface")
                if iface:
                     #The issue was an absolute path specified, works with probes not /home/frank/probes
                    p1 = subprocess.Popen([
                             "sudo", "python3", "probe_cap.py",
                             "-f", file,
                             "-i", iface,
                             "-k"])
                    set_state("kismet", p1.pid, file)
                    flash(f"Kismet capture started on {iface}")

            # ----------------------------
            # STOP CAPTURE
            # ----------------------------
            elif "stop" in request.form:
                stop_capture()
                flash("Capture stopped")

            return redirect(url_for("probes"))

        return render_template_string(
            PROBE_TEMPLATE,
            css=BASE_CSS,
            nics=nics,
            running=running,
            mode=state["mode"]
        )


    @app.route("/beacons", methods=["GET", "POST"])
    def beacons():
        nics = get_nics()
        state = load_state()
        running = is_running()
        bands = get_iface_bands_shell()
        stop = request.form.get("stop")
        launch_beacons = request.form.get("launch")



        if request.method == "POST":
            if launch_beacons and not running:
                iface = request.form.get("launch") or request.form.get("iface")
                if iface:
                    print("IFACE", iface)
                    raw = request.form.get("lines", "")
                    file = "ssid.txt"
                    with open(file, "w") as f:
                        f.write(raw)
                    p1 = subprocess.Popen(["sudo", "python3", "beacons.py", "-f", file, "-i", iface])
                    set_state("beacons", p1.pid, file)
                    flash(f"Beacon flood started on {iface}")

            elif stop:
                stop_capture()
                flash("Beacon flood stopped")

            return redirect(url_for("beacons"))

        return render_template_string(
            BEACON_LAUNCHER,
            css=BASE_CSS,
            nics=nics,
            running=running,
            bands=bands,
        )

    # @app.route("/summary", methods=["GET", "POST"])
    # def summary():
    #     files = load_files()







    @app.route("/wap", methods=["GET", "POST"])
    def wap():

        directory = os.getcwd()
        new_dir = "wap"
        state = load_state_2()
        running = is_running_2()
        print(state)
        print(running)

        current_int = None
        mac = None
        ip = None
        hostapd_config_name = None
        interfaces = get_interfaces()
        print(interfaces)
        interfaces = get_interfaces()
        interfaces_with_internet = [i for i in interfaces if
                                    has_internet_int(i, host="1.1.1.1", port=53, timeout=2) == True]

        if not os.path.exists(os.path.join(directory, new_dir)):
            os.mkdir(new_dir)


        new_path = os.path.join(directory, new_dir)
        nics = get_nics()
        bands = get_iface_bands_shell()
        wap_config = load_wap_config(os.path.join(new_path, "wap.json"))
        hostapd_file_exists = False

        dnsmasq_file_exists = False
        dnsmasq_file_name = None
        ######## Check if a dnsmasq config exists ########
        if os.path.exists(os.path.join(new_path, "dnsmasq", "dnsmasq_config_name.txt")):
            with open(os.path.join(new_path, "dnsmasq", "dnsmasq_config_name.txt"), "r") as file:
                configuration_file = file.read().strip()
                if os.path.exists(os.path.join(new_path, "dnsmasq", configuration_file)):
                    dnsmasq_file_exists = True
                    dnsmasq_file_name = (os.path.join(new_path, "dnsmasq", configuration_file))
        ##################################################



        # Get the current NIC in config file to check its IP/MAC
        if wap_config:
            current_int = wap_config["iface"]
            mac, ip = get_iface_info(current_int)
            host_apd_config_file = wap_config["config_name"]
            hostapd_file_exists = os.path.isfile(host_apd_config_file)
            if hostapd_file_exists:
                with open(host_apd_config_file, "r") as f:
                    host_apd_config = f.read()
            else:
                host_apd_config = convert_to_hostapd_format(os.path.join(new_path, "wap.json"))
        else:
            host_apd_config = None



        ### READ Example DNSMASQ conf ###
        dnsmasq_path = find_dnsmasq_conf()
        if dnsmasq_path:
            with open(dnsmasq_path, "r") as f:
                dnsmasq_content = f.read()
        else:
            print("Example config not found")

        ### DISPLAY DNS CONF
        dnsmasq_conf=convert_to_dnsmasq_format(os.path.join(new_path, "wap.json"))

        if request.method == "POST":
            apply = request.form.get("apply")
            clear = request.form.get("delete_json")
            iface = request.form.get("iface")
            set_ip = request.form.get("set_ip")
            set_mac = request.form.get("set_mac")

            write_host_apd_config = request.form.get("write_host_apd_config")
            set_forward = request.form.get("set_forward")
            forwarding_int = request.form.get("forward_iface")
            disable_forwarding = request.form.get("disable_forward")
            write_dnsmasq_config = request.form.get("dnsmasq_config")

            #####START########
            start_ap = request.form.get("start_ap")


            if apply:
                #print(forwarding_int)
                ssid = request.form.get("ssid")
                channel = request.form.get("channel")
                psk = request.form.get("psk")
                security = request.form.get("security")
                hostapd_config_name = request.form.get("config")

                # Do something with the values here
                print(f"SSID={ssid}, Channel={channel}, Security={security}, PSK={psk}")
                new_config = {
                 "iface": iface,
                 "ssid": ssid,
                 "channel": channel,
                 "psk": psk,
                "sec": security,
                "config_name": os.path.join(new_path, hostapd_config_name)
                }
                print(new_config)


                save_wap_config(config_file=os.path.join(new_path, "wap.json"),  config=new_config)
                #test = convert_to_hostapd_format(os.path.join(new_path, "wap.json"))
                flash("Settings applied successfully!")
                return redirect(url_for("wap"))




            elif write_host_apd_config:
                hostapd_config_file_name = wap_config["config_name"]
                with open(hostapd_config_file_name, "w") as f:
                    f.write(write_host_apd_config)
                run(f"sudo dos2unix {hostapd_config_file_name}")
                flash(f"Config sucessfully written to {hostapd_config_file_name}")
                return redirect(url_for("wap"))



            elif write_dnsmasq_config:
                #Make the path
                dir_name = "dnsmasq"
                dnsmasq_dir = os.path.join(new_path, dir_name)
                print("TARGET DIR", dnsmasq_dir)
                #### Create the new dir
                if not os.path.exists(dnsmasq_dir):
                    os.makedirs(dnsmasq_dir, exist_ok=True)

                file = os.path.join(dnsmasq_dir, "tmp_dns_masq_file.conf")
                with open(file, "w") as f:
                    f.write(write_dnsmasq_config)


                dnsmasq_name = request.form.get("dnsmasq_config_name")
                dnsmasq_config_file_name = os.path.join(dnsmasq_dir, dnsmasq_name)
                is_valid, output = check_dnsmasq_syntax(file)

                if is_valid:
                    ####### Write the filename to a file for future use##########
                    contain_dnsmasq_config_name = os.path.join(dnsmasq_dir, "dnsmasq_config_name.txt")
                    with open(contain_dnsmasq_config_name, "w") as f:
                        f.write(dnsmasq_config_file_name)

                    ########### Write the actual config file ###########"
                    with open(dnsmasq_config_file_name, "w") as f:
                        f.write(write_dnsmasq_config)
                    run(f"sudo dos2unix {dnsmasq_config_file_name}")
                    os.remove(file)
                    flash(f"Dnsmasq configuration written successfully to {dnsmasq_config_file_name}")
                    return redirect(url_for("wap"))
                else:
                    print(output)
                    flash(f"Error on dnsmasq {output}")
                    return redirect(url_for("wap"))



            elif clear:
                print("CLEAR CLICKED")

                if os.path.exists(os.path.join(new_path, "wap.json")):
                    os.remove(os.path.join(new_path, "wap.json"))
                hostapd_config_file_name = wap_config["config_name"]

                if os.path.exists(hostapd_config_file_name):
                    os.remove(hostapd_config_file_name)
                if host_apd_config:
                    host_apd_config = ""

            elif set_forward:
                wap_config["forward_iface"] = forwarding_int
                print(forwarding_int)
                print(wap_config["forward_iface"])
                save_wap_config(config_file=os.path.join(new_path, "wap.json"), config=wap_config)

                run("sudo sysctl -w net.ipv4.ip_forward=1")
                run("""echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf""")

                run(f"sudo iptables -t nat -A POSTROUTING -o {forwarding_int} -j MASQUERADE")

                #FIREWALL
                run(f"sudo iptables -A FORWARD -i {wap_config["iface"]} -o {forwarding_int} -j ACCEPT")
                run(f"sudo iptables -A FORWARD -i {forwarding_int} -o {wap_config["iface"]} -m state --state RELATED,ESTABLISHED -j ACCEPT")

                ##DNS
                run(f"iptables -t nat -A PREROUTING -i {wap_config["iface"]} -p udp --dport 53 -j REDIRECT --to-port 53")
                run(f"iptables -t nat -A PREROUTING -i {wap_config["iface"]} -p tcp --dport 53 -j REDIRECT --to-port 53")
                run(f"iptables -A FORWARD -i {wap_config["iface"]} -p tcp --dport 853 -j REJECT")

                flash(f"Enabled traffic forwarding on {forwarding_int}")

            elif disable_forwarding:
                wap_config.pop("forward_iface", None)
                save_wap_config(config_file=os.path.join(new_path, "wap.json"), config=wap_config)
                flash(f"Disabled Forwarding on {forwarding_int}")


            elif set_ip:
                new_ip = request.form.get("assign_ip")
                conflict_iface = None  # ✅ single variable, no all_ips list needed
                for other_int in interfaces:
                    if other_int == current_int:
                        continue
                    _, other_ip = get_iface_info(other_int)
                    if other_ip:
                        try:
                            new_network = ipaddress.ip_interface(new_ip).network
                            other_network = ipaddress.ip_interface(f"{other_ip}/24").network
                            if new_network.overlaps(other_network):
                                conflict_iface = other_int
                                break
                        except ValueError:
                            pass
                if conflict_iface:  # ✅ check the variable set in the loop
                    flash(f"IP address already in use by {conflict_iface}")
                else:
                    run(f"sudo ip link set {current_int} down")
                    run(f"sudo ip addr flush dev {current_int}")
                    run(f"sudo ip addr add {new_ip} dev {current_int}")
                    run(f"sudo ip link set {current_int} up")
                    flash(f"Assigned {new_ip} to {current_int}")

                return redirect(url_for("wap"))


            elif set_mac:
                new_mac = request.form.get("assign_mac")
                if not re.match(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$', new_mac):
                    flash("Invalid MAC address format", "error")
                else:
                    run(f"sudo ip link set {current_int} down")
                    run(f"sudo ip link set {current_int} address {new_mac}")
                    run(f"sudo ip link set {current_int} up")
                    flash(f"Assigned {new_mac} to {current_int}")
                return redirect(url_for("wap"))

            elif start_ap:
                subprocess.Popen(["sudo", "tcpdump", "-i", current_int , "-w", "/home/frank/pi_pinap/wap/dns_capture.pcap", "port", "53"])
                if running:
                    flash("AP already running !", "warning")
                    return redirect(url_for("wap"))
                else:
                    run("sudo systemctl stop dnsmasq")
                    run("sudo systemctl disable dnsmasq")

                    p1 = subprocess.Popen(["sudo", "hostapd", wap_config["config_name"] ])
                    time.sleep(1)
                    if p1.poll() is not None:
                        flash("hostapd failed to start", "danger")
                        clear_state_2()
                        return redirect(url_for("wap"))
                    else:
                        set_state_2("hostapd", p1.pid, wap_config["config_name"])

                    p2 = subprocess.Popen(["sudo", "dnsmasq", "-C", dnsmasq_file_name, "--no-daemon"])
                    time.sleep(1)
                    #dns_sniffer(current_int)
                    if p2.poll() is not None:
                        p1.terminate()
                        flash("dnsmasq failed to start", "danger")
                        clear_state_2()
                        return redirect(url_for("wap"))
                    else:
                        set_state_2("dnsmasq", p2.pid, dnsmasq_file_name)

                    flash(f"AP successfully started on {current_int}")
                    return redirect(url_for("wap"))


                print("START clicked")
                print(dnsmasq_file_name)
                print(current_int)
                print(wap_config["config_name"])
                print(state)



        return render_template_string(
            WAP_TEMPLATE,
            css=BASE_CSS,
            nics=nics,
            bands=bands,
            wap_config=wap_config,
            config=load_wap_config(config_file=os.path.join(new_path, "wap.json")),
            interfaces_with_internet=interfaces_with_internet,
            host_apd_config=host_apd_config,
            mac=mac,
            ip=ip,
            current_int=current_int,
            dnsmasq_content=dnsmasq_content,
            dnsmasq_conf=dnsmasq_conf,
            hostapd_file_exists=hostapd_file_exists,
            dnsmasq_file_exists=dnsmasq_file_exists,
            dnsmasq_file_name=dnsmasq_file_name,
            running=running

        )

    @app.route("/wap_status", methods=["GET", "POST"])
    def wap_status():

        directory = os.getcwd()
        print(directory, "CURRENT DIR")
        state = load_state_2()
        running = is_running_2()
        dns_records = []
        ap_config = None

        ########## Load DNS FILE#######
        json_path = "/home/frank/pi_pinap/wap/dns.json"
        dns_records = []

        # 2. Safely read dns.json if it exists and has data
        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as json_file:
                    dns_records = json.load(json_file)
            except (json.JSONDecodeError, ValueError):
                # If the file is empty or partially written, default to an empty list
                dns_records = []
        ###############################

        ####################################
        # Load AP config
        ####################################

        config_file = os.path.join(directory, "wap", "wap_config.json")

        if os.path.exists(config_file):
            with open(config_file) as f:
                ap_config = json.load(f)

        ####################################
        # Get DHCP clients from dnsmasq leases
        ####################################

        lease_file = "/var/lib/misc/dnsmasq-ap1.leases"

        devices = get_connected_clients(lease_file)
        if len(devices) == 0:
            print("Empty, no clients")
        else:
            print("clients are there")
            get_dns()



        ####################################
        # Render page
        ####################################

        return render_template_string(
            WAP_STATUS,
            running=running,
            ap_config=ap_config,
            devices=devices,
            dns_records=dns_records,
            css = BASE_CSS
        )