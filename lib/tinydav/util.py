# Utility function for tinydav WebDAV client.
# Copyright (C) 2009  Manuel Hermann <manuel-hermann@gmx.net>
#
# This file is part of tinydav.
#
# tinydav is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Utility functions and classes for tinydav WebDAV client."""

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urlparse

__all__ = (
    "FakeHTTPRequest", "make_destination", "make_multipart",
    "extract_namespace", "get_depth"
)


class FakeHTTPRequest(object):
    """Fake HTTP request object needed for cookies.
    
    See http://docs.python.org/library/cookielib.html#cookiejar-and-filecookiejar-objects

    """
    def __init__(self, client, uri, headers):
        """Initialize the fake HTTP request object.

        client -- HTTPClient object or one of its subclasses.
        uri -- The URI to call.
        headers -- Headers dict to add cookie stuff to.

        """
        self._client = client
        self._uri = uri
        self._headers = headers

    def get_full_url(self):
        return make_destination(self._client, self._uri)

    def get_host(self):
        return self._client.host

    def is_unverifiable(self):
        return False

    def get_origin_req_host(self):
        return self.get_host()

    def get_type(self):
        return self._client.protocol

    def has_header(self, name):
        return (name in self._headers)

    def add_unredirected_header(self, key, header):
        self._headers[key] = header


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


def make_multipart(content, encoding):
    """Return the content as multipart/form-data. RFC 2388

    content -- Dict with content to POST. The dict values are expected to
               be unicode or decodable with us-ascii.
    encoding -- Send multipart with this encoding.

    """
    # RFC 2388 Returning Values from Forms:  multipart/form-data
    mime = MIMEMultipart("form-data")
    for (key, value) in content.iteritems():
        # send file-like objects as octet-streams
        if hasattr(value, "read"):
            sub_part = MIMEApplication(value.read(), "octet-stream")
        else:
            sub_part = MIMEText(str(value), "plain", encoding)
        sub_part.add_header("Content-Disposition", "form-data", name=key)
        mime.attach(sub_part)
    return mime.as_string()


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

