# Mock object for unittests.
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
"""Mock object for unittests."""

from collections import defaultdict
from contextlib import contextmanager
from functools import partial
from StringIO import StringIO
import urllib2


@contextmanager
def injected(func, **kwargs):
    """Inject vars into a function or method while in context mode."""
    # recognize methods
    if hasattr(func, "im_func"):
        func = func.im_func
    # save and replace current function globals as to kwargs
    func_globals = func.func_globals
    saved = dict((k, func_globals[k]) for k in kwargs)
    func_globals.update(kwargs)
    # context is now ready to be used
    yield
    # restore previous state
    func_globals.update(saved)


@contextmanager
def replaced(obj, **attrs):
    """Replace attribute in object while in context mode."""
    # save and replace current attributes
    saved = dict((k, getattr(obj,k)) for k in attrs)
    obj.__dict__.update(attrs)
    # context is ready
    yield
    # restore previous state
    obj.__dict__.update(saved)


def omnivore_func(retval=None, exception=None):
    """Return a function accepting any number of args and act accordingly.

    retval -- Returned function returns this value on call.
    exception -- If not None, this will be raised by the returned function.

    """
    def omnivore(*args, **kwargs):
        omnivore.callcount += 1
        if exception is not None:
            raise exception
        return retval
    omnivore.callcount = 0
    return omnivore


class Omnivore(object):
    """Omnivore class.

    Return pre-defined values or raise predefined exceptions an any method
    that may be called, including __call__.

    """

    def __init__(self, **kwargs):
        """Initialize with return values.

        **kwargs -- Key is the method name, value is the returned value. If
                    the value is an instance of Exception, it will be raised.

        """
        self.__name__ = "Omnivore"
        self.retvals = dict()
        for (key, value) in kwargs.iteritems():
            self.retvals[key] = iter(value)
        self.called = defaultdict(list)

    def __enter__(self):
        self.called["__enter__"] = True
        return self

    def __exit__(exctype, excvalue, exctb):
        self.called["__exit__"] = (exctype, excvalue, exctb)

    def method(self, methodname, *args, **kwargs):
        self.called[methodname].append((args, kwargs))
        generator = self.retvals.get(methodname)
        if generator is None:
            return None
        value = generator.next()
        if isinstance(value, Exception):
            raise value
        return value

    def __getattr__(self, name):
        return partial(self.method, name)

    def __call__(self, *args, **kwargs):
        return self.method("__call__", *args, **kwargs)


class HTTPConnection(object):
    """Mock httplib.HTTPConnection object."""

    def __init__(self):
        # input
        self.method = None
        self.path = None
        self.body = None
        self.headers = None
        # output
        self.response = Response()
        self.closed = False

    def request(self, method, path, body=None, headers=None):
        self.method = method
        self.path = path
        self.body = body
        self.headers = headers

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class ModuleProxy(object):
    """Mock module. Must be instantiated."""

    def __init__(self, module):
        self.__module = module

    def __getattr__(self, name):
        return getattr(self.__module, name)


class Asyncore(object):
    """Mock asyncore."""

    class dispatcher(object):
        pass

    def __init__(self):
        self.custommap = False

    def loop(self, map=None):
        if map is not None:
            self.custommap = True


class Response(urllib2.HTTPError):
    """Mock urllib2 response object."""

    def __init__(self):
        self.code = None
        self.content = ""
        self.version = 11
        self.reason = "The reason"
        self.headers = dict()
        self.status = 200

    def getheaders(self):
        return self.headers

    def read(self):
        return self.content


class Filter(object):
    """Mock filter object from mod_python."""

    def __init__(self, indata=""):
        self.req = Request()
        self.passed_on = False
        self.closed = False
        self.data = StringIO(indata)
        self.writtendata = StringIO()

    def read(self, bytes):
        return self.data.read(bytes)

    def write(self, data):
        self.writtendata.write(data)

    def pass_on(self):
        self.passed_on = True

    def close(self):
        self.closed = True

class Request(object):
    """Mock request object from mod_python."""

    def __init__(self):
        self.readdata = ""
        self.readcalled = False
        self.writtendata = ""
        self.writecalled = False
        self.the_request = ""
        self.unparsed_uri = ""
        self.uri = ""
        self.headers_in = dict()
        self.headers_out = dict()
        self.err_headers_out = dict()
        self.content_type = ""
        self.filename = ""
        self.status = None
        self.prev = None
        self.internallyredirected = None
        self.method = ""
        self.proxyreq = None
        self.user = None

    def read(self, buffer):
        self.readcalled = True
        return self.readdata

    def write(self, data):
        self.writecalled = True
        self.writtendata = data

    def construct_url(self, foo):
        return "newuri"

    def log_error(self, msg, level=None):
        self.logmessage = msg
        self.loglevel = level

    def internal_redirect(self, uri):
        self.internallyredirected = uri


class apache(object):
    """Mock apache module from mod_python."""

    # proxy constant
    PROXYREQ_REVERSE = "reverseproxy"
    # return values for apache
    OK = "OK"
    DECLINED = "DECLINED"
    DONE = "DONE"
    HTTP_CONTINUE = 100
    HTTP_SWITCHING_PROTOCOLS = 101
    HTTP_PROCESSING = 102
    HTTP_OK = 200
    HTTP_CREATED = 201
    HTTP_ACCEPTED = 202
    HTTP_NON_AUTHORITATIVE = 203
    HTTP_NO_CONTENT = 204
    HTTP_RESET_CONTENT = 205
    HTTP_PARTIAL_CONTENT = 206
    HTTP_MULTI_STATUS = 207
    HTTP_MULTIPLE_CHOICES = 300
    HTTP_MOVED_PERMANENTLY = 301
    HTTP_MOVED_TEMPORARILY = 302
    HTTP_SEE_OTHER = 303
    HTTP_NOT_MODIFIED = 304
    HTTP_USE_PROXY = 305
    HTTP_TEMPORARY_REDIRECT = 307
    HTTP_BAD_REQUEST = 400
    HTTP_UNAUTHORIZED = 401
    HTTP_PAYMENT_REQUIRED = 402
    HTTP_FORBIDDEN = 403
    HTTP_NOT_FOUND = 404
    HTTP_METHOD_NOT_ALLOWED = 405
    HTTP_NOT_ACCEPTABLE = 406
    HTTP_PROXY_AUTHENTICATION_REQUIRED = 407
    HTTP_REQUEST_TIME_OUT = 408
    HTTP_CONFLICT = 409
    HTTP_GONE = 410
    HTTP_LENGTH_REQUIRED = 411
    HTTP_PRECONDITION_FAILED = 412
    HTTP_REQUEST_ENTITY_TOO_LARGE = 413
    HTTP_REQUEST_URI_TOO_LARGE = 414
    HTTP_UNSUPPORTED_MEDIA_TYPE = 415
    HTTP_RANGE_NOT_SATISFIABLE = 416
    HTTP_EXPECTATION_FAILED = 417
    HTTP_UNPROCESSABLE_ENTITY = 422
    HTTP_LOCKED = 423
    HTTP_FAILED_DEPENDENCY = 424
    HTTP_INTERNAL_SERVER_ERROR = 500
    HTTP_NOT_IMPLEMENTED = 501
    HTTP_BAD_GATEWAY = 502
    HTTP_SERVICE_UNAVAILABLE = 503
    HTTP_GATEWAY_TIME_OUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    HTTP_VARIANT_ALSO_VARIES = 506
    HTTP_INSUFFICIENT_STORAGE = 507
    HTTP_NOT_EXTENDED = 510
    # logging constants
    APLOG_DEBUG = 0
    APLOG_INFO = 1
    APLOG_WARNING = 2
    APLOG_ERR = 3
    APLOG_CRIT = 4
