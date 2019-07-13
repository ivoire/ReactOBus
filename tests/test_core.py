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
import zmq

from . import mock


def test_core(monkeypatch, tmpdir):
    # Replace zmq.Context.instance()
    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)

    from reactobus.core import Core

    # Create the sockets
    inbound = "ipc://%s" % tmpdir.join("ReactOBus.test.inbound")
    outbound = "ipc://%s" % tmpdir.join("ReactOBus.test.outbound")

    # Create the sockets and the data
    pull = zmq_instance.socket(zmq.PULL)
    pub = zmq_instance.socket(zmq.PUB)

    data = [
        [b"tests.1"],
        [b"tests.2", "some data"],
        [b"tests.3", "something", "else"],
        [],
        [b"tests.5"],
    ]
    pull.recv.extend(data)

    # Start the proxy
    core = Core(inbound, outbound)
    with pytest.raises(IndexError):
        core.run()

    assert len(pull.recv) == 0
    assert len(pull.send) == 0
    assert len(pub.send) == 5
    assert pub.send == data
    assert len(pub.recv) == 0
