"""
Left-side panel — searchable, scrollable list of discovered devices.
"""

import time
from typing import Callable

import customtkinter as ctk

from nexus.core.scanner import Device
from nexus.core.sniffer import TrafficEntry
from nexus.gui.theme import (
    BG_CARD,
    BG_CARD_HOVER,
    BG_DARK,
    BG_INPUT,
    BORDER,
    BORDER_ACCENT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_DIM,
    ACCENT,
    ACCENT_DIM,
    GREEN,
    RED,
    FONT_H3,
    FONT_BODY,
    FONT_SMALL,
    FONT_TINY,
    FONT_MONO,
    CORNER_RADIUS,
    CARD_PAD,
)

# device type -> icon character (unicode)
_ICONS: dict[str, str] = {
    "iPhone": "\U0001F4F1",
    "iPad": "\U0001F4F1",
    "Android Phone": "\U0001F4F1",
    "Android": "\U0001F4F1",
    "Mac": "\U0001F4BB",
    "Laptop / PC": "\U0001F4BB",
    "Windows PC": "\U0001F4BB",
    "Printer": "\U0001F5A8",
    "Smart Speaker": "\U0001F50A",
    "Smart Home": "\U0001F3E0",
    "Streaming Device": "\U0001F4FA",
    "Game Console": "\U0001F3AE",
    "Network Infra": "\U0001F310",
    "Network Adapter": "\U0001F310",
    "IoT / Embedded": "\U00002699",
    "Kindle": "\U0001F4D6",
    "Unknown": "\U00002753",
}


class DevicePanel(ctk.CTkFrame):
    def __init__(self, master, on_select: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=CORNER_RADIUS, **kwargs)
        self._on_select = on_select
        self._cards: dict[str, ctk.CTkFrame] = {}
        self._selected_mac: str | None = None

        # -- header row -------------------------------------------------------
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=CARD_PAD, pady=(CARD_PAD, 8))
        ctk.CTkLabel(top, text="Devices", font=FONT_H3, text_color=TEXT_PRIMARY).pack(
            side="left"
        )
        self.lbl_count = ctk.CTkLabel(
            top, text="0 found", font=FONT_TINY, text_color=TEXT_DIM
        )
        self.lbl_count.pack(side="right")

        # -- search bar -------------------------------------------------------
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        self.search = ctk.CTkEntry(
            self,
            textvariable=self.search_var,
            placeholder_text="Search devices...",
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            font=FONT_SMALL,
            corner_radius=8,
            height=34,
        )
        self.search.pack(fill="x", padx=CARD_PAD, pady=(0, 8))

        # -- scrollable device list -------------------------------------------
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=BORDER_ACCENT,
        )
        self.scroll.pack(fill="both", expand=True, padx=4, pady=(0, 8))

    # -- public ---------------------------------------------------------------

    def update_devices(
        self,
        devices: list[Device],
        all_history: dict[str, list[TrafficEntry]],
    ):
        self.lbl_count.configure(text=f"{len(devices)} found")

        existing_macs = set(self._cards.keys())
        incoming_macs = {d.mac for d in devices}

        # remove cards for devices no longer tracked
        for mac in existing_macs - incoming_macs:
            self._cards[mac].destroy()
            del self._cards[mac]

        # add or update
        for dev in sorted(devices, key=lambda d: (not d.is_online, d.last_seen * -1)):
            history = all_history.get(dev.ip, [])
            recent = history[0].domain if history else ""
            if dev.mac in self._cards:
                self._refresh_card(dev, recent)
            else:
                self._create_card(dev, recent)

        self._apply_filter()

    # -- card management ------------------------------------------------------

    def _create_card(self, dev: Device, recent_domain: str):
        card = ctk.CTkFrame(
            self.scroll,
            fg_color=BG_DARK,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            cursor="hand2",
        )
        card.pack(fill="x", padx=6, pady=3)
        card.dev = dev  # type: ignore[attr-defined]

        # make entire card clickable
        card.bind("<Button-1>", lambda e, m=dev.mac: self._select(m))

        # top row: icon + name + status dot
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(8, 2))
        top.bind("<Button-1>", lambda e, m=dev.mac: self._select(m))

        icon_text = _ICONS.get(dev.device_type, "\U00002753")
        icon_lbl = ctk.CTkLabel(top, text=icon_text, font=("Segoe UI Emoji", 16), width=24)
        icon_lbl.pack(side="left")
        icon_lbl.bind("<Button-1>", lambda e, m=dev.mac: self._select(m))

        display_name = dev.hostname or dev.ip
        name_lbl = ctk.CTkLabel(
            top, text=display_name, font=FONT_BODY, text_color=TEXT_PRIMARY, anchor="w"
        )
        name_lbl.pack(side="left", padx=(6, 0), fill="x", expand=True)
        name_lbl.bind("<Button-1>", lambda e, m=dev.mac: self._select(m))

        dot_color = GREEN if dev.is_online else RED
        dot = ctk.CTkLabel(top, text="\u25CF", text_color=dot_color, font=("Arial", 10))
        dot.pack(side="right")
        dot.bind("<Button-1>", lambda e, m=dev.mac: self._select(m))

        # bottom row: device type + recent domain
        bot = ctk.CTkFrame(card, fg_color="transparent")
        bot.pack(fill="x", padx=10, pady=(0, 8))
        bot.bind("<Button-1>", lambda e, m=dev.mac: self._select(m))

        type_lbl = ctk.CTkLabel(
            bot, text=dev.device_type, font=FONT_TINY, text_color=TEXT_DIM, anchor="w"
        )
        type_lbl.pack(side="left")
        type_lbl.bind("<Button-1>", lambda e, m=dev.mac: self._select(m))

        if recent_domain:
            dom_lbl = ctk.CTkLabel(
                bot,
                text=recent_domain,
                font=FONT_TINY,
                text_color=TEXT_SECONDARY,
                anchor="e",
            )
            dom_lbl.pack(side="right")
            dom_lbl.bind("<Button-1>", lambda e, m=dev.mac: self._select(m))

        # stash references for updating
        card._name_lbl = name_lbl  # type: ignore[attr-defined]
        card._dot = dot  # type: ignore[attr-defined]
        card._type_lbl = type_lbl  # type: ignore[attr-defined]
        card._bot = bot  # type: ignore[attr-defined]
        self._cards[dev.mac] = card

    def _refresh_card(self, dev: Device, recent_domain: str):
        card = self._cards[dev.mac]
        card.dev = dev  # type: ignore[attr-defined]
        display_name = dev.hostname or dev.ip
        card._name_lbl.configure(text=display_name)  # type: ignore[attr-defined]
        dot_color = GREEN if dev.is_online else RED
        card._dot.configure(text_color=dot_color)  # type: ignore[attr-defined]
        card._type_lbl.configure(text=dev.device_type)  # type: ignore[attr-defined]

    def _select(self, mac: str):
        # unhighlight previous
        if self._selected_mac and self._selected_mac in self._cards:
            self._cards[self._selected_mac].configure(
                border_color=BORDER, fg_color=BG_DARK
            )
        # highlight new
        self._selected_mac = mac
        if mac in self._cards:
            self._cards[mac].configure(
                border_color=ACCENT, fg_color=ACCENT_DIM
            )
        self._on_select(mac)

    def _apply_filter(self):
        query = self.search_var.get().lower()
        for mac, card in self._cards.items():
            dev: Device = card.dev  # type: ignore[attr-defined]
            blob = f"{dev.hostname} {dev.ip} {dev.mac} {dev.vendor} {dev.device_type}".lower()
            if query in blob:
                card.pack(fill="x", padx=6, pady=3)
            else:
                card.pack_forget()
