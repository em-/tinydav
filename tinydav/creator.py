# Request creator function for tinydav WebDAV client.
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
"""Module with helper functions that generate XML requests."""

from xml.etree.ElementTree import Element, SubElement, tostring


_NS = {"xmlns": "DAV:"}


def _addnamespaces(elem, namespaces):
    """Add namespace definitions to a given XML element.

    elem -- ElementTree element to add namespaces to.
    namespaces -- Mapping (prefix->namespace) with additional namespaces,
                  if necessary.

    """
    for (nsname, ns) in namespaces.iteritems():
        attrname = "xmlns:%s" % nsname
        elem.attrib[attrname] = ns


class DigestCreator(object):
    def __init__(self, client, method, uri, body):
        self._response = client._response
        self._headers = client.headers
        self.user = client._user
        self.password = client._password
        self.method = method
        self.uri = uri
        self.entity_body = body
        self.content_length = len(body)
        self.A1 = "%s:%s:%s" % (self.user, self.realm, self.password)
        self.A2 = "%s:%s" % (self.method, self.uri)

    def __getattr__(self, name):
        return getattr(self._response, name)

    def __getitem__(self, name):
        name = name.lower()
        for key in self._headers:
            if key.lower() == name:
                return self._headers[key]
        return ""

    def H(self, value):
        return self.algorithm(value).hexdigest()

    def KD(self, value1, value2):
        return self.H("%s:%s" % (value1, value2))

    @property
    def response_digest(self):
        return self.KD(self.H(self.A1), "%s:%s" % (self.nonce, self.H(self.A2)))

    @property
    def entity_info(self):
        content_type = self["Content-Type"]
        content_length = self.content_length
        content_encoding = self["Content-Encoding"]
        last_modified = self["Last-modified"]
        expires = self["Expires"]
        info = "%s:%s:%s:%s:%s:%s" % (self.uri, content_type, content_length,
                                      content_encoding, last_modified, expires)
        return self.H(self.uri)

    @property
    def entity_digest(self):
        date = self["Date"]
        info = self.entity_info
        body = self.H(self.entity_body)
        digest = "%s:%s:%s:%s:%s" % (self.nonce, self.method, date, info, body)
        return self.KD(self.H(self.A1), digest)


def create_propfind(names=False, properties=None,
                    include=None, namespaces=None):
    """Construct and return XML string for PROPFIND.

    names -- Boolean whether the profind is requesting property names only.
    properties -- An iterable containing property names to request. Will only
                  by considered when names is False.
    include -- An Iterable containing properties that shall be returned by the
               WebDAV server in addition to the properties returned by an
               allprop request.
    namespaces -- Mapping (prefix->namespace) with additional namespaces,
                  if necessary.

    If names is False, properties is considered False, an allprop-PROPFIND
    request is created.

    """
    namespaces = dict() if (namespaces is None) else namespaces
    # RFC 2518, 12.14 propfind XML Element
    # <!ELEMENT propfind (allprop | propname | prop) >
    propfind = Element("propfind", _NS)
    _addnamespaces(propfind, namespaces)
    if names:
        # RFC 2518, 12.14.2 propname XML Element
        # <!ELEMENT propname EMPTY >
        names_element = SubElement(propfind, "propname")
    elif properties:
        # RFC 2518, 12.11 prop XML Element
        # <!ELEMENT prop ANY >
        prop = SubElement(propfind, "prop")
        for propname in properties:
            propelement = SubElement(prop, propname)
    else:
        # RFC 2518, 12.14.2 allprop XML Element
        # <!ELEMENT allprop EMPTY >
        allprop = SubElement(propfind, "allprop")
        # draft-reschke-webdav-allprop-include-00
        # <!ELEMENT propfind ((allprop, include+) | propname | prop) >
        # <!ELEMENT include ANY >
        if include:
            include_element = SubElement(propfind, "include")
            for propname in include:
                inclprop = SubElement(include_element, propname)
    return tostring(propfind, "UTF-8")


def create_proppatch(setprops, delprops, namespaces=None):
    """Construct and return XML string for PROPPATCH.

    setprops -- Mapping with properties to set.
    delprops -- Iterable with element names to remove.
    namespaces -- Mapping (prefix->namespace) with additional namespaces,
                  if necessary.

    """
    # RFC 2518, 12.13 propertyupdate XML element
    # <!ELEMENT propertyupdate (remove | set)+ >
    propertyupdate = Element("propertyupdate", _NS)
    if namespaces:
        _addnamespaces(propertyupdate, namespaces)
    # RFC 2518, 12.13.2 set XML element
    # <!ELEMENT set (prop) >
    if setprops:
        set_ = SubElement(propertyupdate, "set")
        prop = SubElement(set_, "prop")
        for (propname, propvalue) in setprops.iteritems():
            prop = SubElement(prop, propname)
            prop.text = propvalue
    # RFC 2518, 12.13.1 set XML element
    # <!ELEMENT remove (prop) >
    if delprops:
        remove = SubElement(propertyupdate, "remove")
        prop = SubElement(remove, "prop")
        for propname in delprops:
            prop = SubElement(prop, propname)
    return tostring(propertyupdate, "UTF-8")


def create_lock(scope="exclusive", type_="write", owner=None):
    """Construct and return XML string for LOCK.

    scope -- One of "exclusive" or "shared".
    type_ -- Only "write" in defined in RFC.
    owner -- Optional owner information for lock. Can be any string.

    Raise ValueError, if illegal scope was given.

    """
    # RFC 2518, 12.7 lockscope XML Element
    # <!ELEMENT lockscope (exclusive | shared) >
    # RFC 2518, 12.7.1 exclusive XML Element
    # <!ELEMENT exclusive EMPTY >
    # RFC 2518, 12.7.2 shared XML Element
    # <!ELEMENT shared EMPTY >
    if scope not in ("exclusive", "shared"):
        raise ValueError("scope must be either exclusive or shared")
    # RFC 2518, 12.6 lockinfo XML Element
    # <!ELEMENT lockinfo (lockscope, locktype, owner?) >
    lockinfo = Element("lockinfo", _NS)
    # set lockscope
    lockscope = SubElement(lockinfo, "lockscope")
    scope = SubElement(lockscope, scope)
    # RFC 2518, 12.8 locktype XML Element
    # <!ELEMENT locktype (write) >
    # RFC 2518, 12.8.1 write XML Element
    # <!ELEMENT write EMPTY >
    locktype = SubElement(lockinfo, "locktype")
    typ_ = SubElement(locktype, type_)
    if owner is not None:
        # RFC 2518, 12.10 owner XML Element
        # <!ELEMENT owner ANY>
        owner_elem = SubElement(lockinfo, "owner")
        if isinstance(owner, basestring):
            owner_elem.text = owner
        else:
            owner_elem.append(owner)
    return tostring(lockinfo)


def create_report(properties=None, elements=None, namespaces=None):
    """Construct and return XML for REPORT."""
    namespaces = dict() if (namespaces is None) else namespaces
    ns = {"xmlns": "DAV:"}
    # RFC 3253, 3.7 DAV:version-tree Report
    # <!ELEMENT version-tree ANY>
    # ANY value: a sequence of zero or more elements, with at most one
    # DAV:prop element.
    report = Element("version-tree", ns)
    _addnamespaces(report, namespaces)
    if properties:
        prop = SubElement(report, "prop")
        for propname in properties:
            propelement = SubElement(prop, propname)
    if elements:
        for element in elements:
            report.append(element)
    return tostring(report, "UTF-8")

