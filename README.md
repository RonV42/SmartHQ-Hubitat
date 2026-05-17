# SmartHQ-Hubitat

A Python bridge and Hubitat Elevation drivers for integrating GE SmartHQ appliances 
into Hubitat Elevation via the SmartHQ cloud API.

## Why This Exists

The GE SmartHQ Android/iOS app delivers unreliable push notifications for appliance 
events like preheat complete, cook timer done, and cycle finished. This bridge replaces 
that dependency with rock-solid Hubitat automations and Rule Machine rules by maintaining 
a persistent WebSocket connection to the SmartHQ cloud API and pushing state changes to 
Hubitat virtual devices via the Maker API.

## Architecture

```
SmartHQ Cloud
     │ (WebSocket/OAuth2 - persistent connection)
     ▼
Python Bridge (systemd service)
     │ (HTTP GET - Maker API)
     ▼
Hubitat Virtual Devices
     │
     ▼
Rule Machine (notifications, automations)
```

The bridge is receive-only by design. Your appliances remain in full control of 
themselves — Hubitat is purely an observer. No risk of automation logic interfering 
with safety-critical appliance functions.

## Included Drivers

The included drivers are built and tested against a **GE Profile PKD7000SN6SS double 
oven range**. This appliance requires three virtual devices in Hubitat due to its 
architecture — a shared control panel plus two independent oven cavities.

The number of Hubitat virtual devices required will vary by appliance type:

- **Double oven range** — 3 devices (control panel, upper oven, lower oven)
- **Single oven range** — 2 devices (control panel, oven)
- **Single appliance** (dishwasher, washer, dryer, refrigerator) — 1 device

Use the discovery script to determine the ERD code structure of your specific 
appliance before creating drivers and virtual devices. The ERD namespace will 
reveal how many logical devices make sense for your model.

## Prerequisites

- Hubitat Elevation hub (tested on C7)
- Hubitat Maker API app installed and configured
- GE SmartHQ account with appliance registered in the SmartHQ app
- Linux host for the Python bridge (Proxmox LXC, Raspberry Pi, or similar)
- Python 3.11 or higher
- Network access from bridge host to Hubitat hub

## Installation

### Step 1 — Discover Your Appliance ERD Codes

Before installing the bridge, run the discovery script to map the ERD codes your 
specific appliance reports. This is essential if you have a different appliance 
model than the included drivers.

```bash
# Create a working directory
mkdir /opt/smarthq-discovery
python3 -m venv /opt/smarthq-discovery
source /opt/smarthq-discovery/bin/activate
pip install gehomesdk

# Create your credentials file
nano /opt/smarthq-discovery/config.json
```

Populate config.json using config.json.example as a template — SmartHQ credentials 
only needed for discovery, Hubitat fields not required at this stage.

```bash
python3 discovery/discover.py
```

The script will connect to SmartHQ, dump all ERD codes your appliance reports, then 
wait for state changes. Interact with your appliance — open doors, turn on lights, 
start a preheat cycle — to capture the full range of ERD codes your model supports.

Press Ctrl+C when done. Note the ERD codes relevant to your appliance for driver 
and bridge customization.

### Step 2 — Install Hubitat Drivers

In Hubitat Elevation Developer Tools, create a new driver for each of the included 
driver files appropriate for your appliance type. After saving each driver, create 
a virtual device using each driver type. Note the device ID assigned by Hubitat for 
each device — you will need these for the bridge configuration.

### Step 3 — Configure Maker API

In Hubitat:

1. Install the **Maker API** built-in app if not already installed
2. Add all virtual devices to the authorized devices list
3. Note your Maker API **App ID** and **Access Token**
4. Ensure **Allow commands** is enabled
5. Click **Done** to save — this step is required for changes to take effect

### Step 4 — Install the Bridge

```bash
# Create bridge directory
mkdir /opt/smarthq-bridge

# Create Python virtual environment
python3 -m venv /opt/smarthq-bridge/venv
source /opt/smarthq-bridge/venv/bin/activate

# Install dependencies
pip install gehomesdk

# Copy bridge script
cp bridge/bridge.py /opt/smarthq-bridge/

# Create configuration file
nano /opt/smarthq-bridge/config.json
```

Populate config.json using config.json.example as a template with your SmartHQ 
credentials, Hubitat IP, Maker API details, and device IDs.

```bash
# Secure the credentials file
chmod 600 /opt/smarthq-bridge/config.json
```

### Step 5 — Test the Bridge

```bash
source /opt/smarthq-bridge/venv/bin/activate
python3 /opt/smarthq-bridge/bridge.py
```

Confirm attributes populate on all virtual Hubitat devices before proceeding 
to systemd setup.

### Step 6 — Install as a systemd Service

```bash
nano /etc/systemd/system/smarthq-bridge.service
```

```ini
[Unit]
Description=SmartHQ to Hubitat Bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/smarthq-bridge
ExecStart=/opt/smarthq-bridge/venv/bin/python3 /opt/smarthq-bridge/bridge.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable smarthq-bridge
systemctl start smarthq-bridge
systemctl status smarthq-bridge
```

## Extending to Other Appliances

The discovery script and bridge are not limited to double oven ranges. Any SmartHQ 
appliance can be integrated by:

1. Running the discovery script to map ERD codes for your appliance
2. Creating custom Hubitat drivers with attributes matching your ERD codes
3. Adding push functions to bridge.py for your appliance's ERD codes

Refer to the [gehomesdk documentation](https://github.com/simbaja/gehome) and the 
[GEMaker GitHub repositories](https://github.com/GEMakers) for ERD code references 
across appliance types.

## Technical Notes

- The SmartHQ cloud API uses OAuth2 with approximately 60 minute token expiry
- The gehomesdk library handles token refresh and reconnection automatically
- Reconnection window is approximately 12 seconds during token refresh
- The bridge is receive-only — no appliance control commands are sent
- Hubitat attributes are updated via the Maker API setAttribute command with 
  comma-separated parameters: `/devices/{id}/setAttribute/{attribute},{value}`

## Acknowledgements

- [simbaja/gehome](https://github.com/simbaja/gehome) — Python SDK for GE SmartHQ appliances
- [GEMaker](https://github.com/GEMakers) — GE appliance protocol documentation

## License

MIT License — see LICENSE file for details.
