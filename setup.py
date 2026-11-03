"""Setup script for JFView."""

from setuptools import setup, find_packages

setup(
    name="jfview",
    version="1.0.0",
    description="Image Viewer and Editor for Linux",
    author="JFView",
    packages=find_packages(),
    package_data={
        "jfview": ["resources/*"],
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15",
        "Pillow>=9.0",
        "numpy>=1.20",
    ],
    entry_points={
        "console_scripts": [
            "jfview=jfview.main:main",
        ],
    },
)
