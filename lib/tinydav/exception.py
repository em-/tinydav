# Exceptions for the tinydav WebDAV client.
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
"""Exceptions for the tinydav WebDAV client."""
from httplib import CONFLICT


class HTTPError(Exception):
    """Base exception class for HTTP errors.

    response -- httplib.Response object.
    method -- String with uppercase method name.

    This object has the following attributes:
      response -- The HTTPResponse object.
    
    """
    def __init__(self, response, method):
        Exception.__init__(self)
        self.response = response


class HTTPUserError(HTTPError):
    """Exception class for 4xx HTTP errors."""


class HTTPServerError(HTTPError):
    """Exception class for 5xx HTTP errors."""


class WebDAVUserError(HTTPUserError):
    """Exception class for 4xx HTTP errors used by WebDAVClient."""
    def __init__(self, response, method):
        # RFC 2818, 8.10.4 Depth and Locking
        # If the lock cannot be granted to all resources, a 409 (Conflict)
        # status code MUST be returned with a response entity body containing
        # a multistatus XML element describing which resource(s) prevented
        # the lock from being granted.
        if (method == "LOCK") and (self == CONFLICT):
            response.set_multistatus()
        super(WebDAVUserError, self).__init__(response, method)


class WebDAVServerError(HTTPUserError):
    """Exception class for 5xx HTTP errors used by WebDAVClient."""


