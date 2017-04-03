#!/usr/bin/python3

from setuptools import setup
setup(
    name="chamelium-utils",
    scripts=[
        'utils/chamelium-screenshot',
        'utils/chamelium-hotplug',
        'utils/chamelium-vga-out',
        'utils/chamelium-edid'
    ]

    author="Lyude Paul",
    author_email="thatslyude@gmail.com",
    description="A set of utilities for controlling the Chamelium"
)
