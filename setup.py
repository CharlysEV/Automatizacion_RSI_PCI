#!/usr/bin/env python3
# setup.py — Instalación y metadata del package

from setuptools import find_packages, setup

setup(
    name="pci_rsi_sugeridor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # aquí van tus dependencias runtime, p.ej.:
        # "requests>=2.25.1",
    ],
    extras_require={
        "dev": [
            "pytest",
            "coverage",
            "flake8",
            "black",
            "isort",
            "mypy",
            "codecov",
        ],
    },
    entry_points={
        "console_scripts": [
            # Asume que pci_rsi_sugeridor/io.py define una función main()
            "pci-rsi=pci_rsi_sugeridor.io:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
