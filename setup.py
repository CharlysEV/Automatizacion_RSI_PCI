from setuptools import setup

setup(
    name="pci_rsi_sugeridor",
    version="3.9",
    py_modules=["io", "core"],
    install_requires=[
        "pandas>=1.0",
        "openpyxl>=3.0",
        "tabulate>=0.8"
    ],
    extras_require={
        "dev": ["pytest>=7.0"]
    },
    entry_points={
        "console_scripts": [
            "pci-rsi=io:main"
        ]
    }
)
