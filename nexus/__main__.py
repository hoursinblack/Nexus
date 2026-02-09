"""
Nexus WiFi Traffic Monitor — entry point.

Usage (script):
    sudo python -m nexus [--iface INTERFACE]

Usage (exe):
    Run Nexus.exe as Administrator

Requires root/admin privileges for packet capture.
"""

import argparse
import ctypes
import os
import sys


def _is_admin() -> bool:
    """Check for elevated privileges on any platform."""
    if os.name == "nt":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0


def _request_admin_windows():
    """Re-launch the current process with a UAC elevation prompt on Windows."""
    if getattr(sys, "frozen", False):
        exe = sys.executable
    else:
        exe = sys.executable  # python.exe
    params = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, params, None, 1
        )
    except Exception:
        pass
    sys.exit(0)


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
    if not _is_admin():
        if os.name == "nt":
            _request_admin_windows()
        else:
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
