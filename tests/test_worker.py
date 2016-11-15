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

from ReactOBus.reactor import Worker

import zmq


class MockZMQSocket(object):
    def __init__(self, socket, count):
        self.socket = socket
        self.count = count

    def recv_multipart(self):
        self.count -= 1
        if self.count:
            return self.socket.recv_multipart()
        else:
            raise IndexError

    def connect(self, addr):
        self.socket.connect(addr)


class MockZMQInstance(object):
    def __init__(self):
        self.instance = zmq.Context.instance()

    def __call__(self):
        return self

    def socket(self, socket_type):
        socket = self.instance.socket(socket_type)
        if socket_type == zmq.DEALER:
            return MockZMQSocket(socket, 3)
        else:
            return socket


class Matcher(object):
    def __init__(self):
        self.runned = False
        self.topic = None

    def run(self, topic, uuid, dt, username, data):
        self.runned = True
        self.topic = topic


def test_worker(monkeypatch):
    # Replace zmq.Context.instance()
    mock_zmq_instance = MockZMQInstance()
    monkeypatch.setattr(zmq.Context, "instance", mock_zmq_instance)

    # Create the socket to send events
    ctx = zmq.Context.instance()
    push = ctx.socket(zmq.PUSH)
    push.bind("inproc://workers")

    # Create the matchers
    matchers = [Matcher(), Matcher(), Matcher()]

    w = Worker(matchers)
    w.start()

    # Push jobs
    push.send_multipart([b"0", b"org.reactobus.test", b"", b"", b"", b""])
    push.send_multipart([b"2", b"org.reactobus.test", b"", b"", b"", b""])
    w.join()
    assert matchers[0].runned
    assert not matchers[1].runned
    assert matchers[2].runned

    # Send invalid messages
    matchers = [Matcher(), Matcher(), Matcher()]
    w = Worker(matchers)
    w.start()
    push.send_multipart([b"a", b"org.reactobus.test", b"", b"", b"", b""])
    push.send_multipart([b"2", b"org.reactobus.test", b"", b"", b""])
    w.join()
    assert not matchers[0].runned
    assert not matchers[1].runned
    assert not matchers[2].runned
