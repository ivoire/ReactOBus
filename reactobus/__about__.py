#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2016-2019 Rémi Duraffort
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

__all__ = [
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__url__",
    "__version__",
]


def git_describe():
    import subprocess

    try:
        # git describe?
        out = subprocess.check_output(["git", "describe"], stderr=subprocess.STDOUT)
        return out.decode("utf-8").rstrip("\n")[1:]
    except Exception:
        return "git"


__author__ = "Rémi Duraffort"
__author_email__ = "remi.duraffort@linaro.org"
__description__ = "A message broker to create software bus over the network"
__license__ = "AGPLv3+"
__url__ = "https://git.lavasoftware.org/lava/ReactOBus"
__version__ = git_describe()
