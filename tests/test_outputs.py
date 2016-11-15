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

import imp
import multiprocessing
import multiprocessing.dummy
import pytest
import zmq


def test_select():
    from ReactOBus.outputs import Output, ZMQPush, ZMQPub

    i = Output.select("ZMQPush", "pull", {"url": ""}, "")
    assert isinstance(i, ZMQPush)

    i = Output.select("ZMQPub", "sub", {"url": ""}, "")
    assert isinstance(i, ZMQPub)

    with pytest.raises(NotImplementedError):
        Output.select("ZMQ", "zmq", {}, "")


def test_zmq_class():
    from ReactOBus.outputs import ZMQ

    with pytest.raises(NotImplementedError):
        ZMQ("", {"url": ""}, "").secure_setup()


def test_zmq_push(monkeypatch, tmpdir):
    # Replace multiprocessing by threading
    monkeypatch.setattr(multiprocessing, "Process",
                        multiprocessing.dummy.Process)

    # Reload the base class "Pipe"
    import ReactOBus.utils
    imp.reload(ReactOBus.utils)
    import ReactOBus.outputs
    imp.reload(ReactOBus.outputs)
    from ReactOBus.outputs import ZMQPush

    # Replace zmq.Context.instance()
    imp.reload(zmq)

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

        def setsockopt(self, key, value):
            self.socket.setsockopt(key, value)

        def connect(self, addr):
            self.socket.connect(addr)

    class MockZMQInstance(object):
        def __init__(self):
            self.instance = zmq.Context.instance()

        def __call__(self):
            return self

        def socket(self, socket_type):
            socket = self.instance.socket(socket_type)
            if socket_type == zmq.SUB:
                return MockZMQSocket(socket, 2)
            else:
                return socket

    mock_zmq_instance = MockZMQInstance()
    monkeypatch.setattr(zmq.Context, "instance", mock_zmq_instance)

    url = "ipc://%s" % tmpdir.join("ReactOBus.test.push")
    outbound = "ipc://%s" % tmpdir.join("ReactOBus.test.outbound")

    # Listen to events
    ctx = zmq.Context.instance()
    pull = ctx.socket(zmq.PULL)
    pull.bind(url)

    # Publish events
    pub = ctx.socket(zmq.PUB)
    pub.bind(outbound)

    p = ZMQPush("push", {"url": url}, outbound)
    p.start()
    # Sleep to give sub socket some time to connect
    import time
    time.sleep(1)

    # Send a valid message
    orig_msg = [b"org.reactobus.test", b"uuid", b"2016-11-15",
                b"testing", b"{}"]
    pub.send_multipart(orig_msg)

    msg = pull.recv_multipart()
    assert msg == orig_msg

    p.join()
