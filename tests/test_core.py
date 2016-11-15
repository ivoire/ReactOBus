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

import multiprocessing
import multiprocessing.dummy
import time
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

    def bind(self, addr):
        self.socket.bind(addr)


class MockZMQInstance(object):
    def __init__(self):
        self.instance = zmq.Context.instance()

    def __call__(self):
        return self

    def socket(self, socket_type):
        socket = self.instance.socket(socket_type)
        if socket_type == zmq.PULL:
            return MockZMQSocket(socket, 2)
        else:
            return socket


def test_core(monkeypatch, tmpdir):
    # Replace multiprocessing by threading
    monkeypatch.setattr(multiprocessing, "Process",
                        multiprocessing.dummy.Process)

    # Replace zmq.Context.instance()
    mock_zmq_instance = MockZMQInstance()
    monkeypatch.setattr(zmq.Context, "instance", mock_zmq_instance)

    from ReactOBus.core import Core

    # Create the sockets
    inbound = "ipc://%s" % tmpdir.join("ReactOBus.test.inbound")
    outbound = "ipc://%s" % tmpdir.join("ReactOBus.test.outbound")

    # Start the proxy
    core = Core(inbound, outbound)
    core.start()

    # Listen for events
    ctx = zmq.Context.instance()
    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.SUBSCRIBE, b"")
    sub.connect(outbound)
    time.sleep(1)

    # Send events
    push = ctx.socket(zmq.PUSH)
    push.connect(inbound)

    push.send_multipart([b"test"])

    msg = sub.recv_multipart()
    assert len(msg) == 1
    assert msg[0] == b"test"

    # Wait for the thread to throw an IndexError exception
    core.join()
