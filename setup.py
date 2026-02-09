from setuptools import setup, find_packages

setup(
    name="nexus-wifi-monitor",
    version="1.0.0",
    description="WiFi traffic monitor with a sleek dark GUI",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "scapy>=2.5.0",
        "customtkinter>=5.2.0",
        "psutil>=5.9.0",
        "mac-vendor-lookup>=0.1.12",
    ],
    entry_points={
        "console_scripts": [
            "nexus=nexus.__main__:main",
        ],
    },
)
