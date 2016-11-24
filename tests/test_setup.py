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

import pytest
import setuptools
import subprocess
from zmq.utils.strtypes import u


def is_pandoc_available():
    try:
        _ = subprocess.check_output(["pandoc", "--help"], timeout=3)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


@pytest.mark.skipif(not is_pandoc_available(),
                    reason="'pandoc' not installed")
def test_long_description(monkeypatch):
    def mock_setup(**args):
        pass
    monkeypatch.setattr(setuptools, "setup", mock_setup)

    from setup import long_description

    out = subprocess.check_output(["pandoc", "README.md", "-t", "rst"])
    assert u(out) == long_description
