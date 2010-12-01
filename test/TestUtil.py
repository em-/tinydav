# Unittests for util module.
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
"""Unittests for util module."""

import unittest

from tinydav import util

import Mock


class UtilTestCase(unittest.TestCase):
    """Test util module."""
    def test_make_absolute(self):
        """Test util.make_absolute function."""
        mockclient = Mock.Omnivore()
        mockclient.protocol = "http"
        mockclient.host = "localhost"
        mockclient.port = 80
        expect = "http://localhost:80/foo/bar"
        self.assertEqual(util.make_absolute(mockclient, "/foo/bar"), expect)

