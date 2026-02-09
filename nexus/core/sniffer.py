"""
Packet sniffer module — captures DNS queries and HTTP host headers to build
a per-device browsing history.
"""

import threading
import time
from dataclasses import dataclass, field

from scapy.all import (
    DNS,
    DNSQR,
    IP,
    TCP,
    UDP,
    conf,
    sniff,
)


@dataclass
class TrafficEntry:
    timestamp: float
    domain: str
    query_type: str  # "DNS", "HTTP", "TLS"
    src_ip: str
    dst_ip: str


class TrafficSniffer:
    """
    Sniffs DNS (port 53) and TLS ClientHello (port 443) traffic to record
    which domains each IP is visiting.
    """

    def __init__(self, iface: str | None = None, max_history: int = 500):
        self.iface = iface or conf.iface
        self.max_history = max_history
        # ip -> list of TrafficEntry (most recent first)
        self.history: dict[str, list[TrafficEntry]] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._sniff_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_history(self, ip: str) -> list[TrafficEntry]:
        with self._lock:
            return list(self.history.get(ip, []))

    def get_all_history(self) -> dict[str, list[TrafficEntry]]:
        with self._lock:
            return {ip: list(entries) for ip, entries in self.history.items()}

    def get_recent_domains(self, ip: str, limit: int = 10) -> list[TrafficEntry]:
        with self._lock:
            entries = self.history.get(ip, [])
            return entries[:limit]

    # -- internals ------------------------------------------------------------

    def _sniff_loop(self):
        sniff(
            iface=self.iface,
            prn=self._process_packet,
            store=False,
            stop_filter=lambda _: not self._running,
            filter="port 53 or port 443 or port 80",
        )

    def _process_packet(self, pkt):
        try:
            if pkt.haslayer(DNS) and pkt.haslayer(DNSQR):
                self._handle_dns(pkt)
            elif pkt.haslayer(TCP) and pkt.haslayer(IP):
                payload = bytes(pkt[TCP].payload)
                if pkt[TCP].dport == 443 and len(payload) > 5:
                    self._handle_tls_hello(pkt, payload)
                elif pkt[TCP].dport == 80 and len(payload) > 0:
                    self._handle_http(pkt, payload)
        except Exception:
            pass

    def _handle_dns(self, pkt):
        qname = pkt[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".")
        if not qname or qname.endswith(".local") or qname.endswith(".arpa"):
            return
        src_ip = pkt[IP].src if pkt.haslayer(IP) else "unknown"
        dst_ip = pkt[IP].dst if pkt.haslayer(IP) else "unknown"
        self._record(src_ip, qname, "DNS", dst_ip)

    def _handle_tls_hello(self, pkt, payload: bytes):
        """Extract SNI from TLS ClientHello."""
        # TLS record: content_type=0x16 (handshake), then version, length
        if payload[0] != 0x16:
            return
        # Skip record header (5 bytes) + handshake header (4 bytes) = offset 9
        # Then skip: client_version(2) + random(32) + session_id(var)
        try:
            offset = 5  # TLS record header
            if payload[offset] != 0x01:  # ClientHello
                return
            offset += 4  # handshake header
            offset += 2  # client version
            offset += 32  # random
            session_id_len = payload[offset]
            offset += 1 + session_id_len
            cipher_suites_len = int.from_bytes(payload[offset:offset + 2], "big")
            offset += 2 + cipher_suites_len
            comp_methods_len = payload[offset]
            offset += 1 + comp_methods_len
            # extensions
            if offset + 2 > len(payload):
                return
            extensions_len = int.from_bytes(payload[offset:offset + 2], "big")
            offset += 2
            end = offset + extensions_len

            while offset + 4 < end:
                ext_type = int.from_bytes(payload[offset:offset + 2], "big")
                ext_len = int.from_bytes(payload[offset + 2:offset + 4], "big")
                offset += 4
                if ext_type == 0x0000:  # SNI
                    # SNI list length (2) + type (1) + name length (2) + name
                    sni_offset = offset + 2 + 1 + 2
                    name_len = int.from_bytes(
                        payload[offset + 3:offset + 5], "big"
                    )
                    sni = payload[sni_offset:sni_offset + name_len].decode(
                        "utf-8", errors="ignore"
                    )
                    if sni:
                        src_ip = pkt[IP].src
                        dst_ip = pkt[IP].dst
                        self._record(src_ip, sni, "TLS", dst_ip)
                    return
                offset += ext_len
        except (IndexError, ValueError):
            pass

    def _handle_http(self, pkt, payload: bytes):
        """Extract Host header from plain HTTP requests."""
        try:
            text = payload[:2048].decode("utf-8", errors="ignore")
            for line in text.split("\r\n"):
                if line.lower().startswith("host:"):
                    host = line.split(":", 1)[1].strip().split(":")[0]
                    if host:
                        src_ip = pkt[IP].src
                        dst_ip = pkt[IP].dst
                        self._record(src_ip, host, "HTTP", dst_ip)
                    return
        except Exception:
            pass

    def _record(self, src_ip: str, domain: str, query_type: str, dst_ip: str):
        entry = TrafficEntry(
            timestamp=time.time(),
            domain=domain,
            query_type=query_type,
            src_ip=src_ip,
            dst_ip=dst_ip,
        )
        with self._lock:
            if src_ip not in self.history:
                self.history[src_ip] = []
            entries = self.history[src_ip]
            # deduplicate consecutive identical domains
            if entries and entries[0].domain == domain:
                entries[0] = entry  # update timestamp
            else:
                entries.insert(0, entry)
            # trim
            if len(entries) > self.max_history:
                self.history[src_ip] = entries[: self.max_history]
