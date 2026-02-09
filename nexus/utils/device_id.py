"""
Device identification utilities — MAC vendor lookup and device-type heuristics.
"""

_VENDOR_CACHE: dict[str, str] = {}
_mac_lookup = None


def _get_mac_lookup():
    global _mac_lookup
    if _mac_lookup is None:
        try:
            from mac_vendor_lookup import MacLookup
            _mac_lookup = MacLookup()
        except Exception:
            _mac_lookup = False
    return _mac_lookup


def lookup_mac_vendor(mac: str) -> str:
    """Return the manufacturer name for a MAC address."""
    if mac in _VENDOR_CACHE:
        return _VENDOR_CACHE[mac]

    vendor = ""
    lookup = _get_mac_lookup()
    if lookup:
        try:
            vendor = lookup.lookup(mac)
        except Exception:
            vendor = ""

    _VENDOR_CACHE[mac] = vendor
    return vendor


# keyword -> device type mapping (order matters — first match wins)
_TYPE_RULES: list[tuple[list[str], str]] = [
    (["iphone", "ios"], "iPhone"),
    (["ipad"], "iPad"),
    (["apple", "macbook", "imac", "mac-"], "Mac"),
    (["samsung", "galaxy"], "Android Phone"),
    (["android"], "Android"),
    (["pixel", "oneplus", "xiaomi", "huawei", "oppo", "vivo", "realme"], "Android Phone"),
    (["kindle", "fire"], "Kindle"),
    (["roku", "chromecast", "fire tv", "apple tv", "nvidia shield"], "Streaming Device"),
    (["playstation", "xbox", "nintendo", "switch"], "Game Console"),
    (["echo", "alexa", "google home", "homepod", "sonos"], "Smart Speaker"),
    (["nest", "ring", "arlo", "wyze", "blink"], "Smart Home"),
    (["printer", "canon", "epson", "brother", "hp inc"], "Printer"),
    (["raspberry", "espressif", "arduino"], "IoT / Embedded"),
    (["dell", "lenovo", "hp", "asus", "acer", "toshiba", "msi"], "Laptop / PC"),
    (["intel", "realtek", "qualcomm", "broadcom", "mediatek"], "Network Adapter"),
    (["cisco", "ubiquiti", "netgear", "tp-link", "aruba", "meraki", "unifi"], "Network Infra"),
    (["microsoft"], "Windows PC"),
    (["windows"], "Windows PC"),
]


def identify_device_type(vendor: str, hostname: str) -> str:
    """Guess the device type from vendor string and hostname."""
    blob = f"{vendor} {hostname}".lower()
    for keywords, device_type in _TYPE_RULES:
        for kw in keywords:
            if kw in blob:
                return device_type
    return "Unknown"
