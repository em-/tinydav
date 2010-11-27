#!/usr/bin/python
# coding: utf-8
#
# Created by Manuel Hermann <manuel-hermann@gmx.net>

# Importing setup from setuptools (external package) has the opportunity
# to run unittests via "python setup.py test"
from setuptools import setup


if __name__ == "__main__":
    setup(
        name="TinyDAV library",
        version="0.5.2",
        author="Manuel Hermann",
        author_email="manuel-hermann@gmx.net",
        description="Tiny WebDAV client.",
        # project files
        py_modules=[],
        packages=["tinydav"],
        package_dir={"": "lib"},
        package_data={},
        # additional dirs go here
        data_files=[],
        # only when using setup from setuptools
        test_suite="test.testloader.run",
    )

