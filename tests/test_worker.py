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

from ReactOBus.reactor import Worker
from . import mock


class Matcher(object):
    def __init__(self):
        self.runned = False
        self.topic = None

    def run(self, topic, uuid, dt, username, data):
        self.runned = True
        self.topic = topic


def test_worker(monkeypatch):
    # Replace zmq.Context.instance()
    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)

    # Create the matchers
    matchers = [Matcher(), Matcher(), Matcher()]
    w = Worker(matchers)
    # Run for nothing to create the sockets
    with pytest.raises(IndexError):
        w.run()

    dealer = zmq_instance.socks[zmq.DEALER]
    assert dealer.connected and not dealer.bound

    # Create some work
    data = [[b"0", b"org.reactobus.test", b"", b"", b"", b""],
            [b"2", b"org.reactobus.test", b"", b"", b"", b""]]
    dealer.recv = data

    with pytest.raises(IndexError):
        w.run()

    assert matchers[0].runned
    assert not matchers[1].runned
    assert matchers[2].runned
    assert dealer.recv == []

    # Send invalid messages
    matchers = [Matcher(), Matcher(), Matcher()]
    w = Worker(matchers)

    data = [[b"a", b"org.reactobus.test", b"", b"", b"", b""],
            [b"2", b"org.reactobus.test", b"", b"", b""]]
    dealer.recv = data
    with pytest.raises(IndexError):
        w.run()
    assert not matchers[0].runned
    assert not matchers[1].runned
    assert not matchers[2].runned
    assert dealer.recv == []
