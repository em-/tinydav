#!/usr/bin/python
# coding: utf-8
#
# Copyright (C) 2009  Manuel Hermann <manuel-hermann@gmx.net>
from distutils.core import setup

VERSION = "0.6.0"
DOWNLOAD = "http://tinydav.googlecode.com/files/tinydav-%s.tar.gz" % VERSION
DESCRIPTION = "An easy-to-use HTTP and WebDAV client."
LONG_DESCRIPTION = """\
An easy-to-use HTML and WebDAV client library for Python
--------------------------------------------------------

The tinydav library contains a HTTP client supporting HTTP and HTTPS.

Features:
 - Cookie support
 - SSL support
 - HTTP methods: OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT

Features of the WebDAV client:
 - All features of the HTTP client
 - WebDAV methods: MKCOL, PROPFIND, PROPPATCH, DELETE, COPY, MOVE, LOCK, UNLOCK
 - RFC 3253 REPORT (rudimentary)

This version requires Python 2.5 or later; Python 3 is not supportet, yet.
"""

CLASSIFIERS = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.5",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Development Status :: 4 - Beta",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: "\
        "GNU Library or Lesser General Public License (LGPL)",
    "Operating System :: OS Independent",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

if __name__ == "__main__":
    setup(
        name="tinydav",
        packages=["tinydav"],
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        author="Manuel Hermann",
        author_email="manuel-hermann@gmx.net",
        url="http://code.google.com/p/tinydav/",
        download_url=DOWNLOAD,
        keywords = ["http", "https", "webdav", "library", "client"],
        license="LGPL",
        classifiers=CLASSIFIERS,
    )

