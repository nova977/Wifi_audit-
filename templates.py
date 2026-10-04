INDEX_TEMPLATE = """
<!doctype html>
<html>
<head>
  <title>System</title>
  {{ css | safe }}
</head>
<body>

<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>

<!-- LEFT COLUMN -->
<div class="column">

<!-- SYSTEM HEALTH -->
<div class="card">
  <h2>System Health</h>

  <p>
    Voltage: {{ voltage }} V
    {% if undervoltage %}<span class="alert">Undervoltage detected!</span>{% endif %}
  </p>

  <p>
    CPU: <span class="badge managed" id="cpu">--%</span>
    RAM: <span class="badge managed" id="ram">--%</span>
    Temp: <span class="badge managed" id="temp">--°C</span>
  </p>
  <p>
    SSH:
    {% if ssh_status %}
    <span class="badge managed">Running</span>
    {% else %}
    <span class="alert">Stopped</span>
    {% endif %}

    Internet:
    {% if internet %}
    <span class="badge managed">Online</span>
    {% else %}
    <span class="alert">Offline</span>
    {% endif %}
    </p>


  <h3>Available Wireless Adapters</h3>
  {% for nic in nics %}
    <div class="nic">
      <div>
        <strong>{{ nic.name }}</strong><br>
        <span class="muted">{{ nic.chipset }}</span><br>
        {% if bands[nic.name] %}
          <span class="muted">Capabilities: {{ bands[nic.name] | join(", ") }} GHz</span>
        {% else %}
          <span class="muted">Capabilities: unknown</span>
        {% endif %}
      </div>
      <span class="badge {{ nic.mode }}">{{ nic.mode }}</span>
      {% if undervoltage %}<span class="alert">Undervoltage</span>{% endif %}
    </div>
  {% endfor %}
</div>


<!-- REQUIREMENTS STATUS -->
<div class="card">
  <h2>Requirements Status</h2>

  {% if missing_tools|length == 0 and missing_scripts|length == 0 %}
    <span class="badge managed">All requirements satisfied</span>
  {% else %}
    <span class="alert">Missing dependencies detected</span>
  {% endif %}
</div>


<div class="card">
  <h2>Missing Tools</h2>
  {% if missing_tools %}
    {% for tool in missing_tools %}
      <div class="nic">
        <span class="alert">{{ tool }}</span>
        <small>
          Affected pages:
          {{ tool_pages[tool] | join(", ") }}
        </small>
      </div>
    {% endfor %}
  {% else %}
    <span class="badge managed">None</span>
  {% endif %}
</div>


<div class="card">
  <h2>Missing Scripts</h2>
  {% if missing_scripts %}
    {% for script in missing_scripts %}
      <div class="nic">
        <span class="alert">{{ script }}</span>
        <small>
          Affected pages:
          {{ script_pages[script] | join(", ") }}
        </small>
      </div>
    {% endfor %}
  {% else %}
    <span class="badge managed">None</span>
  {% endif %}
</div>

</div>

<!-- RIGHT COLUMN -->
<div class="column">

  <!-- TERMINAL -->
  <div class="card">
    <h2>Terminal</h2>

    <div class="terminal">
      <iframe 
          src="http://localhost:7681"
          style="
            width:100%;
            height:500px;
            border:none;
            border-radius:8px;
          ">
      </iframe>
    </div>
  </div>
  


  <!-- NEW HANDSHAKE STATUS BOX -->
  <div class="card">
    <h2>Handshake Status</h2>
    {% if handshake_found %}
      <span class="badge managed">Handshake detected : ({{ handshake_name }})</span>
    {% else %}
      <span class="alert">No handshake detected on the system</span>
    {% endif %}
  </div>
</div>

</main>

<!-- LIVE SYSTEM INFO UPDATER -->
<script>
function updateSysInfo() {
  fetch("/sysinfo")
    .then(r => r.json())
    .then(d => {
      let cpu = document.getElementById("cpu");
      let ram = document.getElementById("ram");
      let temp = document.getElementById("temp");

      cpu.innerText = d.cpu + "%";
      ram.innerText = d.ram + "%";
      temp.innerText = (d.temperature ?? "--") + "°C";

      // Only alert if temperature is dangerously high
      if (d.temperature !== null && d.temperature > 75) {
        temp.className = "badge alert";
      } else {
        temp.className = "badge managed";
      }
    });
}

setInterval(updateSysInfo, 2000);
updateSysInfo();
</script>

</body>
</html>
"""








SETTINGS = """
<!doctype html>
<html>
<head>
  <title>Recon Settings</title>
  {{ css | safe }}
</head>

<body>

<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
<div class="column">

<!-- FLASH MESSAGES -->
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="alerts">
      {% for category, msg in messages %}
        <div class="alert {{ category }}">{{ msg }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}

<!-- PAGE TITLE CARD -->
<div class="card">
  <h2>NIC Management</h2>
  <p class="muted">Manage modes and channels per wireless interface</p>
</div>

<!-- ONE BOX PER NIC -->
{% if nics and nics|length > 0 %}
  {% for nic in nics %}
  <div class="card">

    <h2>{{ nic.name }}</h2>

    <!-- NIC MODE -->
    <p><strong>Mode:</strong> {{ nic.mode }}</p>

    <!-- Wireless Bands -->
    <p>
      <strong>Frequencies:</strong>
      {% if bands and nic.name in bands and bands[nic.name] %}
        {{ bands[nic.name] | join(", ") }} GHz
      {% else %}
        Unknown
      {% endif %}
    </p>

    <!-- INTERFACE MODE FORM -->
    <form method="post" class="actions">
      <input type="hidden" name="iface" value="{{ nic.name }}">

      <button type="submit" name="monitor" value="{{ nic.name }}"
        class="{% if nic.mode == 'managed' %}blue{% else %}secondary{% endif %}"
        {% if nic.mode == 'monitor' %}disabled{% endif %}>
        Monitor {{ nic.name }}
      </button>

      <button type="submit" name="manage" value="{{ nic.name }}"
        class="{% if nic.mode == 'monitor' %}blue{% else %}secondary{% endif %}"
        {% if nic.mode == 'managed' %}disabled{% endif %}>
        Manage {{ nic.name }}
      </button>
    </form>

    <hr>

    <!-- CHANNEL MANAGEMENT -->
    <h3>Channel Management</h3>

    <!-- Current Channel Display -->
    <div class="current-channel-card">
      <span class="label">Current Channel</span>
      <span class="channel-pill">
        {% if nic.current_channel %}
          {{ nic.current_channel }}
        {% else %}
          Unknown
        {% endif %}
      </span>
    </div>

    {% if nic.available_channels %}
    <form method="post" class="actions">
      <input type="hidden" name="iface" value="{{ nic.name }}">

      <select name="set_channel" required>
        {% for ch in nic.available_channels %}
          <option value="{{ ch }}" {% if ch == nic.current_channel %}selected{% endif %}>
            Channel {{ ch }}
          </option>
        {% endfor %}
      </select>

      <button type="submit" name="change_channel" value="1" class="blue">
        Change Channel
      </button>
    </form>
    {% else %}
      <p class="muted">No channels detected.</p>
    {% endif %}

  </div>
  {% endfor %}
{% else %}
  <div class="card">
    <h2>No Wireless NICs</h2>
    <p class="muted">No wireless interfaces detected on this system.</p>
  </div>
{% endif %}

</div>
</main>

<style>

/* Current channel UI */
.current-channel-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #0b1220;
  border: 1px solid #1f2937;
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 16px;
}

.current-channel-card .label {
  color: #9ca3af;
  font-weight: 500;
}

.channel-pill {
  background: #0f172a;
  border: 1px solid #00ff99;
  color: #00ff99;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 0 0 8px rgba(0, 255, 153, 0.4);
  animation: glow 2s infinite;
}

@keyframes glow {
  0% { box-shadow: 0 0 5px #00ff99; }
  50% { box-shadow: 0 0 15px #00ff99; }
  100% { box-shadow: 0 0 5px #00ff99; }
}

</style>

</body>
</html>
"""






RECON_TEMPLATE = """
<!doctype html>
<html>
<head>
  <title>Recon</title>
  {{ css | safe }}
</head>
<body>

<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2"> Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
  <div class="column">

    <!-- Flash notifications -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="alerts">
          {% for category, msg in messages %}
            <div class="alert {{ category }}">{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <!-- SCAN CARD -->
    <div class="card">
      <h2>Scan</h2>
      <h3>Wireless Capabilities</h3>

      {% if bands %}
        <ul>
        {% for iface, bandlist in bands.items() %}
          <li>
            <b>{{ iface }}</b> :
            {% if bandlist %}
              {{ bandlist | join(", ") }} GHz
            {% else %}
              Unknown
            {% endif %}
          </li>
        {% endfor %}
        </ul>
      {% else %}
        <p class="muted">No wireless PHY detected.</p>
      {% endif %}

      {% if nics %}
      <form method="post" class="actions">

        <select name="iface" required>
          {% for nic in nics %}
            <option value="{{ nic.name }}">{{ nic.name }} ({{ nic.mode }})</option>
          {% endfor %}
        </select>

        {% for nic in nics %}
        <button
            type="submit"
            name="scan"
            value="{{ nic.name }}"
            class="{% if nic.mode == 'managed' %}blue{% else %}secondary{% endif %}"
            {% if nic.mode == 'monitor' %}disabled{% endif %}
        >
            Scan {{ nic.name }}
        </button>
        {% endfor %}

        <button type="submit" name="clear">Clear</button>

        {% if networks %}
        <a href="{{ url_for('view_json') }}">
          <button type="button">View JSON</button>
        </a>
        {% endif %}

      </form>
      {% else %}
        <p class="muted">No wireless interfaces available.</p>
      {% endif %}

      {% if scanned_at %}
        <p class="muted">Scanned at {{ scanned_at }}</p>
      {% endif %}
    </div>

    {% if networks %}

    <!-- TARGET SELECTION CARD -->
    <div class="card">
      <h2>Select Target</h2>

      <form method="post" class="actions">
        <label for="target_id">Choose Network ID:</label>

        <select name="target_id" required>
          {% for net in networks %}
            <option value="{{ net.id }}">
              {{ net.id }} - {{ net.ssid or "<hidden>" }}
            </option>
          {% endfor %}
        </select>

        <button type="submit" name="set_target">Set Target</button>
      </form>

      {% if target %}
      <div style="
          margin-top:1rem;
          padding:1rem;
          border:1px solid #ccc;
          border-radius:12px;
          background:#f9fafb;
      ">
        <h3> Current Target</h3>
        <p><strong>ID:</strong> {{ target.id }}</p>
        <p><strong>SSID:</strong> {{ target.ssid or "<hidden>" }}</p>
        <p><strong>BSSID:</strong> {{ target.bssid }}</p>
        <p><strong>CHANNEL:</strong> {{ target.channel }}</p>
        <p><strong>SECURITY:</strong> {{ target.security }}</p>
      </div>
      {% endif %}
    </div>

    <!-- NETWORK TABLE CARD -->
    <div class="card">
      <h2>Detected Networks</h2>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>BSSID / ESSID</th>
            <th>Signal (dBm)</th>
            <th>Frequency (MHz)</th>
            <th>Channel</th>
            <th>Security</th>
          </tr>
        </thead>

        <tbody>
          {% for net in networks %}
          <tr>
            <td>{{ net.id }}</td>

            <td>
              <strong>{{ net.bssid }}</strong><br>
              <span class="muted">{{ net.ssid or "<hidden>" }}</span>
            </td>

            <td>{{ net.signal_dbm | default("N/A") }} dBm</td>
            <td>{{ net.frequency_mhz | default("N/A") }}</td>
            <td>{{ net.channel | default("N/A") }}</td>
            <td>{{ net.security | default("N/A") }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    {% endif %}

  </div>
</main>

<footer style="position:fixed;bottom:0;width:100%;text-align:center;padding:0.5rem;background:#f8fafc;">
  iw scan → parser2.py → networks.json
</footer>

</body>
</html>
"""











RECON_2 = """
<!doctype html>
<html>
<head>
  <title>Recon</title>
  {{ css | safe }}
  
  {% if scan_running and not handshake_found %}
    <meta http-equiv="refresh" content="2">
    {% endif %}

</head>
<body>
<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2"> Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
  <div class="column">
  
    <!-- Flash notifications -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="alerts">
          {% for category, msg in messages %}
            <div class="alert {{ category }}">{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}
    
    <!-- SCAN CARD -->
    <div class="card">
      <h2>Capture WPA Handshake on Target</h2>
      <h3>Wireless Capabilities</h3>

      {% if bands %}
        <ul>
        {% for iface, bandlist in bands.items() %}
          <li>
            <b>{{ iface }}</b> :
            {% if bandlist %}
              {{ bandlist | join(", ") }} GHz
            {% else %}
              Unknown
            {% endif %}
          </li>
        {% endfor %}
        </ul>
      {% else %}
        <p class="muted">No wireless PHY detected.</p>
      {% endif %}

      {% if nics %}
      <form method="post" class="actions">

        <select name="iface" required>
          {% for nic in nics %}
            <option value="{{ nic.name }}">{{ nic.name }} ({{ nic.mode }})</option>
          {% endfor %}
        </select>

        <!-- Advanced Scan buttons -->
        {% for nic in nics %}
        <button
            type="submit"
            name="advanced_scan"
            value="{{ nic.name }}"
            class="{% if nic.mode == 'monitor' %}blue{% else %}secondary{% endif %}"
            {% if nic.mode == "managed" or scan_running %}disabled{% endif %}
        >
            Capture Handshake {{ nic.name }}
        </button>
        {% endfor %}

         




        {% if networks %}
        <a href="{{ url_for('view_json') }}">
          <button type="button" class="secondary">View JSON</button>
        </a>
        {% endif %}

        <button type="submit" name="kill" value="1">Kill conflicting Processes</button>
      </form>
      {% else %}
        <p class="muted">No NICs found.</p>
      {% endif %}
    </div>
    
    {% if target %}
      <div style="
          margin-top:1rem;
          padding:1rem;
          border:1px solid #ccc;
          border-radius:12px;
          background:#f9fafb;
      ">
        <h3> Current Target</h3>
        <p><strong>ID:</strong> {{ target.id }}</p>
        <p><strong>SSID:</strong> {{ target.ssid or "<hidden>" }}</p>
        <p><strong>BSSID:</strong> {{ target.bssid }}</p>
        <p><strong>CHANNEL:</strong> {{ target.channel }}</p>
        <p><strong>SECURITY:</strong> {{ target.security }}</p>
      </div>
      {% endif %}
    
    {% if target2 %}
      <div style="
          margin-top:1rem;
          padding:1rem;
          border:1px solid #ccc;
          border-radius:12px;
          background:#f9fafb;
      ">
        <h3> Current Target</h3>
        <p><strong>ID:</strong> {{ target2.id }}</p>
        <p><strong>SSID:</strong> {{ target2.ssid or "<hidden>" }}</p>
        <p><strong>BSSID:</strong> {{ target2.bssid }}</p>
        <p><strong>CHANNEL:</strong> {{ target2.channel }}</p>
        <p><strong>SECURITY:</strong> {{ target2.security }}</p>
      </div>
      {% endif %}
    
    
    
    
  </div>
</main>
</body>
</html>
"""





# Handshake Status Template
HANDSHAKE_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Handshake Capture</title>
    {{ css | safe }}

    {% if not handshake_found %}
        <meta http-equiv="refresh" content="3">
    {% endif %}

    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background:#f1f5f9;
            color:#0f172a;
            margin:0;
            display:flex;
        }

        /* Sidebar */
        .sidebar {
            width:240px;
            min-height:100vh;
            background:#0f172a;
            color:white;
            padding:1.5rem;
        }

        .sidebar h2 {
            margin-top:0;
            font-size:1.3rem;
        }

        .sidebar .nav a {
            display:block;
            color:white;
            text-decoration:none;
            margin:0.6rem 0;
            font-weight:500;
        }

        .sidebar .nav a:hover {
            text-decoration:underline;
        }

        /* Main content */
        .main-content {
            flex:1;
            padding:1rem;
            display:flex;
            flex-direction:column;
            align-items:center;
        }

        /* Top horizontal box */
        .top-box {
            width:90%;
            background:#ffffff;
            border:1px solid #cbd5f5;
            border-radius:14px;
            padding:1.5rem 2rem;
            box-shadow:0 8px 20px rgba(0,0,0,0.08);
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:2rem;
        }

        .top-box h2 {
            margin:0;
            color:#1d4ed8;
        }

        .top-box .timer {
            font-weight:600;
            color:#1e40af;
        }

        /* Split container */
        .split-container {
            display:flex;
            gap:2rem;
            width:90%;
        }

        .card-half {
            flex:1;
            background:#ffffff;
            border:1px solid #cbd5f5;
            border-radius:14px;
            padding:2rem;
            box-shadow:0 8px 20px rgba(0,0,0,0.08);
            text-align:center;
        }

        .spinner {
            border:8px solid #f3f3f3;
            border-top:8px solid #2563eb;
            border-radius:50%;
            width:50px;
            height:50px;
            animation:spin 1s linear infinite;
            margin:1rem auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .success {
            color:green;
            font-weight:bold;
            font-size:1.2rem;
            margin-top:1rem;
        }

        .btn-back {
            margin-top:1.5rem;
            display:inline-block;
            padding:0.6rem 1.2rem;
            border-radius:12px;
            background:linear-gradient(135deg,#60a5fa,#2563eb);
            color:white;
            text-decoration:none;
            font-weight:600;
        }

        .btn-stop {
            margin-top:1rem;
            padding:0.6rem 1.4rem;
            border-radius:12px;
            border:none;
            background:linear-gradient(135deg,#f87171,#dc2626);
            color:white;
            font-weight:600;
            cursor:pointer;
        }

        .btn-stop:hover {
            opacity:0.9;
        }

        h3 {
            color:#1d4ed8;
            margin-bottom:1rem;
        }

        .target-info p {
            margin:0.25rem 0;
        }
    </style>
</head>

<body>

    <!-- Sidebar -->
    <div class="sidebar">
        <h2>Navigation</h2>
        <div class="nav">
            <a href="/">Home</a>
            <a href="#">Recon</a>
            <a href="/wireless_landscape">Wireless Landscape</a>
            <a href="/probes">Probes</a>
            <a href="/beacons">Beacon Flood</a>
            <a href="/settings">NIC Settings</a>
            <a href="#">Logs</a>
        </div>
    </div>

    <!-- Main content -->
    <div class="main-content">

        <!-- Top Box -->
        <div class="top-box">
            <h2>Current Handshake Capture</h2>
            <div class="timer">Elapsed: {{ elapsed_time }}</div>
        </div>

        <!-- Split container -->
        <div class="split-container">

            <div class="card-half">
                <h3>Handshake Status for {{ target_ssid or "Unknown Target" }}</h3>

                {% if handshake_found %}
                    <p class="success">✅ Handshake captured!</p>
                    <p>Saved to {{ full_path_for_cap }}</p>
                    {% if capture_time %}
                        <p>Captured at: {{ capture_time }}</p>
                    {% endif %}
                    <a href="{{ url_for('recon_2') }}" class="btn-back">Back to Scan</a>

                {% elif capture_running %}
                    <div class="spinner"></div>
                    <p>Capturing handshake... ⏳</p>

                    <form method="POST" action="{{ url_for('stop_handshake') }}">
                        <button class="btn-stop">⛔ Stop Capture</button>
                    </form>

                {% else %}
                    <p class="no-capture">No capture running</p>
                {% endif %}
            </div>

            <!-- Right Half -->
            <div class="card-half target-info">
                {% if target %}
                    <h3>Current Target</h3>
                    <p><strong>ID:</strong> {{ target.id }}</p>
                    <p><strong>SSID:</strong> {{ target.ssid or "<hidden>" }}</p>
                    <p><strong>BSSID:</strong> {{ target.bssid }}</p>
                    <p><strong>CHANNEL:</strong> {{ target.channel }}</p>
                    <p><strong>SECURITY:</strong> {{ target.security }}</p>
                {% else %}
                    <h3>No Target Selected</h3>
                {% endif %}
            </div>

        </div>
    </div>

</body>
</html>
"""










PROBE_TEMPLATE= """
<!doctype html>
<html>
<head>
  <title>Probe Capture</title>
  {{ css | safe }}
</head>
<body>
<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2"> Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
  <div class="column">

    <!-- Flash notifications -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="alerts">
          {% for category, msg in messages %}
            <div class="alert {{ category }}">{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <div class="card">
      <h2>Probe Capture</h2>

      {% if nics %}
      <form method="post" class="actions">
        <!-- NIC selector -->
        <select name="iface" required class="nic">
          {% for nic in nics %}
            <option value="{{ nic.name }}">{{ nic.name }} ({{ nic.mode }})</option>
          {% endfor %}
        </select>

        <!-- Start/Stop Buttons -->
        <button type="submit" name="start_tcp">Start Capture TCPDUMP</button>
        <button type="submit" name="start_kis">Start Capture KISMET</button>
        <!-- <button type="submit" name="stop" class="secondary">Stop Capture</button> -->

        <!-- View Live Output -->
          <a href="{{ url_for('render_probes') }}">
            <button type="button">View Live Output</button>
          </a>

      </form>
      {% else %}
        <p class="muted">No NICs found.</p>
      {% endif %}
    </div>

  </div>
</main>
</body>
</html>
"""











PROBE_OUTPUT = """
<!doctype html>
<html>
<head>
  <title>Probe Monitor</title>
  {{ css | safe }}

  <!-- Auto refresh every 2s while running -->
  {% if capture_running %}
    <meta http-equiv="refresh" content="2">
  {% endif %}
</head>

<body>
<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2"> Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
  <div class="column">

    <!-- Flash notifications -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="alerts">
          {% for category, msg in messages %}
            <div class="alert {{ category }}">{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <!-- STATUS CARD -->
    <div class="card">
      <h2>Probe Capture Status</h2>

      {% if capture_running %}
        <p>
          <span class="badge monitor">RUNNING</span>
          Capturing probe requests & responses...
        </p>
      {% else %}
        <p>
          <span class="badge managed">STOPPED</span>
          No active probe capture.
        </p>
      {% endif %}

      <p><strong>Started at:</strong> {{ started_at or "—" }}</p>
      <p><strong>Elapsed:</strong> {{ elapsed_time }}</p>

      <!-- ACTION BUTTONS -->
      <form method="post" class="actions">

        {% if capture_running %}
          <button type="submit" name="stop" value="1">
            Stop Capture
          </button>
        {% endif %}

        <button type="submit" name="clear" value="1" class="secondary">
          Clear Probes
        </button>

      </form>
    </div>


    <!-- TABLES ROW -->
    <div style="display:flex; gap:1rem; align-items:flex-start;">

      <!-- PROBE REQUESTS -->
      <div class="card" style="flex:1;">
        <h2>Probe Requests</h2>

        {% if probe_requests %}
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Source</th>
              <th> Random </th>
              <th>Destination</th>
              <th>SSID</th>
              <th>CHANNEL</th>
              <th>Time</th>
            </tr>
          </thead>

          <tbody>
            {% for p in probe_requests %}
            <tr>
  <td>{{ p.id }}</td>

  <td>
    <strong>{{ p.src }}</strong>
  </td>

  <!-- Random column -->
  <td class="src-note">
    {% if p.src_note %}
      {{ p.src_note }}
    {% else %}
      <span class="muted">—</span>
    {% endif %}
  </td>

  <td class="muted">{{ p.dst }}</td>

  <td>
    {% if p.ssid == "<hidden>" %}
      <span class="muted">&lt;hidden&gt;</span>
    {% else %}
      {{ p.ssid }}
    {% endif %}
  </td>

  <td>{{ p.channel }}</td>

  <td class="muted">
    {{ p.timestamp | int | datetimeformat }}
  </td>
</tr>
            {% endfor %}
          </tbody>
        </table>

        {% else %}
          <p class="muted">No probe requests detected yet.</p>
        {% endif %}
      </div>


      <!-- PROBE RESPONSES -->
      <div class="card" style="flex:1;">
        <h2>Probe Responses</h2>

        {% if probe_responses %}
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Source</th>
              <th>Destination</th>
              <th>SSID</th>
              <th>CHANNEL</th>
              <th>Time</th>
            </tr>
          </thead>

          <tbody>
            {% for p in probe_responses %}
            <tr>
              <td>{{ p.id }}</td>

              <td><strong>{{ p.src }}</strong></td>

              <td class="muted">{{ p.dst }}</td>

              <td>
                {% if p.ssid == "<hidden>" %}
                  <span class="muted">&lt;hidden&gt;</span>
                {% else %}
                  {{ p.ssid }}
                {% endif %}
              </td>
              
              <td>{{p.channel}}</td>

              <td class="muted">
                {{ p.timestamp | int | datetimeformat }}
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>

        {% else %}
          <p class="muted">No probe responses detected yet.</p>
        {% endif %}
      </div>

    </div>

  </div>
</main>

</body>
</html>
"""





WIFI_LIVE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Wireless LIVE Landscape</title>

    {{ css | safe }}

    <style>
        .field-label { font-weight: 600; color: #1e3a8a; margin-right: 0.25rem; }
        .field-value { font-weight: 400; color: #0f172a; }
        .title-card { background:#2563eb; color:white; border-radius:14px; padding:1rem 1.25rem; text-align:center; font-size:1.4rem; font-weight:700; margin-bottom:1rem; box-shadow:0 8px 20px rgba(37,99,235,0.25); }
        .band-label { font-weight:600; color:#1e40af; }

        .band-24 { background:#e0f2fe; border-radius:8px; padding:0.5rem 0.8rem; margin-bottom:0.5rem; }
        .band-5 { background:#ede9fe; border-radius:8px; padding:0.5rem 0.8rem; margin-bottom:0.5rem; }

        .live-dot {
            display:inline-block;
            width:10px; height:10px;
            background:#22c55e;
            border-radius:50%;
            animation:pulse 1.5s infinite;
            margin-right:6px;
        }

        @keyframes pulse {
            0% { opacity:1; }
            50% { opacity:0.4; }
            100% { opacity:1; }
        }
    </style>
</head>

<body>

<!-- Sidebar -->
<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
<div class="column">

    <!-- Title -->
    <div class="title-card">
        <span class="live-dot"></span> Wireless LIVE Landscape
    </div>

    <!-- STATUS CARD -->
    <div class="card">
        <h2>Live Capture Status</h2>
        <p><span class="badge monitor">LIVE API</span> Updating every 2 seconds</p>
    </div>

    <!-- LIVE RESULTS -->
    <div id="wifi-container"></div>

</div>
</main>

<script>
async function loadWifi() {
    const res = await fetch("/api/wifi_live");
    const data = await res.json();

    let html = "";

    let index = 1;
    for (const ssid in data.grouped_aps) {
        html += `<div class="card"><h2>${index}. ${ssid}</h2>`;

        data.grouped_aps[ssid].forEach(ap => {
    let bandClass = ap.channel <= 14 ? "band-24" : "band-5";
    let bandLabel = ap.channel <= 14 ? "2.4 GHz" : "5 GHz";

    html += `
    <div class="nic">
        <span>${ap.bssid}</span>
        <span class="badge">${bandLabel}</span>
    </div>

    <div class="${bandClass}">
        <span class="band-label">BAND:</span> ${bandLabel} -
        <span class="field-label">SSID:</span> ${ap.essid} -
        <span class="field-label">Channel:</span> ${ap.channel} -
        <span class="field-label">Security:</span> ${ap.security || "N/A"}
    </div>
    `;

    // Render clients if exist
    if (ap.clients && ap.clients.length > 0) {
        html += `<table>
            <thead>
                <tr><th>Station</th><th>First Seen</th><th>Last Seen</th></tr>
            </thead>
            <tbody>`;
        ap.clients.forEach(client => {
            html += `<tr>
                <td>${client.station}</td>
                <td>${client.first_seen}</td>
                <td>${client.last_seen}</td>
            </tr>`;
        });
        html += `</tbody></table>`;
    } else {
        html += `<p class="muted" style="margin-top:0.3rem;">No clients detected on this band.</p>`;
    }
});

        html += "</div>";
        index++;
    }

    document.getElementById("wifi-container").innerHTML = html;
}

setInterval(loadWifi, 2000);
loadWifi();
</script>

</body>
</html>
"""








WIFI_OUTPUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    {% if running %}
    <meta http-equiv="refresh" content="3">
    {% endif %}
    <meta charset="UTF-8">
    <title>Wireless LANDSCAPE</title>
    {{ BASE_CSS | safe }}
    <style>
        .field-label { font-weight: 600; color: #1e3a8a; margin-right: 0.25rem; }
        .field-value { font-weight: 400; color: #0f172a; }
        .title-card { background:#2563eb; color:white; border-radius:14px; padding:1rem 1.25rem; text-align:center; font-size:1.4rem; font-weight:700; margin-bottom:1rem; box-shadow:0 8px 20px rgba(37,99,235,0.25); }
        .band-label { font-weight:600; color:#1e40af; }

        /* Band alternating colors */
        .band-24 { background:#e0f2fe; border-radius:8px; padding:0.5rem 0.8rem; margin-bottom:0.5rem; }
        .band-5 { background:#ede9fe; border-radius:8px; padding:0.5rem 0.8rem; margin-bottom:0.5rem; }

        /* Unassociated clients table */
        .unassociated-card { margin-top:1.5rem; }
        .unassociated-card h2 { margin-top:0; }
    </style>
</head>
<body>

<!-- Sidebar Navigation -->
<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
  <div class="column">

    <!-- Page Title -->
    <div class="title-card">Wireless LANDSCAPE</div>
    

    <!-- Flash notifications -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="alerts">
          {% for category, msg in messages %}
            <div class="alert {{ category }}">{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <!-- STATUS CARD -->
    <div class="card" style="margin-bottom:1rem;">
        <h2>Capture Status</h2>
        
    {% if specific_target_selected and running %}
    <p>
        <span class="badge monitor">Targetted Scan</span>
        Scan against a Target.
    </p>

{% elif running %}
    <p>
        <span class="badge monitor">Global Scan</span>
        Scan against all networks.
    </p>

{% else %}
    <p>

    </p>
{% endif %}
    

        {% if running %}
            <p>
                <span class="badge monitor">RUNNING</span>
                Wireless scan is active.
            </p>
        {% else %}
            <p>
                <span class="badge managed">STOPPED</span>
                No active scan.
            </p>
        {% endif %}

        <p><strong>Started at:</strong> {{ started_at or "—" }}</p>
        <p><strong>Elapsed:</strong> {{ elapsed_time }}</p>

        <!-- Control Buttons -->
        <form method="POST" style="display:flex; gap:1rem; margin-top:0.5rem;">
        
            {% if running %}
                <button type="submit" name="stop" class="btn btn-danger">Stop Capture</button>
            {% endif %}
            <button type="submit" name="clear" class="btn btn-warning">Clear Results</button>
            
            
        <!-- LIVE POLL JS -->
        {% if running %}
        <a href="{{ url_for('wifi_live_page') }}">
          <button type="button">LIVE OUTPUT</button>
        </a>
        {% endif %}
        
        <!-- FOCUS TARGET IF RESULTS EXIST -->    
        
            {% if results_w_lands and not running %}

        <a href="{{ url_for('discover_target') }}">
          <button type="button">Focus Target</button>
        </a>
{% else %}
<button class="secondary" disabled>Focus Target</button>
{% endif %}
        </form>
    </div>

    <!-- Access Points Cards -->
    {% set ap_index = 1 %}
    {% for ssid, aps in grouped_aps.items() %}
    <div class="card">
        <h2>{{ ap_index }}. {% if ssid == "<hidden>" %}<span style="color:#2563eb;">&lt;hidden&gt;</span>{% else %}{{ ssid }}{% endif %}</h2>

        {% for ap in aps|sort(attribute='channel') %}
        <div class="nic" style="margin-bottom:0.5rem;">
            <span>{{ ap.bssid }}</span>
            <span class="badge">{{ get_band(ap.channel) }}</span>
        </div>
        <div class="{% if get_band(ap.channel) == '2.4 GHz' %}band-24{% else %}band-5{% endif %}">
            <span class="band-label">BAND:</span> {{ get_band(ap.channel) }} - 
            <span class="field-label">SSID:</span> {% if ap.essid == "<hidden>" %}<span style="color:#2563eb;">&lt;hidden&gt;</span>{% else %}{{ ap.essid }}{% endif %}, 
            <span class="field-label">First Seen:</span> <span class="field-value">{{ ap.first_seen }}</span>, 
            <span class="field-label">Last Seen:</span> <span class="field-value">{{ ap.last_seen }}</span>, 
            <span class="field-label">Channel:</span> <span class="field-value">{{ ap.channel }}</span>, 
            <span class="field-label">Security:</span> <span class="field-value">{{ format_security(ap.security) }}</span>

            <!-- Clients Table -->
            {% if ap.clients %}
            <table>
                <thead>
                    <tr><th>Station</th><th>First Seen</th><th>Last Seen</th></tr>
                </thead>
                <tbody>
                    {% for client in ap.clients %}
                    <tr>
                        <td>{{ client.station }}</td>
                        <td>{{ client.first_seen }}</td>
                        <td>{{ client.last_seen }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p class="muted" style="margin-top:0.3rem;">No clients detected on this band.</p>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% set ap_index = ap_index + 1 %}
    {% endfor %}

    <!-- Unassociated Clients -->
    <div class="card unassociated-card">
        <h2>Unassociated Clients</h2>
        {% if unassociated_clients %}
        <table>
            <thead>
                <tr><th>Station</th><th>First Seen</th><th>Last Seen</th></tr>
            </thead>
            <tbody>
                {% for client in unassociated_clients %}
                <tr>
                    <td>{{ client.station }}</td>
                    <td>{{ client.first_seen }}</td>
                    <td>{{ client.last_seen }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p class="muted">No unassociated clients detected.</p>
        {% endif %}
    </div>

  </div>
</main>

</body>
</html>
"""






WIRELESS_LANDSCAPE = """
<!doctype html>
<html>
<head>
  <title>Wireless Landscape</title>
  {{ css | safe }}
</head>

<body>

<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main style="padding-bottom: 4rem;">
<div class="column">

{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="alerts">
      {% for category, msg in messages %}
        <div class="alert {{ category }}">{{ msg }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}

<!-- PAGE TITLE CARD -->
<div class="card">
  <h2>Wireless Landscape</h2>
  <p class="muted">Detected wireless interfaces and RF capabilities</p>
</div>

<!-- ONE CARD PER NIC -->
{% if nics and nics|length > 0 %}
  {% for nic in nics %}
  <div class="card">

    <h2>{{ nic.name }}</h2>

    <p><strong>Mode:</strong> {{ nic.mode }}</p>

    <p>
      <strong>Frequencies:</strong>
      {% if bands and nic.name in bands and bands[nic.name] %}
        {{ bands[nic.name] | join(", ") }} GHz
      {% else %}
        Unknown
      {% endif %}
    </p>

    {% if nic.frequency %}
      <p><strong>Current Frequency:</strong> {{ nic.frequency }} MHz</p>
    {% endif %}

    <form method="post" class="actions">
      <input type="hidden" name="iface" value="{{ nic.name }}">

      <button
        type="submit"
        name="scan"
        value="{{ nic.name }}"
        class="{% if nic.mode == 'monitor' %}blue{% else %}secondary{% endif %}"
        {% if nic.mode == 'managed' %}disabled{% endif %}
      >
        Scan {{ nic.name }}
      </button>
      
      
      

    </form>

  </div>
  {% endfor %}

{% else %}
  <!-- NO NICs -->
  <div class="card">
    <h2>No Wireless NICs</h2>
    <p class="muted">No wireless interfaces detected on this system.</p>
  </div>
{% endif %}

</div>
</main>

<footer style="position:fixed;bottom:0;width:100%;text-align:center;padding:0.5rem;background:#f8fafc;">
  Wireless Landscape Monitor
</footer>

</body>
</html>
"""






DISCOVER_TARGET = """
<!doctype html>
<html>
<head>
  <title>Discover Target</title>
  {{ css | safe }}
  <style>
    html, body { height: 100%; margin: 0; }
    body { display: flex; flex-direction: row; font-family: sans-serif; }
    .sidebar {
      width: 220px; background: #f0f2f5; padding: 1rem; height: 100vh;
      box-sizing: border-box; position: fixed; overflow-y: auto;
    }
    main {
      margin-left: 220px; flex: 1; display: flex; flex-direction: column;
      min-height: 100vh; padding: 1rem; box-sizing: border-box;
    }
    .column { flex: 1; }
    footer {
      padding: 0.5rem; text-align: center; background: #f8fafc;
      border-top: 1px solid #ddd; margin-top: 1rem;
    }
    table { width: 100%; border-collapse: collapse; }
    table th, table td { border: 1px solid #ccc; padding: 0.5rem; text-align: left; }
    .card {
      margin-bottom: 1.5rem; padding: 1rem; border-radius: 12px;
      background: #fff; box-shadow: 0 0 5px rgba(0,0,0,0.05);
    }
    .muted { color: #666; }
    .alerts { margin-bottom: 1rem; }
    .alert {
      padding: 0.5rem; margin-bottom: 0.5rem; border-radius: 6px;
      background: #fdecea; color: #611a15;
    }
  </style>
</head>

<body>

<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
  <div class="column">

    <!-- Flash notifications -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="alerts">
          {% for category, msg in messages %}
            <div class="alert {{ category }}">{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <!-- WIRELESS NICs -->

    {% if nics and nics|length > 0 %}
      {% for nic in nics %}
        <div class="card">
          <h2>{{ nic.name }}</h2>
          <p><strong>Mode:</strong> {{ nic.mode }}</p>
          <p>
            <strong>Frequencies:</strong>
            {% if bands and nic.name in bands and bands[nic.name] %}
              {{ bands[nic.name] | join(", ") }} GHz
            {% else %}
              Unknown
            {% endif %}
          </p>
          {% if nic.frequency %}
            <p><strong>Current Frequency:</strong> {{ nic.frequency }} MHz</p>
          {% endif %}

          <form method="post" class="actions">
            <input type="hidden" name="iface" value="{{ nic.name }}">
            <button
              type="submit"
              name="scan"
              value="{{ nic.name }}"
              class="{% if nic.mode == 'monitor' %}blue{% else %}secondary{% endif %}"
              {% if nic.mode == 'managed' %}disabled{% endif %}
            >
              Scan {{ target.ssid }} <!-- ---MIGHT FLOP ----------------------------- -->
            </button>
          </form>
        </div>
      {% endfor %}
    {% else %}
      <div class="card">
        <h2>No Wireless NICs</h2>
        <p class="muted">No wireless interfaces detected on this system.</p>
      </div>
    {% endif %}

    <!-- ACCESS POINTS -->
    {% if aps %}
      <!-- TARGET SELECTION CARD -->
      <div class="card">
        <h2>Select Target</h2>
        <form method="post" class="actions">
          <label for="ap_id">Choose Network:</label>
          <select name="ap_id" required>
            {% for ap in aps %}
              <option value="{{ ap.id }}">
                {{ ap.ssid or "<hidden>" }} - {{ ap.channel }}
              </option>
            {% endfor %}
          </select>
          <button type="submit" name="set_target">Set Target</button>
        </form>

        {% if target %}
          <div style="
              margin-top:1rem;
              padding:1rem;
              border:1px solid #ccc;
              border-radius:12px;
              background:#f9fafb;
          ">
            <h3> Current Target</h3>
            <p><strong>BSSID:</strong> {{ target.bssid }}</p>
            <p><strong>ESSID:</strong> {{ target.ssid or "<hidden>" }}</p>
            <p><strong>CHANNEL:</strong> {{ target.channel }}</p>
            <p><strong>FREQ:</strong> {{ target.freq }} MHz</p>
            <p><strong>POWER:</strong> {{ target.power }} dBm</p>
            <p><strong>SECURITY:</strong> {{ target.security or "Unknown" }}</p>
          </div>
        {% endif %}
      </div>

      <!-- NETWORK TABLE CARD -->
      <div class="card">
        <h2>Detected Networks</h2>
        <table>
          <thead>
            <tr>
              <th>BSSID</th>
              <th>ESSID</th>
              <th>Channel</th>
              <th>Frequency (MHz)</th>
              <th>Power (dBm)</th>
              <th>Security</th>
            </tr>
          </thead>
          <tbody>
            {% for ap in aps %}
              <tr {% if target and ap.id == target.id %}style="background:#e0f7fa;"{% endif %}>
                <td><strong>{{ ap.bssid }}</strong></td>
                <td><span class="muted">{{ ap.ssid or "<hidden>" }}</span></td>
                <td>{{ ap.channel }}</td>
                <td>{{ ap.freq }}</td>
                <td>{{ ap.power }}</td>
                <td>{{ ap.security or "Unknown" }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% else %}
      <p class="muted">No access points detected.</p>
    {% endif %}

  </div>

  <footer>
    JSON → Target Selection
  </footer>

</main>
</body>
</html>
"""










BEACON_LAUNCHER = """
<!doctype html>
<html>
<head>
  <title>Line Launcher</title>
  {{ css | safe }}
</head>  
<body>

<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
  <div class="column">

    <!-- Flash notifications -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="alerts">
          {% for category, msg in messages %}
            <div class="alert {{ category }}">{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <!-- SCAN CARD -->
    <div class="card">
      <h2>Beacon Flood</h2>
      <h3>Wireless Capabilities</h3>

      {% if bands %}
        <ul>
        {% for iface, bandlist in bands.items() %}
          <li>
            <b>{{ iface }}</b> :
            {% if bandlist %}
              {{ bandlist | join(", ") }} GHz
            {% else %}
              Unknown
            {% endif %}
          </li>
        {% endfor %}
        </ul>
      {% else %}
        <p class="muted">No wireless PHY detected.</p>
      {% endif %}

      {% if nics %}
      <form method="post" class="actions">
        <select name="iface" required>
          {% for nic in nics %}
            <option value="{{ nic.name }}">{{ nic.name }} ({{ nic.mode }})</option>
          {% endfor %}
        </select>
      <!--</form>-->
      {% else %}
        <p class="muted">No wireless interfaces available.</p>
      {% endif %}


        </form>
    </div>

    <!-- LINE INPUT CARD -->
    <div class="card">
      <h2>SSIDs</h2>
      <p class="muted">Write one SSID per line (example: <code>line(1): Hello</code>)</p>

      <form method="post" class="actions">

        <textarea name="lines" rows="8" style="width:100%; font-family:monospace;" placeholder="SSID(1): Livebox-XXXX
SSID(2): Freebox
SSID(3): Test"></textarea>


        {% for nic in nics %}
        <button
            type="submit"
            name="launch"
            value="{{ nic.name }}"
            class="{% if nic.mode == 'monitor' %}blue{% else %}secondary{% endif %}"
            {% if nic.mode == "managed" %}disabled{% endif %}
        >
            Launch {{ nic.name }}
        </button>

        <button
            type="submit"
            name="stop"
            value="{{ nic.name }}"
            class="{% if running %}blue{% else %}secondary{% endif %}"
            {% if not running %}disabled{% endif %}
        >
            STOP Beacons
        </button>
        {% endfor %}

      </form>
    </div>

  </div>
</main>

</body>
</html>
"""





LOGS = """
<!doctype html>
<html>
<head>
  <title>Flask Logs</title>
  {{ css | safe }}
  <style>
    /* Match your site’s card style */
    main {
      padding-bottom: 4rem;
    }
    .column {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .card {
      background: #fff;
      border-radius: 8px;
      padding: 1rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th, td {
      padding: 0.5rem;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    th {
      background-color: #f0f0f0;
    }
    .log-info { color: green; }
    .log-warning { color: orange; }
    .log-error { color: red; }
    .sidebar a.active { font-weight: bold; }
  </style>
</head>

<body>

<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="/logs" class="active">Logs</a>
  </div>
</div>

<main>
<div class="column">

<!-- PAGE TITLE CARD -->
<div class="card">
  <h2>Live Flask Logs</h2>
  <p class="muted">Streaming live logs from Flask/Werkzeug server</p>
</div>

<!-- LOGS TABLE -->
<div class="card">
  <table>
    <thead>
      <tr>
        <th>Date / Time</th>
        <th>Level</th>
        <th>Message</th>
      </tr>
    </thead>
    <tbody id="log-table">
      <!-- Logs will appear here -->
    </tbody>
  </table>
</div>

</div>
</main>

<footer style="position:fixed;bottom:0;width:100%;text-align:center;padding:0.5rem;background:#f8fafc;">
  Flask Log Monitor
</footer>

<script>
const logTable = document.getElementById("log-table");
const es = new EventSource("/logs/stream");

es.onmessage = e => {
    // Parse log line assuming format: "YYYY-MM-DD HH:MM:SS | LEVEL | Message"
    const parts = e.data.split(" | ");
    const date = parts[0] || "";
    const level = parts[1] || "";
    const message = parts.slice(2).join(" | ") || "";

    // Map log level to CSS class
    let cls = "";
    if(level.toLowerCase().includes("error")) cls = "log-error";
    else if(level.toLowerCase().includes("warning")) cls = "log-warning";
    else cls = "log-info";

    const row = document.createElement("tr");
    row.innerHTML = `<td>${date}</td><td class="${cls}">${level}</td><td>${message}</td>`;
    logTable.appendChild(row);

    // Auto-scroll
    row.scrollIntoView({behavior: "smooth", block: "end"});
};
</script>

</body>
</html>
"""







WAP_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>WiFi Settings</title>
  {{ css | safe }}
  <style>
    .two-col {
      display: flex;
      gap: 16px;
      margin-top: 16px;
      align-items: flex-start;
    }
    .two-col > .card {
      flex: 1;
    }
    .nic-info {
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
    }
    .nic-info div {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .nic-info span.label {
      font-size: 0.75em;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      opacity: 0.6;
    }
    .nic-info span.value {
      font-family: monospace;
      font-size: 1em;
      font-weight: bold;
    }
    @media (max-width: 768px) {
      .two-col {
        flex-direction: column;
      }
    }
  </style>
</head>
<body>
<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>
<div class="main">
  <h2>WiFi Settings</h2>
  
  {% if running %}
<div style="
  background: #2ecc71;
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-weight: bold;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
">
  <span>🟢 Access Point is running</span>

  <a href="/wap_status" style="
    background: white;
    color: #2ecc71;
    padding: 6px 12px;
    border-radius: 6px;
    text-decoration: none;
    font-size: 0.85em;
    font-weight: bold;
  ">
    View Status
  </a>
</div>
{% endif %}

  
   <!-- Flash notifications -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="alerts">
          {% for category, msg in messages %}
            <div class="alert {{ category }}">{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}
  
  
  {% if nics %}
  
  <form method="POST">
    <div class="card" style="display:flex; align-items:flex-end; gap:16px; flex-wrap:wrap;">
      <label>Interface
        <select name="iface" required>
          {% for nic in nics %}
            <option value="{{ nic.name }}">{{ nic.name }} ({{ nic.mode }})
            {% if bands.get(nic.name) %}
            — {{ bands[nic.name] | join(", ") }} GHz
                {% endif %}
            </option>
          {% endfor %}
        </select>
      </label>
      <label>SSID
        <input type="text" name="ssid" required>
      </label>
      <label>Channel
        <input type="number" name="channel" min="1" max="14" required>
      </label>
      <label>Security
        <select name="security">
          <option value="none">None</option>
          <option value="wpa2">WPA2</option>
          <option value="wpa3">WPA3</option>
        </select>
      </label>
      <label>PSK
        <input type="text" name="psk">
      </label>
      <label>Config name .conf
        <input type="text" name="config" required>   
      </label>
      <button type="submit" name="apply" value="1">Apply Settings</button>
    </div>
  </form>
  {% else %}
    <p class="muted">No wireless interfaces available.</p>
  {% endif %}

 <!-- Two column layout -->
  <div class="two-col">
    {% if config %}
    <div class="card">
    <h3>Current Config </h3>
    
      <table>
        <tr><td><b>Interface</b></td><td>{{ config.get("iface", "-") }}</td></tr>
        <tr><td><b>SSID</b></td><td>{{ config.get("ssid", "-") }}</td></tr>
        <tr><td><b>Channel</b></td><td>{{ config.get("channel", "-") }}</td></tr>
        <tr><td><b>Security</b></td><td>{{ config.get("sec", "-") }}</td></tr>
        <tr><td><b>PSK</b></td><td>{{ config.get("psk", "-") }}</td></tr>
        <tr><td><b>Forward Interface</b></td><td>{{ config.get("forward_iface", "-") }}</td></tr>
      </table>
      <form method="POST">
      <button type="submit" name="delete_json" value="1"> Delete Config</button>
      </form>
    </div>
    {% endif %}
    
        
    {% if host_apd_config %}
<div class="card">
  <h3>Hostapd Config Preview: {{ config.get("config_name", "-") }}</h3>
  
  <form method="POST">
    <textarea 
  name="write_host_apd_config"
  style="white-space: pre-wrap; font-family: monospace; font-size: 0.9em; width: 100%;"
  rows="20">{{ host_apd_config }}</textarea>

    <button type="submit" name="submit_host_ap_conf" value="1">Write Hostapd Config</button>
  </form>
</div>
{% else %}
  <p>No current Config file</p>
{% endif %}
  
</div>

  <!-- NIC Info Box -->
  
  {% if current_int %}
  <div class="card" style="margin-top:16px;">
    <h3>📡 Active Interface</h3>
    <div style="display:flex; align-items:flex-end; gap:24px; flex-wrap:wrap;">
      <div class="nic-info">
        <div>
          <span class="label">Interface</span>
          <span class="value">{{ current_int }}</span>
        </div>
        <div>
          <span class="label">MAC Address</span>
          <span class="value">{{ mac if mac else "—" }}</span>
        </div>
        <div>
          <span class="label">IP Address</span>
          <span class="value">{{ ip if ip else "Not assigned" }}</span>
        </div>
      </div>
      <form method="POST" style="display:flex; align-items:flex-end; gap:8px; flex-wrap:wrap;">
        <label>
          <span class="label">Assign IP</span>
          {% if ip %}
          <input type="text" name="assign_ip" value="{{ ip ~ '/24' }}" style="font-family:monospace;">
          {% else %}
          <input type="text" name="assign_ip" value="192.168.50.1/24" style="font-family:monospace;">
        </label>
        {% endif %}
        <button type="submit" name="set_ip" value="1">Assign IP</button>
        
        <span class="label">Assign MAC</span>
          <input type="text" name="assign_mac" value="{{mac}}" style="font-family:monospace;">
        </label>
        <button type="submit" name="set_mac" value="1">Assign MAC</button>
      </form>
    </div>
  </div>
  {% endif %}

  <!-- Forward Traffic Card -->
  <div class="card" style="margin-top:16px;">
    <h3> Forward Traffic</h3>
    <p class="muted" style="margin-bottom:12px;">Select an interface with internet access to forward AP traffic through.</p>
    {% if interfaces_with_internet %}
    <form method="POST">
      <div style="display:flex; align-items:flex-end; gap:16px; flex-wrap:wrap;">
        <label>Uplink Interface
          <select name="forward_iface" required>
            {% for iface in interfaces_with_internet %}
              <option value="{{ iface }}" {% if current_forward == iface %}selected{% endif %}>
                {{ iface }}
              </option>
            {% endfor %}
          </select>
        </label>
        <button type="submit" name="set_forward" value="1">Apply Forwarding</button>
        <button type="submit" name="disable_forward" value="2">Disable Forwarding</button>
      </div>
    </form>
    {% else %}
      <p class="muted">⚠️ No interfaces with internet connectivity found.</p>
    {% endif %}
  </div>
  
  <div style="display:flex; gap:16px; margin-top:16px;">
  
  <!-- Left Box - Dnsmasq Config -->
  <div class="card" style="flex:1;">
    <h3>Example Dnsmasq Config</h3>
    <form method="POST">
      <textarea readonly name="hostapd_raw" 
                style="width:100%; min-height:80vh; font-family:monospace; font-size:0.9em; 
                       background:#1e1e1e; color:#d4d4d4; border:1px solid #444; 
                       border-radius:4px; padding:12px; box-sizing:border-box; resize:vertical;">{{ dnsmasq_content }}</textarea>
    </form>
  </div>

  <!-- Right Box -->
  <div class="card" style="flex:1;">
    <h3>Edit Dnsmasq config</h3>
    <form method="POST">
      <textarea name="dnsmasq_config" 
                style="width:100%; min-height:80vh; font-family:monospace; font-size:0.9em; 
                       background:#1e1e1e; color:#d4d4d4; border:1px solid #444; 
                       border-radius:4px; padding:12px; box-sizing:border-box; resize:vertical;">{{ dnsmasq_conf }}</textarea>
    <label>Dnsmasq config file name .conf
    <input type="text" name="dnsmasq_config_name" required>
    </label>
      <button type="submit" name="save_right_box" value="1" style="margin-top:8px;">Write dnsmasq config</button>
    </form>
    <form method="POST"> 
    </form>
  </div>

</div>

  
  
  <!-- Start the AP -->
<div class="card" style="margin-top:16px;">
  <h3>🚀 Start Access Point</h3>

  <p class="muted" style="margin-bottom:12px;">
    Launch the wireless access point using the current <b>hostapd</b> and <b>dnsmasq</b> configurations.
  </p>

  <!-- Status / checklist -->
  <div style="display:flex; gap:16px; flex-wrap:wrap; margin-bottom:16px;">
    
    <div style="flex:1; min-width:200px; background:#ffffff; padding:14px; border-radius:8px; border:1px solid #ddd; box-shadow:0 2px 6px rgba(0,0,0,0.2);">
  <span class="label" style="color:#666;">Hostapd Config</span>
  <div class="value" style="margin-top:6px; color:#111;">
  
    {% if hostapd_file_exists %}
      <span class="badge managed">Hostapd Ready</span>
      <span class="badge managed">{{ config.get("config_name", "-") }}<span>
    {% else %}
      <span class="alert">Hostapd Missing: Generate config !</span>
    {% endif %}
  </div>
</div>

    <div style="flex:1; min-width:200px; background:#ffffff; padding:14px; border-radius:8px; border:1px solid #ddd; box-shadow:0 2px 6px rgba(0,0,0,0.2);">
  <span class="label" style="color:#666;">Dnsmasq Config</span>
  <div class="value" style="margin-top:6px; color:#111;">
    {% if dnsmasq_file_exists %}
      <span class="badge managed">Dnsmasq Ready</span>
      <span class="badge managed">{{dnsmasq_file_name}}</span>
    {% else %}
      <span class="alert">DnsMasq Missing: Generate config !</span>
    {% endif %}
  </div>
</div>

<div style="flex:1; min-width:200px; background:#ffffff; padding:14px; border-radius:8px; border:1px solid #ddd; box-shadow:0 2px 6px rgba(0,0,0,0.2);">
  <span class="label" style="color:#666;">Card Config</span>
  <div class="value" style="margin-top:6px; color:#111;">
  
    {% if current_int and ip %}
      <span class="badge managed">NIC ready on {{ ip }}</span>
    {% else %}
      <span class="alert">No IP configured on NIC</span>
    {% endif %}
  </div>
</div>

    <div style="flex:1; min-width:200px; background:#ffffff; padding:14px; border-radius:8px; border:1px solid #ddd; box-shadow:0 2px 6px rgba(0,0,0,0.2);">
  <span class="label" style="color:#666;">Interface</span>
  <div class="value" style="margin-top:6px; color:#111; font-weight:bold;">
    {{ current_int if current_int else "Not selected" }}
  </div>
</div>

  <!-- Action buttons -->
  <form method="POST" style="display:flex; gap:12px; flex-wrap:wrap; align-items:center;">
    
    <button type="submit" name="start_ap" value="1"
      style="padding:10px 18px; font-weight:bold; font-size:0.95em;">
      ▶ Start AP
    </button>

    <button type="submit" name="stop_ap" value="1"
      style="padding:10px 18px; font-size:0.9em; opacity:0.8;">
      ■ Stop
    </button>

  </form>

  <!-- Hint -->
  <p class="muted" style="margin-top:12px; font-size:0.85em;">
    Make sure the interface is in <b>AP mode</b> and IP/forwarding are configured.
  </p>
</div>
  

</div>
</body>
</html>
"""




WAP_STATUS = """
<!doctype html>
<html>
<head>
  <title>WAP Status & DNS Traffic</title>
  {{ css | safe }}
  <style>
    html, body { height: 100%; margin: 0; }
    body { display: flex; flex-direction: row; font-family: sans-serif; }
    .sidebar {
      width: 220px; background: #f0f2f5; padding: 1rem; height: 100vh;
      box-sizing: border-box; position: fixed; overflow-y: auto;
    }
    main {
      margin-left: 220px; flex: 1; display: flex; flex-direction: column;
      min-height: 100vh; padding: 1rem; box-sizing: border-box;
    }
    .column { flex: 1; }
    footer {
      padding: 0.5rem; text-align: center; background: #f8fafc;
      border-top: 1px solid #ddd; margin-top: 1rem;
    }
    table { width: 100%; border-collapse: collapse; }
    table th, table td { border: 1px solid #ccc; padding: 0.5rem; text-align: left; }
    .card {
      margin-bottom: 1.5rem; padding: 1rem; border-radius: 12px;
      background: #fff; box-shadow: 0 0 5px rgba(0,0,0,0.05);
    }
    .muted { color: #666; }
    .badge { padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.85rem; font-weight: bold; }
    .managed { background: #e6f4ea; color: #137333; }
    .monitor { background: #fce8e6; color: #c5221f; }
    .alerts { margin-bottom: 1rem; }
    .alert {
      padding: 0.5rem; margin-bottom: 0.5rem; border-radius: 6px;
      background: #fdecea; color: #611a15;
    }
  </style>
</head>

<body>

<div class="sidebar">
  <h2>Navigation</h2>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/recon">Recon</a>
    <a href="/recon_2">Handshake Capture</a>
    <a href="/wireless_landscape">Wireless Landscape</a>
    <a href="/probes">Probes</a>
    <a href="/beacons">Beacon Flood</a>
    <a href="/settings">NIC Settings</a>
    <a href="#">Logs</a>
  </div>
</div>

<main>
  <div class="column">

    <!-- Flash notifications -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="alerts">
          {% for category, msg in messages %}
            <div class="alert {{ category }}">{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <!-- Connected Clients -->
    <div class="card">
      <h2>👥 DHCP Clients</h2>
      {% if devices %}
        <table>
          <thead>
            <tr>
              <th>Hostname</th>
              <th>IP Address</th>
              <th>MAC Address</th>
              <th>Lease</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {% for d in devices %}
              <tr>
                <td><strong>{{ d.hostname or "Unknown" }}</strong></td>
                <td>{{ d.ip }}</td>
                <td><span class="muted">{{ d.mac }}</span></td>
                <td>
                  {% if d.lease_remaining %}
                    {{ (d.lease_remaining // 3600) }}h {{ ((d.lease_remaining % 3600) // 60) }}m
                  {% else %}
                    expired
                  {% endif %}
                </td>
                <td>
                  {% if d.connected %}
                    <span class="badge managed">ACTIVE</span>
                  {% else %}
                    <span class="badge monitor">EXPIRED</span>
                  {% endif %}
                </td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% else %}
        <p class="muted">No DHCP clients connected.</p>
      {% endif %}
    </div>

    <!-- DNS Traffic -->
    <div class="card">
      <h2>🌐 Live DNS Traffic</h2>
      {% if dns_records %}
        <table>
          <thead>
            <tr>
              <th>Hostname</th>
              <th>Client IP</th>
              <th>Requested Domain</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {% for record in dns_records|reverse %}
              <tr>
                <td>
                  {% set ns = namespace(hostname="Unknown") %}
                  {% for d in devices %}
                    {% if d.ip == record.client_ip %}
                      {% set ns.hostname = d.hostname or "Unknown" %}
                    {% endif %}
                  {% endfor %}
                  <strong>{{ ns.hostname }}</strong>
                </td>
                <td>{{ record.client_ip }}</td>
                <td><code>{{ record.query }}</code></td>
                <td>{{ record.timestamp_paris }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% else %}
        <p class="muted">No DNS queries on the page.</p>
      {% endif %}
    </div>

  </div>

  <footer>
    WAP Status Tracking Panel
  </footer>
</main>

</body>
</html>
"""