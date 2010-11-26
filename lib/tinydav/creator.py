# Request creator function for tinydav WebDAV client.
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
    propfind = Element("propfind", _NS)
    _addnamespaces(propfind, namespaces)
    # available property names
    if names:
        names_element = SubElement(propfind, "propname")
    # explicitly requested properties
    elif properties:
        prop = SubElement(propfind, "prop")
        for propname in properties:
            propelement = SubElement(prop, propname)
    # all available properties
    else:
        allprop = SubElement(propfind, "allprop")
        # additional properties that won't be sent until requested
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
    propertyupdate = Element("propertyupdate", _NS)
    if namespaces:
        _addnamespaces(propertyupdate, namespaces)
    # set properties
    if setprops:
        set_ = SubElement(propertyupdate, "set")
        prop = SubElement(set_, "prop")
        for (propname, propvalue) in setprops.iteritems():
            property = SubElement(prop, propname)
            property.text = propvalue
    # remove properties
    if delprops:
        remove = SubElement(propertyupdate, "remove")
        prop = SubElement(remove, "prop")
        for propname in delprops:
            property = SubElement(prop, propname)
    return tostring(propertyupdate, "UTF-8")


def create_lock(scope="exclusive", type_="write", owner=None):
    """Construct and return XML string for LOCK.

    scope -- One of "exclusive" or "shared".
    type_ -- Only "write" in defined in RFC.
    owner -- Optional owner information for lock. Can be any string.

    Raise ValueError, if illegal scope was given.

    """
    if scope not in ("exclusive", "shared"):
        raise ValueError("scope must be either exclusive or shared")
    lockinfo = Element("lockinfo", _NS)
    # set lockscope
    lockscope = SubElement(lockinfo, "lockscope")
    scope = SubElement(lockscope, scope)
    # locktype
    locktype = SubElement(lockinfo, "locktype")
    typ_ = SubElement(locktype, type_)
    # add owner, if needed
    if owner is not None:
        owner_elem = SubElement(lockinfo, "owner")
        if isinstance(owner, str):
            owner_elem.text = owner
        else:
            owner_elem.append(owner)
    return tostring(lockinfo)


def create_report(properties=None, elements=None, namespaces=None):
    """Construct and return XML for REPORT."""
    namespaces = dict() if (namespaces is None) else namespaces
    ns = {"xmlns": "DAV:"}
    report = Element("version-tree", ns)
    _addnamespaces(report, namespaces)
    # set at most one prop.
    if properties:
        prop = SubElement(report, "prop")
        for propname in properties:
            propelement = SubElement(prop, propname)
    # additional xml.
    if elements:
        for element in elements:
            report.append(element)
    return tostring(report, "UTF-8")
