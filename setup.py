"""Setup script for audio-metadata-completionist."""
from setuptools import find_packages, setup

setup(
    packages=find_packages(exclude=["tests*"]),
    package_data={
        "src": ["py.typed"],
    },
)
