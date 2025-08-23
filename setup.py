#!/usr/bin/env python

from __future__ import absolute_import
from setuptools import setup

if __name__ == '__main__':
    # Provide static information in setup.json
    # such that it can be discovered automatically
    setup(
        packages=["figure"],
        name="hcofs-co2-discover-section",
        author="Leopold Talirz",
        author_email="info@materialscloud.org",
        description="A template for DISCOVER sections using bokeh server.",
        license="MIT",
        classifiers=["Programming Language :: Python"],
        version="0.1.0",
        install_requires=[
            "aiida-core~=2.7.0pre1",
            "bokeh>=1.4.0,<1.5",
            "jsmol-bokeh-extension~=0.2.1",
            "pandas>=1.3.0,<1.4",
            "holoviews>=1.12,<1.14",
            "xarray>=0.14.1,<0.16",
            "datashader>=0.10.0,<0.13",
            "panel>=0.8.1,<0.9",  # bumping panel to 0.8.1 to avoid conflict
            "param>=1.9,<1.11",
            "jinja2>=3.0.0,<3.2",
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
