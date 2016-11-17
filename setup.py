#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2016 Rémi Duraffort
# This file is part of ReactOBus.
#
# ReactOBus is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ReactOBus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with ReactOBus.  If not, see <http://www.gnu.org/licenses/>

from setuptools import setup
import subprocess
import sys


# Generate the long description from README.md
try:
    long_desc = subprocess.check_output(["pandoc", "-t", "rst",
                                         "README.md"]).decode('utf-8')
except FileNotFoundError:
    sys.stderr.write("Unable to generate the long description from README.md.\n"
                     "Is 'pandoc' available?\n")
    sys.exit(1)

setup(
    name="ReactOBus",
    version="0.1",
    description="A message broker to create software bus over the network",
    long_description=long_desc,
    url="https://github.com/ivoire/ReactOBus",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Communications",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Networking",
    ],
    author="Rémi Duraffort",
    author_email="ivoire@videolan.org",
    license="AGPLv3+",
    packages=["ReactOBus"],
    scripts=["reactobus"],
    install_requires=[
        "PyYAML",
        "pyzmq",
        "setproctitle"
    ],
    extras_require={
        # SQLAlchemy is optional because the ReactOBus.db module is loaded only
        # when used
        'db':  ["SQLAlchemy"]
    }

)
