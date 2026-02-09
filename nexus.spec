# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Nexus WiFi Traffic Monitor.

Build with:
    pyinstaller nexus.spec

Output lands in dist/Nexus/Nexus.exe (one-dir) or dist/Nexus.exe (one-file).
"""

import os
import sys
import importlib

block_cipher = None

# Locate customtkinter package data (themes, assets)
ctk_path = os.path.dirname(importlib.import_module("customtkinter").__file__)

a = Analysis(
    ["nexus/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[
        # bundle customtkinter's theme/json files
        (ctk_path, "customtkinter"),
    ],
    hiddenimports=[
        # scapy pulls in a lot dynamically
        "scapy.all",
        "scapy.layers.dns",
        "scapy.layers.http",
        "scapy.layers.inet",
        "scapy.layers.l2",
        "scapy.layers.tls",
        "scapy.arch.windows",
        "scapy.arch.windows.native",
        # mac vendor db
        "mac_vendor_lookup",
        # tkinter
        "tkinter",
        "_tkinter",
        # our packages
        "nexus",
        "nexus.core",
        "nexus.core.scanner",
        "nexus.core.sniffer",
        "nexus.gui",
        "nexus.gui.app",
        "nexus.gui.header",
        "nexus.gui.device_panel",
        "nexus.gui.detail_panel",
        "nexus.gui.theme",
        "nexus.utils",
        "nexus.utils.device_id",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",
        "cv2",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Nexus",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # no console window — GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,          # request admin on launch (Windows UAC)
    icon=None,               # set to "assets/icon.ico" if you add one
)
