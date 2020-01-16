#!/usr/bin/env python

from __future__ import absolute_import
from setuptools import setup

if __name__ == '__main__':
    # Provide static information in setup.json
    # such that it can be discovered automatically
    setup(packages=["figure"],
          name="cofdb-discover-section",
          author="Leopold Talirz",
          author_email="info@materialscloud.org",
          description="A template for DISCOVER sections using bokeh server.",
          license="MIT",
          classifiers=["Programming Language :: Python"],
          version="0.1.1",
          install_requires=[
              "bokeh~=1.4.0",
              "jsmol-bokeh-extension~=0.2.1",
              "holoviews[recommended]",
              "xarray",
              "datashader",
              "pandas~=0.24.2",
              "panel",
              "param",
              "jupyter",
          ],
          extras_require={
              "pre-commit":
              ["pre-commit==1.17.0", "prospector==1.2.0", "pylint==2.4.4"]
          })
