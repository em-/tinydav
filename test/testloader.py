# Testloader for setuptools unittest.
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
"""Testloader for setuptools unittest."""
from os import path
import sys
import unittest

import Mock

TESTDIR = path.dirname(Mock.__file__)
TINYDAV = path.join(TESTDIR, "..")
sys.path.insert(0, TINYDAV)

import TestTinyDAV
import TestCreator
import TestUtil


def run():
    suite = unittest.TestSuite()
    for testclass in (TestTinyDAV, TestCreator, TestUtil):
        suite.addTests(unittest.findTestCases(testclass))
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == "__main__":
    run()

