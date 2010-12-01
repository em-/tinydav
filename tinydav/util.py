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

from email.encoders import encode_base64
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urlparse

__all__ = (
    "FakeHTTPRequest", "make_absolute", "make_multipart",
    "extract_namespace", "get_depth"
)

DEFAULT_CONTENT_TYPE = "application/octet-stream"


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
        return make_absolute(self._client, self._uri)

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


def make_absolute(httpclient, uri):
    """Return correct absolute URI.

    httpclient -- HTTPClient instance with protocol, host and port attribute.
    uri -- The destination path.

    """
    netloc = "%s:%d" % (httpclient.host, httpclient.port)
    parts = (httpclient.protocol, netloc, uri, None, None)
    return urlparse.urlunsplit(parts)


def make_multipart(content, default_encoding):
    """Return the headers and content for multipart/form-data.

    content -- Dict with content to POST. The dict values are expected to
               be unicode or decodable with us-ascii.
    default_encoding -- Send multipart with this encoding, if no special 
                        encoding was given with the content.

    """
    # RFC 2388 Returning Values from Forms:  multipart/form-data
    mime = MIMEMultipart("form-data")
    for (key, data) in content.iteritems():
        # are there explicit encodings/content-types given?
        try:
            (value, encoding) = data
        except ValueError:
            value = data
            encoding = default_encoding
        # cope with file-like objects
        try:
            value = value.read()
        except AttributeError:
            # no file-like object
            encoding = encoding if encoding else default_encoding
            sub_part = MIMEText(value, "plain", encoding)
        else:
            # encoding is content-type when treating with file-like objects
            if encoding:
                (maintype, subtype) = encoding.split("/")
                sub_part = MIMEBase(maintype, subtype)
                sub_part.set_payload(value)
                encode_base64(sub_part)
            else:
                sub_part = MIMEApplication(value, DEFAULT_CONTENT_TYPE)
        sub_part.add_header("content-disposition", "form-data", name=key)
        mime.attach(sub_part)
    # mime.items must be called after mime.as_string when the headers shall
    # contain the boundary
    complete_mime = mime.as_string()
    headers = dict(mime.items())
    # start after \n\n
    payload_start = complete_mime.index("\n\n") + 2
    payload = complete_mime[payload_start:]
    return (headers, payload)


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

