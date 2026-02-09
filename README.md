# Nexus — WiFi Traffic Monitor

A real-time WiFi traffic monitoring tool with a sleek dark GUI. Nexus discovers every device on your network, identifies what type of device it is, and shows you what websites each device is visiting.

Built as a modern replacement for outdated school network monitoring tools.

## What It Does

- **Device Discovery** — ARP scans the local subnet to find every connected device
- **Device Identification** — Resolves hostnames, looks up MAC vendors, and guesses device types (iPhone, laptop, printer, smart speaker, etc.)
- **Traffic Capture** — Sniffs DNS queries, TLS SNI (Server Name Indication), and HTTP Host headers to log which domains each device visits
- **Live Dashboard** — Dark-themed GUI that updates in real time with a searchable device list and per-device traffic history

## Screenshot Layout

```
+-----------------------------------------------+
|  NEXUS  WiFi Traffic Monitor     3 Online  1 … |
+------------------+----------------------------+
| [Search devices] |  Device: fred              |
|                  |  IP: 192.168.1.42          |
|  > fred     [●]  |  MAC: AA:BB:CC:DD:EE:FF   |
|  > printer  [●]  |  Vendor: Apple Inc.        |
|  > galaxy   [○]  |  Type: Mac                 |
|                  |                            |
|                  |  Traffic History            |
|                  |  TLS  github.com     2m ago |
|                  |  DNS  reddit.com     5m ago |
|                  |  TLS  youtube.com   12m ago |
+------------------+----------------------------+
```

## Requirements

- Python 3.11+
- Root / administrator privileges (required for packet capture)
- A WiFi interface in monitor-capable mode (or a standard interface for ARP + DNS sniffing)

## Installation

```bash
# clone the repo
git clone https://github.com/hoursinblack/Nexus.git
cd Nexus

# (recommended) create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# run with auto-detected interface
sudo python -m nexus

# or specify an interface
sudo python -m nexus --iface wlan0

# adjust scan interval (default 30s)
sudo python -m nexus --scan-interval 15
```

## How It Works

1. **ARP Scanner** (`nexus/core/scanner.py`) — Sends ARP broadcast packets to the local /24 subnet and collects replies. Each responding device is added to the device table with its IP, MAC, resolved hostname, and vendor.

2. **Traffic Sniffer** (`nexus/core/sniffer.py`) — Runs a packet capture filter on ports 53, 80, and 443:
   - **DNS (port 53)** — Reads the query name from DNS request packets
   - **HTTP (port 80)** — Extracts the `Host:` header from plaintext HTTP requests
   - **TLS (port 443)** — Parses the SNI extension from TLS ClientHello messages

3. **Device Identification** (`nexus/utils/device_id.py`) — Combines MAC vendor lookup (via OUI database) with hostname keyword matching to classify devices into types like "iPhone", "Laptop / PC", "Printer", etc.

4. **GUI** (`nexus/gui/`) — Built with CustomTkinter for a native-feeling dark interface. Refreshes every second to show live device status and traffic.

## Limitations

- VPN / encrypted DNS (DoH/DoT) will hide traffic from this tool — this is expected
- Only sees traffic on the local subnet; devices on VLANs or different subnets won't appear
- Requires the monitoring machine to be on the same network segment
- TLS 1.3 with Encrypted Client Hello (ECH) will hide SNI

## Project Structure

```
Nexus/
├── nexus/
│   ├── __init__.py
│   ├── __main__.py          # entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scanner.py       # ARP network scanner
│   │   └── sniffer.py       # DNS/TLS/HTTP traffic sniffer
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── app.py           # main window
│   │   ├── header.py        # top bar with stats
│   │   ├── device_panel.py  # left device list
│   │   ├── detail_panel.py  # right detail/history view
│   │   └── theme.py         # colors and fonts
│   └── utils/
│       ├── __init__.py
│       └── device_id.py     # MAC vendor + device type identification
├── requirements.txt
├── setup.py
└── .gitignore
```

## License

MIT
