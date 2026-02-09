"""
Right-side detail panel — shows device info and browsing history.
"""

import time
from datetime import datetime

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
    GREEN,
    RED,
    BLUE,
    YELLOW,
    FONT_H2,
    FONT_H3,
    FONT_BODY,
    FONT_SMALL,
    FONT_TINY,
    FONT_MONO,
    CORNER_RADIUS,
    CARD_PAD,
)


def _relative_time(ts: float) -> str:
    diff = time.time() - ts
    if diff < 5:
        return "just now"
    if diff < 60:
        return f"{int(diff)}s ago"
    if diff < 3600:
        return f"{int(diff // 60)}m ago"
    if diff < 86400:
        return f"{int(diff // 3600)}h ago"
    return datetime.fromtimestamp(ts).strftime("%b %d, %H:%M")


_QUERY_TAG_COLORS = {
    "DNS": BLUE,
    "TLS": GREEN,
    "HTTP": YELLOW,
}


class DetailPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=CORNER_RADIUS, **kwargs)

        # placeholder when nothing is selected
        self._placeholder = ctk.CTkLabel(
            self,
            text="Select a device to view details",
            font=FONT_BODY,
            text_color=TEXT_DIM,
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # container that holds actual detail content
        self._detail_frame: ctk.CTkFrame | None = None

    def show_device(self, device: Device, history: list[TrafficEntry]):
        self._placeholder.place_forget()

        # rebuild detail frame
        if self._detail_frame:
            self._detail_frame.destroy()

        self._detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._detail_frame.pack(fill="both", expand=True, padx=CARD_PAD, pady=CARD_PAD)

        # -- device info header -----------------------------------------------
        info_card = ctk.CTkFrame(
            self._detail_frame,
            fg_color=BG_DARK,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
        )
        info_card.pack(fill="x", pady=(0, 12))

        # row 1: name + status
        row1 = ctk.CTkFrame(info_card, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(12, 4))

        display_name = device.hostname or device.ip
        ctk.CTkLabel(
            row1, text=display_name, font=FONT_H2, text_color=TEXT_PRIMARY
        ).pack(side="left")

        status_color = GREEN if device.is_online else RED
        status_text = "Online" if device.is_online else "Offline"
        status_frame = ctk.CTkFrame(row1, fg_color="transparent")
        status_frame.pack(side="right")
        ctk.CTkLabel(
            status_frame, text="\u25CF", text_color=status_color, font=("Arial", 10)
        ).pack(side="left", padx=(0, 4))
        ctk.CTkLabel(
            status_frame, text=status_text, font=FONT_SMALL, text_color=status_color
        ).pack(side="left")

        # row 2: metadata grid
        meta = ctk.CTkFrame(info_card, fg_color="transparent")
        meta.pack(fill="x", padx=14, pady=(0, 12))

        self._meta_field(meta, "IP Address", device.ip, 0, 0)
        self._meta_field(meta, "MAC Address", device.mac, 0, 1)
        self._meta_field(meta, "Vendor", device.vendor or "Unknown", 1, 0)
        self._meta_field(meta, "Device Type", device.device_type, 1, 1)
        self._meta_field(
            meta,
            "First Seen",
            datetime.fromtimestamp(device.first_seen).strftime("%b %d, %H:%M:%S")
            if device.first_seen
            else "-",
            2,
            0,
        )
        self._meta_field(
            meta,
            "Last Seen",
            _relative_time(device.last_seen) if device.last_seen else "-",
            2,
            1,
        )

        meta.grid_columnconfigure(0, weight=1)
        meta.grid_columnconfigure(1, weight=1)

        # -- traffic history --------------------------------------------------
        hist_header = ctk.CTkFrame(self._detail_frame, fg_color="transparent")
        hist_header.pack(fill="x", pady=(4, 6))
        ctk.CTkLabel(
            hist_header, text="Traffic History", font=FONT_H3, text_color=TEXT_PRIMARY
        ).pack(side="left")
        ctk.CTkLabel(
            hist_header,
            text=f"{len(history)} entries",
            font=FONT_TINY,
            text_color=TEXT_DIM,
        ).pack(side="right")

        # scrollable history list
        history_scroll = ctk.CTkScrollableFrame(
            self._detail_frame,
            fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=BORDER_ACCENT,
        )
        history_scroll.pack(fill="both", expand=True)

        if not history:
            ctk.CTkLabel(
                history_scroll,
                text="No traffic recorded yet",
                font=FONT_BODY,
                text_color=TEXT_DIM,
            ).pack(pady=40)
        else:
            for entry in history[:200]:
                self._traffic_row(history_scroll, entry)

    # -- helpers --------------------------------------------------------------

    def _meta_field(self, parent, label: str, value: str, row: int, col: int):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="w", padx=(0, 20), pady=2)
        ctk.CTkLabel(frame, text=label, font=FONT_TINY, text_color=TEXT_DIM).pack(
            anchor="w"
        )
        ctk.CTkLabel(
            frame, text=value, font=FONT_SMALL, text_color=TEXT_PRIMARY
        ).pack(anchor="w")

    def _traffic_row(self, parent, entry: TrafficEntry):
        row = ctk.CTkFrame(
            parent,
            fg_color=BG_DARK,
            corner_radius=6,
            height=38,
            border_width=1,
            border_color=BORDER,
        )
        row.pack(fill="x", padx=2, pady=2)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10)

        # protocol tag
        tag_color = _QUERY_TAG_COLORS.get(entry.query_type, TEXT_DIM)
        ctk.CTkLabel(
            inner,
            text=entry.query_type,
            font=FONT_TINY,
            text_color=BG_DARK,
            fg_color=tag_color,
            corner_radius=4,
            width=40,
            height=20,
        ).pack(side="left", padx=(0, 8), pady=8)

        # domain
        ctk.CTkLabel(
            inner,
            text=entry.domain,
            font=FONT_MONO,
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # timestamp
        ctk.CTkLabel(
            inner,
            text=_relative_time(entry.timestamp),
            font=FONT_TINY,
            text_color=TEXT_DIM,
        ).pack(side="right")
