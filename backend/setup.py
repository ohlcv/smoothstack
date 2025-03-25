from setuptools import setup, find_packages

setup(
    name="smoothstack-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "rich>=10.0.0",
        "docker>=6.0.0",
        "fastapi>=0.104.1",
        "uvicorn>=0.23.2",
        "pydantic>=2.4.2",
    ],
    entry_points={
        "console_scripts": [
            "smoothstack=backend.cli.main:cli",
        ],
    },
)
