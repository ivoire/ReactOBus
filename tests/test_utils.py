# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2016-2017 Rémi Duraffort
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

from reactobus.utils import lookup, Pipe
from reactobus.reactor import Matcher


class PipeTest(Pipe):
    classname = "PipeTest"

    def __init__(self, name, options, inbound):
        pass


class PipeSubTest(PipeTest):
    classname = "PipeSubTest"


def test_pipe():
    p = Pipe.select("PipeTest", "testing", {}, "")
    assert isinstance(p, PipeTest)

    p = Pipe.select("PipeSubTest", "testing", {}, "")
    assert isinstance(p, PipeSubTest)

    with pytest.raises(NotImplementedError):
        Pipe.select("TestClass", "test", {}, "")

    p = Pipe()
    with pytest.raises(NotImplementedError):
        p.setup()
    with pytest.raises(NotImplementedError):
        p.run()


def test_lookup():
    assert lookup("username", {"username": "kernel"}, {}) == "kernel"
    assert lookup("msg", {"username": "kernel", "msg": "hello"}, {}) == "hello"

    # $data
    assert lookup("data", {"msg": "something"}, {}) == "{}"
    assert lookup("data", {"msg": "something"}, "just a string") == "just a string"
    assert (
        lookup("data", {"msg": "something"}, {"hello": "world"}) == '{"hello": "world"}'
    )
    assert (
        lookup("data", {"msg": "something"}, ["hello", "world"]) == '["hello", "world"]'
    )

    # $data.key
    assert lookup("data.key", {"msg": "something"}, {"key": "value"}) == "value"
    assert lookup("data.hello", {"msg": "something"}, {"hello": "world"}) == "world"
    assert lookup("data.hello", {"msg": "something"}, {"hello": []}) == "[]"
    assert (
        lookup(
            "data.hello", {"msg": "something"}, {"hello": [{"world": 1}, {"wordl": 2}]}
        )
        == '[{"world": 1}, {"wordl": 2}]'
    )

    with pytest.raises(KeyError):
        lookup("msg", {}, {})
    with pytest.raises(KeyError):
        lookup("msg", {}, {"msg": "value"})
    with pytest.raises(KeyError):
        lookup("msg", {"username": "kernel"}, {})
    with pytest.raises(KeyError):
        lookup("data.username", {"username": "kernel"}, {})
