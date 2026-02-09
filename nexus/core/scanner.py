"""
Network scanner module — discovers devices on the local network via ARP.
"""

import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from scapy.all import ARP, Ether, srp, conf

from nexus.utils.device_id import identify_device_type, lookup_mac_vendor


@dataclass
class Device:
    ip: str
    mac: str
    hostname: str = ""
    vendor: str = ""
    device_type: str = "Unknown"
    first_seen: float = 0.0
    last_seen: float = 0.0
    is_online: bool = True


class NetworkScanner:
    """Periodically ARP-scans the local subnet and maintains a device table."""

    def __init__(self, iface: str | None = None, scan_interval: int = 30):
        self.iface = iface or conf.iface
        self.scan_interval = scan_interval
        self.devices: dict[str, Device] = {}  # keyed by MAC
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._on_update: Callable | None = None

    # -- public API -----------------------------------------------------------

    def start(self, on_update: Callable | None = None):
        self._on_update = on_update
        self._running = True
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_devices(self) -> list[Device]:
        with self._lock:
            return list(self.devices.values())

    def get_subnet(self) -> str:
        """Derive the /24 subnet from the default gateway or interface IP."""
        try:
            import psutil
            addrs = psutil.net_if_addrs().get(self.iface, [])
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    parts = addr.address.rsplit(".", 1)
                    return f"{parts[0]}.0/24"
        except Exception:
            pass
        # fallback: use scapy route table
        for route in conf.route.routes:
            if route[3] == self.iface and route[1] != 0xFFFFFFFF:
                ip = conf.route.get_if_addr(self.iface)
                parts = ip.rsplit(".", 1)
                return f"{parts[0]}.0/24"
        return "192.168.1.0/24"

    # -- internals ------------------------------------------------------------

    def _scan_loop(self):
        while self._running:
            try:
                self._do_scan()
            except Exception:
                pass
            for _ in range(self.scan_interval * 10):
                if not self._running:
                    return
                time.sleep(0.1)

    def _do_scan(self):
        subnet = self.get_subnet()
        pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
        ans, _ = srp(pkt, timeout=3, verbose=False, iface=self.iface)

        now = time.time()
        seen_macs: set[str] = set()

        for _, rcv in ans:
            mac = rcv[Ether].src.upper()
            ip = rcv[ARP].psrc
            seen_macs.add(mac)

            with self._lock:
                if mac in self.devices:
                    dev = self.devices[mac]
                    dev.ip = ip
                    dev.last_seen = now
                    dev.is_online = True
                else:
                    hostname = self._resolve_hostname(ip)
                    vendor = lookup_mac_vendor(mac)
                    dev = Device(
                        ip=ip,
                        mac=mac,
                        hostname=hostname,
                        vendor=vendor,
                        device_type=identify_device_type(vendor, hostname),
                        first_seen=now,
                        last_seen=now,
                        is_online=True,
                    )
                    self.devices[mac] = dev

        # mark devices not seen as offline
        with self._lock:
            for mac, dev in self.devices.items():
                if mac not in seen_macs:
                    dev.is_online = False

        if self._on_update:
            self._on_update()

    @staticmethod
    def _resolve_hostname(ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror, OSError):
            return ""
