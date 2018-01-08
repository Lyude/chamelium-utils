#!/usr/bin/python3

import setuptools
from setuptools import setup
setup(
    name="chamelium-utils",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'chamelium = chamelium_utils.main:__main__'
        ]
    },

    author="Lyude Paul",
    author_email="thatslyude@gmail.com",
    description="A set of utilities for controlling the Chamelium"
)
