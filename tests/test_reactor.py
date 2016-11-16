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


class ZMQMockSocket(object):
    def __init__(self):
        self.connected = False
        self.opts = {}
        self.url = None
        self.msgs = []
        self.send_msgs = []

    def setsockopt(self, key, value):
        self.opts[key] = value

    def connect(self, url):
        self.connected = True
        self.url = url

    def bind(self, url):
        self.connected = True
        self.url = url

    def recv_multipart(self):
        return self.msgs.pop(0)

    def send_multipart(self, msg):
        self.send_msgs.append(msg)


class ZMQMock(object):
    def __init__(self):
        self.socks = {}

    def __call__(self):
        return self

    def socket(self, sock_type):
        if sock_type not in self.socks:
            self.socks[sock_type] = ZMQMockSocket()
        return self.socks[sock_type]


class MockWorker(object):
    def __init__(self, matchers):
        self.matchers = matchers
        self.started = False

    def start(self):
        self.started = True


def test_reactor(monkeypatch):
    # Replace zmq.Context.instance()
    zmq_mock = ZMQMock()
    monkeypatch.setattr(zmq.Context, "instance", zmq_mock)
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
    assert zmq_mock.socks[zmq.SUB].connected is True
    assert zmq_mock.socks[zmq.SUB].url == "inproc://test"
    assert zmq_mock.socks[zmq.SUB].opts == {zmq.SUBSCRIBE: b''}
    assert zmq_mock.socks[zmq.DEALER].connected is True
    assert zmq_mock.socks[zmq.DEALER].opts == {}
    assert zmq_mock.socks[zmq.DEALER].url == "inproc://workers"
    assert len(zmq_mock.socks[zmq.DEALER].send_msgs) == 0

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
    zmq_mock.socks[zmq.SUB].msgs = [
        ["org.reactobus.lava", "uuid", "2016", "lavauser", "{}"],
        ["org.reactobus.lava", ""]
    ]
    with pytest.raises(IndexError):
        r.run()

    assert len(r.matchers) == 1
    assert r.matchers[0].name == "first test"
    assert len(r.workers) == 2
    assert r.workers[0].started
    assert r.workers[1].started
    assert zmq_mock.socks[zmq.SUB].connected is True
    assert zmq_mock.socks[zmq.SUB].url == "inproc://test"
    assert zmq_mock.socks[zmq.SUB].opts == {zmq.SUBSCRIBE: b''}
    assert zmq_mock.socks[zmq.DEALER].connected is True
    assert zmq_mock.socks[zmq.DEALER].opts == {}
    assert zmq_mock.socks[zmq.DEALER].url == "inproc://workers"
    assert len(zmq_mock.socks[zmq.DEALER].send_msgs) == 1
    assert zmq_mock.socks[zmq.DEALER].send_msgs[0] == [b"0", b"org.reactobus.lava",
                                                       b"uuid", b"2016",
                                                       b"lavauser", b"{}"]
