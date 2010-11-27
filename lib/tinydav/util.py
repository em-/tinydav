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
    # RFC 2517, 9.3 Destination Header
    # Destination = "Destination" ":" absoluteURI
    netloc = "%s:%d" % (httpclient.host, httpclient.port)
    parts = (httpclient.protocol, netloc, uri, None, None)
    return urlparse.urlunsplit(parts)


def extract_namespace(key):
    """Return the namespace in key or None, when no namespace is in key.

    key -- String to get namespace from

    """
    if not key.startswith("{"):
        return None
    return key[1:].split("}")[0]


def get_depth(depth, allowed=("0", "1", "infinity")):
    """Return string with depth.

    depth -- Depth value to check.
    allowed -- Iterable with allowed depth header values.

    Raise ValueError, if an illegal depth was given.

    """
    depth = str(depth).lower()
    if depth not in allowed:
        raise ValueError("illegal depth %s" % depth)
    return depth

