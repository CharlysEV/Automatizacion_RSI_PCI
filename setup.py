#!/usr/bin/env python3
# setup.py — Instalación y package metadata

from setuptools import setup, find_packages

setup(
    name="pci_rsi_sugeridor",
    version="0.1.0",
    description="CLI y librería para sugerir asignaciones de PCI/RSI ZN-ZR con pool virtual",
    author="Carlos Álvarez Corredor",
    author_email="carlos.alvarez@circet.es",
    url="https://github.com/CharlysEV/Automatizacion_RSI_PCI",
    packages=find_packages(exclude=["tests", ".github", "venv*"]),
    install_requires=[
        "pandas>=1.0",
        "openpyxl>=3.0",
        "tabulate>=0.8",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=22.0",
            "flake8>=4.0",
        ]
    },
    entry_points={
        "console_scripts": [
            # Asume que tu io.py define una función main() que lanza el CLI
            "pci-rsi=pci_rsi_sugeridor.io:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
