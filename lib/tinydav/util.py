# Utility function for tinydav WebDAV client.
# Copyright (C) 2009  Manuel Hermann <manuel-hermann@gmx.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Utility function for tinydav WebDAV client."""

import urlparse


def make_destination(httpclient, uri):
    """Return correct destination header value.

    httpclient -- HTTPClient instance with protocol, host and port attribute.
    uri -- The destination path.

    """
    netloc = "%s:%d" % (httpclient.host, httpclient.port)
    parts = (httpclient.protocol, netloc, uri, None, None)
    return urlparse.urlunsplit(parts)

