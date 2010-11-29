# The tinydav WebDAV client.
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
"""The tinydav WebDAV client."""

from __future__ import with_statement
from contextlib import closing
from functools import wraps
from httplib import MULTI_STATUS
from StringIO import StringIO
from xml.etree.ElementTree import ElementTree, Element, SubElement, tostring
from xml.parsers.expat import ExpatError
import httplib
import sys
import urllib

from tinydav import creator, util


PYTHON2_6 = (sys.version_info >= (2, 6))

# RFC 2518, 9.8 Timeout Request Header
# The timeout value for TimeType "Second" MUST NOT be greater than 2^32-1.
MAX_TIMEOUT = 4294967295


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
        return util.make_destination(self._client, self._uri)

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


class HTTPError(Exception):
    """Exception for any error that occurs."""

    def __init__(self, carry):
        """Initialize the HTTPError.

        carry -- The original exception.

        """
        self.carry = carry


class HTTPResponse(int):
    """Result from HTTP request."""

    def __new__(cls, response):
        """Construct HTTPResponse.

        response -- Response object from httplib.

        """
        return int.__new__(cls, response.status)

    def __init__(self, response):
        """Initialize the HTTPResponse.

        response -- Response object from httplib.

        """
        self.response = response
        self.headers = dict(response.getheaders())
        self.content = response.read()
        version = "HTTP/%s.%s" % tuple(str(response.version))
        self.statusline = "%s %d %s"\
                        % (version, response.status, response.reason)

    def __repr__(self):
        """Return representation string."""
        return "<%s: %d>" % (self.__class__.__name__, self)


class WebDAVResponse(HTTPResponse):
    """Result from WebDAV request."""

    def __init__(self, response):
        """Initialize the WebDAVResult.

        response -- Response object from httplib.

        """
        super(WebDAVResponse, self).__init__(response)
        self._etree = ElementTree()
        # on XML parsing error set this to the raised exception
        self.parse_error = None
        if self == MULTI_STATUS:
            try:
                self._etree.parse(StringIO(self.content))
            except ExpatError, e:
                self.parse_error = e
                # don't fail on further processing
                self._etree.parse(StringIO("<root><empty/></root>"))

    def __len__(self):
        """Return the number of responses in a multistatus response.

        When the response was no multistatus the return value is 1.

        """
        if self == MULTI_STATUS:
            # RFC 2518, 12.9 multistatus XML Element
            # <!ELEMENT multistatus (response+, responsedescription?) >
            return len(self._etree.findall("/{DAV:}response"))
        return 1

    def __iter__(self):
        """Iterator over the response.

        Yield MultiStatusResponse instances for each response in a 207
        response.
        Yield self otherwise.

        """
        if self == MULTI_STATUS:
            # RFC 2518, 12.9 multistatus XML Element
            # <!ELEMENT multistatus (response+, responsedescription?) >
            for response in self._etree.findall("/{DAV:}response"):
                yield MultiStatusResponse(response)
        else:
            yield self


class MultiStatusResponse(int):
    """Wrapper for multistatus responses."""

    def __new__(cls, response):
        """Create instance with status code as int value."""
        # RFC 2518, 12.9.1 response XML Element
        # <!ELEMENT response (href, ((href*, status)|(propstat+)),
        # responsedescription?) >
        statusline = response.findtext("{DAV:}propstat/{DAV:}status")
        status = int(statusline.split()[1])
        return int.__new__(cls, status)

    def __init__(self, response):
        """Initialize the MultiStatusResponse.

        response -- ElementTree element: response-tag.

        """
        self.response = response
        self._href = None
        self._statusline = None
        self._namespaces = None

    def __repr__(self):
        """Return representation string."""
        return "<%s: %d>" % (self.__class__.__name__, self)

    def __getitem__(self, name):
        """Return requested property as ElementTree element.

        name -- Name of the property with namespace. No namespace needed for
                DAV properties.

        """
        # check, whether its a default DAV property name
        if not name.startswith("{"):
            name = "{DAV:}%s" % name
        # RFC 2518, 12.9.1.1 propstat XML Element
        # <!ELEMENT propstat (prop, status, responsedescription?) >
        prop = self.response.find("{DAV:}propstat/{DAV:}prop/%s" % name)
        if prop is None:
            raise KeyError(name)
        return prop

    def __iter__(self):
        """Iterator over propertynames with their namespaces."""
        return self.iterkeys()

    def keys(self):
        """Return list of propertynames with their namespaces.

        No namespaces for DAV properties.

        """
        return list(self.iterkeys())

    def iterkeys(self, cut_dav_ns=True):
        """Iterate over propertynames with their namespaces.

        cut_dav_ns -- No namespaces for DAV properties when this is True.

        """
        for (tagname, value) in self.iteritems(cut_dav_ns):
            yield tagname

    def items(self):
        """Return list of 2-tuples with propertyname and value."""
        return list(self.iteritems())

    def iteritems(self, cut_dav_ns=True):
        """Iterate list of 2-tuples with propertyname and value.

        cut_dav_ns -- No namespaces for DAV properties when this is True.

        """
        # RFC 2518, 12.11 prop XML element
        # <!ELEMENT prop ANY>
        props = self.response.findall("{DAV:}propstat/{DAV:}prop/*")
        for prop in props:
            tagname = prop.tag
            if cut_dav_ns and tagname.startswith("{DAV:}"):
                tagname = tagname[6:]
            yield (tagname, prop.text)

    def get(self, key, default=None, namespace=None):
        """Return value for requested property.

        key -- Property name with namespace. Namespace may be omitted, when
               namespace-argument is given, or Namespace is DAV:
        default -- Return this value when key does not exist.
        namespace -- The namespace in which the property lives in. Must be
                     given, when the key value has no namespace defined and
                     the namespace ist not DAV:.

        """
        if namespace:
            key = "{%s}%s" % (namespace, key)
        try:
            return self[key]
        except KeyError:
            return default

    @property
    def statusline(self):
        """Return the status line for this response."""
        if self._statusline is None:
            # RFC 2518, 12.9.1.2 status XML Element
            # <!ELEMENT status (#PCDATA) >
            statustag = self.response.findtext("{DAV:}propstat/{DAV:}status")
            self._statusline = statustag
        return self._statusline

    @property
    def href(self):
        """Return the href for this response."""
        if self._href is None:
            # RFC 2518, 12.3 href XML Element
            # <!ELEMENT href (#PCDATA)>
            self._href = self.response.findtext("{DAV:}href")
        return self._href

    @property
    def namespaces(self):
        """Return frozenset of namespaces."""
        if self._namespaces is None:
            self._namespaces = frozenset(util.extract_namespace(key)
                                         for key in self.iterkeys(False)
                                         if util.extract_namespace(key))
        return self._namespaces


class HTTPClient(object):
    """Mini HTTP client."""

    ResponseType = HTTPResponse

    def __init__(self, host, port=80, user=None, password="", protocol="http"):
        """Initialize the WebDAV client.

        host -- WebDAV server host.
        port -- WebDAV server port.
        user -- Login name.
        password -- Password for login.
        protocol -- Either "http" or "https".

        """
        assert isinstance(port, int)
        self.host = host
        self.port = port
        self.protocol = protocol
        self.headers = dict()
        self.cookie = None
        # set header for basic authentication
        if user is not None:
            self.setbasicauth(user, password)

    def _getconnection(self):
        """Return HTTP(S)Connection object depending on set protocol."""
        if self.protocol == "http":
            return httplib.HTTPConnection(self.host, self.port)
        return httplib.HTTPSConnection(self.host, self.port)

    def _request(self, method, uri, content=None, headers=None):
        """Make request and return response.

        method -- Request method.
        uri -- URI the request is for.
        content -- The content of the request. May be None.
        headers -- If given, a mapping with additonal headers to send.

        """
        if not uri.startswith("/"):
            uri = "/%s" % uri

        headers = dict() if (headers is None) else headers

        # handle cookies, if necessary
        if self.cookie is not None:
            fake_request = FakeHTTPRequest(self, uri, headers)
            self.cookie.add_cookie_header(fake_request)

        con = self._getconnection()
        try:
            with closing(con):
                con.request(method, uri, content, headers)
                response = self.ResponseType(con.getresponse())
        except Exception, err:
            raise HTTPError(err)
        else:
            if self.cookie is not None:
                # make httplib.Response compatible with urllib2.Response
                response.response.info = lambda: response.response.msg
                self.cookie.extract_cookies(response.response, fake_request)
            return response

    def _prepare(self, uri, headers, query=None):
        """Return 2-tuple with prepared version of uri and headers.

        The headers will contain the authorization headers, if given.

        uri -- URI the request is for.
        headers -- Mapping with additional headers to send.
        query -- Mapping with key/value-pairs to be added as query to the URI.

        """
        uri = urllib.quote(uri)
        # collect headers
        sendheaders = dict(self.headers)
        if headers:
            sendheaders.update(headers)
        # construct query string
        if query:
            querystr = urllib.urlencode(query)
            uri = "%s?%s" % (uri, querystr)
        return (uri, sendheaders)

    def setbasicauth(self, user, password):
        """Set authorization header for basic auth.

        user -- Username
        password -- Password for user.

        """
        # RFC 2068, 11.1 Basic Authentication Scheme
        # basic-credentials = "Basic" SP basic-cookie
        # basic-cookie   = <base64 [7] encoding of user-pass,
        # except not limited to 76 char/line>
        # user-pass   = userid ":" password
        # userid      = *<TEXT excluding ":">
        # password    = *TEXT
        userpw = "%s:%s" % (user, password)
        auth = userpw.encode("base64").rstrip()
        self.headers["Authorization"] = "Basic %s" % auth

    def setcookie(self, cookie):
        """Set cookie class to be used in requests.

        cookie -- Cookie class from cookielib.

        """
        self.cookie = cookie

    def options(self, uri, headers=None):
        """Make OPTIONS request and return status.

        uri -- URI of the request.
        headers -- Optional mapping with headers to send.

        Raise HTTPError on HTTP errors.

        """
        (uri, headers) = self._prepare(uri, headers)
        return self._request("OPTIONS", uri, None, headers)

    def get(self, uri, headers=None, query=None):
        """Make GET request and return status.

        uri -- URI of the request.
        headers -- Optional mapping with headers to send.
        query -- Mapping with key/value-pairs to be added as query to the URI.

        Raise HTTPError on HTTP errors.

        """
        (uri, headers) = self._prepare(uri, headers, query)
        return self._request("GET", uri, None, headers)

    def head(self, uri, headers=None, query=None):
        """Make HEAD request and return status.

        uri -- URI of the request.
        headers -- Optional mapping with headers to send.
        query -- Mapping with key/value-pairs to be added as query to the URI.

        Raise HTTPError on HTTP errors.

        """
        (uri, headers) = self._prepare(uri, headers, query)
        return self._request("HEAD", uri, None, headers)

    def post(self, uri, content="", headers=None, query=None):
        """Make POST request and return HTTPResponse.

        uri -- Path to post data to.
        content -- File descriptor or string with content to POST.
        headers -- If given, must be a mapping with headers to set.
        query -- Mapping with key/value-pairs to be added as query to the URI.

        Raise HTTPError on HTTP errors.

        """
        (uri, headers) = self._prepare(uri, headers, query)
        return self._request("POST", uri, content, headers)

    def put(self, uri, fileobject, headers=None):
        """Make PUT request and return status.

        uri -- Path for PUT.
        fileobject -- File object with content to PUT.
        headers -- If given, must be a dict with headers to send.

        Raise HTTPError on HTTP errors.

        """
        (uri, headers) = self._prepare(uri, headers)
        # use 2.6 feature, if running under this version
        data = fileobject if PYTHON2_6 else fileobject.read()
        return self._request("PUT", uri, data, headers)

    def delete(self, uri, headers=None):
        """Make DELETE request and return HTTPResponse.

        uri -- Path to post data to.
        headers -- If given, must be a mapping with headers to set.

        Raise HTTPError on HTTP errors.

        """
        (uri, headers) = self._prepare(uri, headers)
        return self._request("DELETE", uri, None, headers)

    def trace(self, uri, maxforwards=None, via=None, headers=None):
        """Make TRACE request and return HTTPResponse.

        uri -- Path to post data to.
        maxforwards -- Number of maximum forwards. May be None.
        via -- If given, an iterable containing each station in the form
               stated in RFC2616, section 14.45.
        headers -- If given, must be a mapping with headers to set.

        Raise ValueError, if maxforward is not an int or convertable to
        an int.
        Raise TypeError, if via is not an iterable of string.
        Raise HTTPError on HTTP errors.

        """
        (uri, headers) = self._prepare(uri, headers)
        if maxforwards is not None:
            # RFC 2068, 14.31 Max-Forwards
            # Max-Forwards   = "Max-Forwards" ":" 1*DIGIT
            int(maxforwards)
            headers["Max-Forwards"] = str(maxforwards)
        # RFC 2068, 14.44 Via
        if via:
            headers["Via"] = ", ".join(via)
        return self._request("TRACE", uri, None, headers)

    def connect(self, uri, headers=None):
        """Make CONNECT request and return HTTPResponse.

        uri -- Path to post data to.
        headers -- If given, must be a mapping with headers to set.

        Raise HTTPError on HTTP errors.

        """
        (uri, headers) = self._prepare(uri, headers)
        return self._request("CONNECT", uri, None, headers)


class CoreWebDAVClient(HTTPClient):
    """Basic WebDAVClient specified in RFC 2518."""

    ResponseType = WebDAVResponse

    def _preparecopymove(self, source, destination, depth, overwrite, headers):
        """Return prepared for copy/move request version of uri and headers."""
        # RFC 2518, 8.8.3 COPY for Collections
        # A client may submit a Depth header on a COPY on a collection with a
        # value of "0" or "infinity".
        depth = util.get_depth(depth, ("0", "infinity"))
        headers = dict() if (headers is None) else headers
        (source, headers) = self._prepare(source, headers)
        # RFC 2518, 8.8 COPY Method
        # The Destination header MUST be present.
        # RFC 2518, 8.9 MOVE Method
        # Consequently, the Destination header MUST be present on all MOVE
        # methods and MUST follow all COPY requirements for the COPY part of
        # the MOVE method.
        headers["Destination"] = util.make_destination(self, destination)
        # RFC 2518, 8.8.3 COPY for Collections
        # A client may submit a Depth header on a COPY on a collection with
        # a value of "0" or "infinity".
        # RFC 2518, 8.9.2 MOVE for Collections
        if source.endswith("/"):
            headers["Depth"] = depth
        # RFC 2518, 8.8.4 COPY and the Overwrite Header
        #           8.9.3 MOVE and the Overwrite Header
        # If a resource exists at the destination and the Overwrite header is
        # "T" then prior to performing the copy the server MUST perform a
        # DELETE with "Depth: infinity" on the destination resource.  If the
        # Overwrite header is set to "F" then the operation will fail.
        if overwrite is not None:
            headers["Overwrite"] = "T" if overwrite else "F"
        return (source, headers)

    def mkcol(self, uri, headers=None):
        """Make MKCOL request and return status.

        uri -- Path to create.
        headers -- If given, must be a dict with headers to send.

        Raise WebDAVError HTTP errors.

        """
        (uri, headers) = self._prepare(uri, headers)
        return self._request("MKCOL", uri, None, headers)

    def propfind(self, uri, depth=0, names=False,
                 properties=None, include=None, namespaces=None,
                 headers=None):
        """Make PROPFIND request and return status.

        uri -- Path for PROPFIND.
        depth -- Depth for PROFIND request. Default is zero.
        names -- If True, only the available namespace names are returned.
        properties -- If given, an iterable with all requested properties is
                      expected.
        include -- If properties is not given, then additional properties can
                   be requested with this argument.
        namespaces -- Mapping with namespaces for given properties, if needed.
        headers -- If given, must be a dict with headers to send.

        Raise ValueError, if illegal depth was given or if properties and
        include argunemtns were given.
        Raise WebDAVError on HTTP errors.

        """
        namespaces = dict() if (namespaces is None) else namespaces
        # RFC 2517, 8.1 PROPFIND
        # A client may submit a Depth header with a value of "0", "1", or
        # "infinity" with a PROPFIND on a collection resource with internal
        # member URIs.
        depth = util.get_depth(depth)
        # check mutually exclusive arguments
        if all([properties, include]):
            raise ValueError("properties and include are "
                                 "mutually exclusive")
        (uri, headers) = self._prepare(uri, headers)
        # additional headers needed for PROPFIND
        headers["Depth"] = depth
        headers["Content-Type"] = "application/xml"
        content = creator.create_propfind(names, properties,
                                          include, namespaces)
        return self._request("PROPFIND", uri, content, headers)

    def proppatch(self, uri, setprops=None, delprops=None,
                  namespaces=None, headers=None):
        """Make PROPPATCH request and return status.

        uri -- Path to resource to set properties.
        setprops -- Mapping with properties to set.
        delprops -- Iterable with properties to remove.
        namespaces -- dict with namespaces: name -> URI.
        headers -- If given, must be a dict with headers to send.

        Either setprops or delprops or both of them must be given, else
        ValueError will be risen.

        """
        # RFC 2517, 12.13 propertyupdate XML element
        # <!ELEMENT propertyupdate (remove | set)+ >
        if not any((setprops, delprops)):
            raise ValueError("setprops and/or delprops must be given")
        (uri, headers) = self._prepare(uri, headers)
        # additional header for proppatch
        headers["Content-Type"] = "application/xml"
        content = creator.create_proppatch(setprops, delprops, namespaces)
        return self._request("PROPPATCH", uri, content, headers)

    def delete(self, uri, headers=None):
        """Make DELETE request and return WebDAVResponse.

        uri -- Path of resource or collection to delete.
        headers -- If given, must be a mapping with headers to set.

        Raise WebDAVError HTTP errors.

        """
        headers = dict() if (headers is None) else headers
        if uri.endswith("/"):
            # RFC 2517, 8.6.2 DELETE for Collections
            # A client MUST NOT submit a Depth header with a DELETE on a
            # collection with any value but infinity.
            headers["Depth"] = "infinity"
        return super(CoreWebDAVClient, self).delete(uri, headers)

    def copy(self, source, destination, depth="infinity",
             overwrite=None, headers=None):
        """Make COPY request and return WebDAVResponse.

        source -- Path of resource to copy.
        destination -- Path of destination to copy source to.
        depth -- Either 0 or "infinity". Default is the latter.
        overwrite -- If not None, then a boolean indicating whether the
                     Overwrite header ist set to "T" (True) or "F" (False).
        headers -- If given, must be a mapping with headers to set.

        Raise WebDAVError HTTP errors.

        """
        (source, headers) = self._preparecopymove(source, destination, depth,
                                                  overwrite, headers)
        return self._request("COPY", source, None, headers)

    def move(self, source, destination, depth="infinity",
             overwrite=None, headers=None):
        """Make MOVE request and return WebDAVResponse.

        source -- Path of resource to move.
        destination -- Path of destination to move source to.
        depth -- Either 0 or "infinity". Default is the latter.
        overwrite -- If not None, then a boolean indicating whether the
                     Overwrite header ist set to "T" (True) or "F" (False).
        headers -- If given, must be a mapping with headers to set.

        Raise WebDAVError HTTP errors.
        Raise ValueError, if an illegal depth was given.

        """
        # RFC 2518, 8.9.2 MOVE for Collections
        # A client MUST NOT submit a Depth header on a MOVE on a collection
        # with any value but "infinity".
        if source.endswith("/") and (depth != "infinity"):
            raise ValueError("depth must be infinity when moving collections")
        (source, headers) = self._preparecopymove(source, destination, depth,
                                                  overwrite, headers)
        return self._request("MOVE", source, None, headers)

    def lock(self, uri, scope="exclusive", type_="write", owner=None,
             timeout=None, depth=None, headers=None):
        """Make LOCK request and return DAVLock instance.

        uri -- Resource to get lock on.
        scope -- Lock scope: One of "exclusive" (default) or "shared".
        type_ -- Lock type: "write" (default) only. Any other value allowed by
                 this library.
        owner -- Content of owner element. May be None, a string or an
                 ElementTree element.
        timeout -- Value for the timeout header. Either "infinite" or a number
                   representing the seconds (not greater than 2^32 - 1).

        """
        (uri, headers) = self._prepare(uri, headers)
        # RFC 2517, 9.8 Timeout Request Header
        # TimeOut = "Timeout" ":" 1#TimeType
        # TimeType = ("Second-" DAVTimeOutVal | "Infinite" | Other)
        # DAVTimeOutVal = 1*digit
        # Other = "Extend" field-value   ; See section 4.2 of [RFC2068]
        if timeout is not None:
            try:
                timeout = int(timeout)
            except ValueError: # no number
                if timeout.lower() == "infinite":
                    value = "Infinite"
                else:
                    raise ValueError("either number of seconds or 'infinite'")
            else:
                if timeout > MAX_TIMEOUT:
                    raise ValueError("timeout too big")
                value = "Second-%d" % int(timeout)
            headers["Timeout"] = value
        # RFC 2517, 8.10.4 Depth and Locking
        # Values other than
        # 0 or infinity MUST NOT be used with the Depth header on a LOCK
        # method.
        if depth is not None:
            headers["Depth"] = util.get_depth(depth, ("0", "infinity"))
        content = creator.create_lock(scope, type_, owner)
        return self._request("LOCK", uri, content, headers)


class ExtendedWebDAVClient(CoreWebDAVClient):
    """WebDAV client with versioning extensions (RFC 3253)."""
    def report(self, uri, depth=0, properties=None,
               elements=None, namespaces=None, headers=None):
        """Make a REPORT request and return status.

        uri -- Resource or collection to get report for.
        depth -- Either 0 or 1 or "infinity". Default is zero.
        properties -- If given, an iterable with all requested properties is
                      expected.
        elements -- An iterable with additional XML elements.
        namespaces -- Mapping with namespaces for given properties, if needed.
        headers -- If given, must be a mapping with headers to set.

        Raise WebDAVError HTTP errors.
        Raise ValueError, if an illegal depth value was given.

        """
        depth = util.get_depth(depth)
        (uri, headers) = self._prepare(uri, headers)
        content = creator.create_report(properties, elements, namespaces)
        # RFC 3253, 3.6 REPORT Method
        # The request MAY include a Depth header.  If no Depth header is
        # included, Depth:0 is assumed.
        headers["Depth"] = depth
        headers["Content-Type"] = "application/xml"
        return self._request("REPORT", uri, content, headers)


class WebDAVClient(ExtendedWebDAVClient):
    """Mini WebDAV client."""
