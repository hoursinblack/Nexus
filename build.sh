#!/usr/bin/env bash
set -e

echo "============================================"
echo "  Nexus — Building standalone executable"
echo "============================================"
echo

echo "[1/3] Installing dependencies..."
pip install -r requirements.txt

echo
echo "[2/3] Building with PyInstaller..."
pyinstaller nexus.spec --noconfirm

echo
echo "[3/3] Done!"
echo
echo "  Output: dist/Nexus"
echo "  Run with: sudo ./dist/Nexus"
echo
