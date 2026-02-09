"""
Main application window for Nexus WiFi Traffic Monitor.
"""

import customtkinter as ctk

from nexus.core.scanner import NetworkScanner
from nexus.core.sniffer import TrafficSniffer
from nexus.gui.device_panel import DevicePanel
from nexus.gui.detail_panel import DetailPanel
from nexus.gui.header import HeaderBar
from nexus.gui.theme import (
    BG_DARK,
    BG_CARD,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    FONT_BODY,
    CORNER_RADIUS,
)


class NexusApp(ctk.CTk):
    def __init__(self, scanner: NetworkScanner, sniffer: TrafficSniffer):
        super().__init__()

        self.scanner = scanner
        self.sniffer = sniffer

        # -- window setup -----------------------------------------------------
        self.title("Nexus  —  WiFi Traffic Monitor")
        self.geometry("1360x820")
        self.minsize(960, 600)
        self.configure(fg_color=BG_DARK)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # -- layout -----------------------------------------------------------
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # header
        self.header = HeaderBar(self, scanner=self.scanner)
        self.header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        # main content container
        self.content = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1, minsize=480)
        self.content.grid_columnconfigure(1, weight=2, minsize=480)

        # left: device list
        self.device_panel = DevicePanel(
            self.content,
            on_select=self._on_device_selected,
        )
        self.device_panel.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

        # right: detail view
        self.detail_panel = DetailPanel(self.content)
        self.detail_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)

        # -- start periodic UI refresh ----------------------------------------
        self._selected_mac: str | None = None
        self._refresh()

    # -- callbacks ------------------------------------------------------------

    def _on_device_selected(self, mac: str):
        self._selected_mac = mac
        self._update_detail()

    # -- refresh loop ---------------------------------------------------------

    def _refresh(self):
        """Refresh the device list and detail panel every second."""
        devices = self.scanner.get_devices()
        all_history = self.sniffer.get_all_history()

        self.device_panel.update_devices(devices, all_history)
        self.header.update_stats(devices)

        if self._selected_mac:
            self._update_detail()

        self.after(1000, self._refresh)

    def _update_detail(self):
        if not self._selected_mac:
            return
        devices = self.scanner.get_devices()
        device = None
        for d in devices:
            if d.mac == self._selected_mac:
                device = d
                break
        if device is None:
            return
        history = self.sniffer.get_history(device.ip)
        self.detail_panel.show_device(device, history)
