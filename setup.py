from setuptools import setup, find_packages

setup(
    name="calendar_manager",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1.7",
    ],
    entry_points={
        "console_scripts": [
            "calendar-manager=calendar_manager.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    description="A CLI application for managing calendars",
    keywords="calendar, cli, management",
) 