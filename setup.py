"""Setup script for AutoPosst."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="autoposst",
    version="0.1.0",
    description="Автономная AI Content Entity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AutoPosst Team",
    packages=find_packages(),
    install_requires=[
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "PySide6>=6.6.0",
        "google-generativeai>=0.3.0",
        "sqlalchemy>=2.0.0",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
        "aiohttp>=3.9.0",
        "playwright>=1.40.0",
        "python-telegram-bot>=20.7",
        "vk-api>=11.9.9",
        "cryptography>=41.0.0",
        "keyring>=24.3.0",
        "schedule>=1.2.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "autoposst=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

