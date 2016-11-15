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

from ReactOBus.utils import Pipe

import pytest


class PipeTest(Pipe):
    classname = "PipeTest"

    def __init__(self, name, options, inbound):
        pass


class PipeSubTest(PipeTest):
    classname = "PipeSubTest"


def test_pipe():
    p = Pipe.select("PipeTest", "testing", {}, '')
    assert isinstance(p, PipeTest)

    p = Pipe.select("PipeSubTest", "testing", {}, '')
    assert isinstance(p, PipeSubTest)

    with pytest.raises(NotImplementedError):
        Pipe.select("TestClass", "test", {}, '')

    p = Pipe()
    with pytest.raises(NotImplementedError):
        p.setup()
    with pytest.raises(NotImplementedError):
        p.run()
