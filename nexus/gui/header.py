"""
Top header bar with branding, stats, and interface selector.
"""

import customtkinter as ctk

from nexus.core.scanner import Device, NetworkScanner
from nexus.gui.theme import (
    BG_CARD,
    BG_DARK,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_DIM,
    ACCENT,
    GREEN,
    RED,
    FONT_H1,
    FONT_H2,
    FONT_H3,
    FONT_BODY,
    FONT_SMALL,
    FONT_TINY,
    CORNER_RADIUS,
)


class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, scanner: NetworkScanner, **kwargs):
        super().__init__(
            master,
            fg_color=BG_CARD,
            corner_radius=0,
            height=72,
            border_width=0,
            **kwargs,
        )
        self.scanner = scanner
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        # logo / title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=14, sticky="w")

        ctk.CTkLabel(
            title_frame,
            text="NEXUS",
            font=FONT_H1,
            text_color=ACCENT,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text="  WiFi Traffic Monitor",
            font=FONT_BODY,
            text_color=TEXT_SECONDARY,
        ).pack(side="left", pady=(4, 0))

        # stats (right side)
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.grid(row=0, column=2, padx=20, pady=14, sticky="e")

        self.lbl_online = self._stat_label("0", "Online", GREEN)
        self.lbl_offline = self._stat_label("0", "Offline", RED)
        self.lbl_total = self._stat_label("0", "Total", TEXT_SECONDARY)

        # interface info
        iface_frame = ctk.CTkFrame(self, fg_color="transparent")
        iface_frame.grid(row=0, column=1, sticky="e", padx=10)
        self.lbl_iface = ctk.CTkLabel(
            iface_frame,
            text=f"Interface: {scanner.iface}",
            font=FONT_TINY,
            text_color=TEXT_DIM,
        )
        self.lbl_iface.pack()
        self.lbl_subnet = ctk.CTkLabel(
            iface_frame,
            text=f"Subnet: {scanner.get_subnet()}",
            font=FONT_TINY,
            text_color=TEXT_DIM,
        )
        self.lbl_subnet.pack()

    def _stat_label(self, value: str, label: str, color: str):
        frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        frame.pack(side="left", padx=14)
        val = ctk.CTkLabel(frame, text=value, font=FONT_H2, text_color=color)
        val.pack()
        ctk.CTkLabel(frame, text=label, font=FONT_TINY, text_color=TEXT_DIM).pack()
        return val

    def update_stats(self, devices: list[Device]):
        online = sum(1 for d in devices if d.is_online)
        offline = len(devices) - online
        self.lbl_online.configure(text=str(online))
        self.lbl_offline.configure(text=str(offline))
        self.lbl_total.configure(text=str(len(devices)))
