#!/usr/bin/env python

from __future__ import absolute_import
from setuptools import setup

if __name__ == '__main__':
    # Provide static information in setup.json
    # such that it can be discovered automatically
    setup(
        packages=["figure"],
        name="hdofs-co2-discover-section",
        author="Leopold Talirz",
        author_email="info@materialscloud.org",
        description="A template for DISCOVER sections using bokeh server.",
        license="MIT",
        classifiers=["Programming Language :: Python"],
        version="0.1.0",
        install_requires=[
            "aiida-core~=1.1.1",
            "bokeh~=1.4.0",
            #"jsmol-bokeh-extension~=0.2.1",
            "holoviews~=1.12",
            "xarray~=0.14.1",
            "datashader~=0.10.0",
            "panel~=0.7.0",
            "param~=1.9",
        ],
        extras_require={
            "pre-commit":
            ["pre-commit==1.17.0", "prospector==1.2.0", "pylint==2.4.4"],
            "testing": [
                "pg8000~=1.13",
                "pgtest~=1.3,>=1.3.1",
                "pytest~=5.3",
            ]
        })
