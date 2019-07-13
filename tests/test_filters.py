# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2017 Rémi Duraffort
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

from ReactOBus.filters import Filter


def test_filters():
    f = Filter("username", "kernel-ci")
    assert f.match(
        {"topic": "testing.data", "username": "kernel-ci"}, {"hello": "world"}
    )
    assert not f.match(
        {"topic": "testing.data", "username": "1kernel-ci"}, {"hello": "world"}
    )
    assert f.match(
        {"topic": "testing.data", "username": "kernel-ci2"}, {"hello": "world"}
    )

    assert not f.match({}, {"username": "kernel-ci"})
    assert not f.match({"hello": "world"}, {"username": "kernel-ci"})

    f = Filter("data.hello", "world")
    assert not f.match({"hello": "world"}, {"username": "kernel-ci"})
    assert f.match({}, {"hello": "world"})
    assert not f.match({}, {"hello": "wood"})
    assert not f.match({}, {})
