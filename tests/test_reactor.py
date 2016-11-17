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


class MockWorker(object):
    def __init__(self, matchers):
        self.matchers = matchers
        self.started = False

    def start(self):
        self.started = True


def test_reactor(monkeypatch):
    # Replace zmq.Context.instance()
    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)
    import ReactOBus.reactor
    monkeypatch.setattr(ReactOBus.reactor, "Worker", MockWorker)

    from ReactOBus.reactor import Reactor

    options = {
        "rules": {},
        "workers": 0
    }
    r = Reactor(options, "inproc://test")
    with pytest.raises(IndexError):
        r.run()
    sub = zmq_instance.socks[zmq.SUB]
    dealer = zmq_instance.socks[zmq.DEALER]

    assert sub.connected and not sub.bound
    assert sub.url == "inproc://test"
    assert sub.opts == {zmq.SUBSCRIBE: b''}

    assert dealer.bound and not dealer.connected
    assert dealer.url == "inproc://workers"
    assert dealer.recv == []

    options = {
        "rules": [{"name": "first test",
                   "match": {"field": "topic",
                             "pattern": "^org.reactobus.lava"},
                   "exec": {"path": "/bin/true",
                            "args": ["topic", "$topic", "username",
                                     "$username"],
                            "timeout": 1}}],
        "workers": 2
    }
    r = Reactor(options, "inproc://test")
    sub.recv = [
        ["org.reactobus.lava", "uuid", "2016", "lavauser", "{}"],
        ["org.reactobus.lav", "uuid", "2016", "lavauser", "{}"],
        ["org.reactobus.lava", ""]
    ]
    with pytest.raises(IndexError):
        r.run()

    assert len(r.matchers) == 1
    assert r.matchers[0].name == "first test"
    assert len(r.workers) == 2
    assert r.workers[0].started
    assert r.workers[1].started
    assert sub.recv == []
    assert dealer.send == [[b"0", b"org.reactobus.lava", b"uuid",
                            b"2016", b"lavauser", b"{}"]]
