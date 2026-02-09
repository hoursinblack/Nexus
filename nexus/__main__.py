"""
Nexus WiFi Traffic Monitor — entry point.

Usage:
    sudo python -m nexus [--iface INTERFACE]

Requires root/admin privileges for packet capture.
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Nexus — WiFi Traffic Monitor",
    )
    parser.add_argument(
        "--iface",
        type=str,
        default=None,
        help="Network interface to monitor (e.g. wlan0, en0, Wi-Fi). "
             "Auto-detected if omitted.",
    )
    parser.add_argument(
        "--scan-interval",
        type=int,
        default=30,
        help="Seconds between ARP scans (default: 30).",
    )
    args = parser.parse_args()

    # privilege check
    if os.name == "posix" and os.geteuid() != 0:
        print(
            "ERROR: Nexus requires root privileges for packet capture.\n"
            "Run with:  sudo python -m nexus"
        )
        sys.exit(1)

    # lazy imports so --help works without deps
    from nexus.core.scanner import NetworkScanner
    from nexus.core.sniffer import TrafficSniffer
    from nexus.gui.app import NexusApp

    scanner = NetworkScanner(iface=args.iface, scan_interval=args.scan_interval)
    sniffer = TrafficSniffer(iface=args.iface)

    # start background threads
    print(f"[nexus] Interface : {scanner.iface}")
    print(f"[nexus] Subnet    : {scanner.get_subnet()}")
    print(f"[nexus] Starting scanner and sniffer...")

    scanner.start(on_update=None)  # GUI refresh loop handles updates
    sniffer.start()

    try:
        app = NexusApp(scanner=scanner, sniffer=sniffer)
        app.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[nexus] Shutting down...")
        sniffer.stop()
        scanner.stop()
        print("[nexus] Done.")


if __name__ == "__main__":
    main()
