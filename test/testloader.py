# Testloader for setuptools unittest.
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
"""Testloader for setuptools unittest."""

from os import path
import glob
import os
import re
import sys
import unittest

try:
    import coverage
except ImportError:
    coverage = None

# FIXME: when the coverage module is present, the code breaks.
coverage = None

# Define packages/modules that shall not be checked for coverage.
EXCEPTIONS = frozenset()

MODULE_DIR = path.dirname(__file__)
# make sure this directory is in python path for import
sys.path.insert(1, MODULE_DIR)


def find_modules():
    """Collect all defined modules and packages to be covered."""
    modpack = set()
    lib = path.abspath(path.join(MODULE_DIR, "..", "lib"))
    for (dirpath, dirnames, filenames) in os.walk(lib):
        if (dirpath == lib) or ("__init__.py" in filenames):
            try:
                filenames.remove("__init__.py")
                package = dirpath[len(lib)+1:]
                if package:
                    modpack.add(package)
            except ValueError:
                pass
            for name in filenames:
                if name.endswith(".py"):
                    name = name[:-3]
                    filepath = path.join(dirpath, name)[len(lib)+1:]
                    modpack.add(filepath.replace(path.sep, "."))
    return modpack


def wrap_run_coverage(func):
    """Wrapper for the suit run-method.

    Wrap the run method of (unittest) suite objects to print coverage
    stats.

    """
    def wrapper(*args, **kwargs):
        # Due to an unknown reason, the os module is None within the coverage
        # module and thus, the registered atexit-function fails. As there seems
        # to be no important reason for calling this function, we remove it.
        # FIXME find out what's going on
        import atexit
        atexit._exithandlers.remove(
            (coverage.the_coverage.save, tuple(), dict())
        )
        # Wrap the canonical_filename-method and employ an os. Else, there'll
        # be many coverage numbers missing.
        def save(func):
            def wrapper(*args, **kwargs):
                func.func_globals['os'] = os
                return func(*args, **kwargs)
            return wrapper
        coverage.the_coverage.canonical_filename = \
                save(coverage.the_coverage.canonical_filename)

        try:
            return func(*args, **kwargs)
        finally:
            look_at = find_modules() - EXCEPTIONS
            mods = dict((name, module)
                        for name, module in sys.modules.items()
                        if name in look_at)
            print
            print "Test coverage report:"
            coverage.report(mods.values(), show_missing=True)
            missing = look_at - set(mods)
            if missing:
                print
                print "Never imported modules/packages and thus not covered:"
                for mod in missing:
                    print " *", mod
    return wrapper


def create_suite():
    """Return test suite."""
    all_pys = path.join(MODULE_DIR, "*.py")
    modules = list()
    for module in glob.glob(all_pys):
        modulename = path.split(module)[1]
        if modulename not in ("__init__.py", "testloader.py"):
            modules.append(modulename[:-3]) # cut .py
    loader = unittest.TestLoader()
    return loader.loadTestsFromNames(modules)


def run():
    """Test everything automatically by setup.py and measure coverage."""
    if coverage:
        coverage.erase()
        coverage.start()
    suite = create_suite()
    if coverage:
        suite.run = wrap_run_coverage(suite.run)
    return suite


if __name__ == "__main__":
    # Add more dirs, if necessary. This is for the case that you want to
    # run unittests by hand without using setup.py
    sys.path.insert(1, "../lib")
    run()
