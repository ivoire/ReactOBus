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
    from ReactOBus.inputs import Input, ZMQPull, ZMQSub

    i = Input.select("ZMQPull", "pull", {"url": ""}, "")
    assert isinstance(i, ZMQPull)

    i = Input.select("ZMQSub", "sub", {"url": ""}, "")
    assert isinstance(i, ZMQSub)

    with pytest.raises(NotImplementedError):
        Input.select("ZMQ", "zmq", {}, "")


def test_zmq_class():
    from ReactOBus.inputs import ZMQ

    with pytest.raises(NotImplementedError):
        ZMQ("", {"url": ""}, "").secure_setup()


def test_zmq_pull(monkeypatch, tmpdir):
    # Replace multiprocessing by threading
    monkeypatch.setattr(multiprocessing, "Process",
                        multiprocessing.dummy.Process)

    # Reload the base class "Pipe"
    import ReactOBus.utils
    imp.reload(ReactOBus.utils)
    import ReactOBus.inputs
    imp.reload(ReactOBus.inputs)
    from ReactOBus.inputs import ZMQPull

    # Replace zmq.Context.instance()
    imp.reload(zmq)

    class MockZMQSocket(object):
        def __init__(self, socket, count):
            self.socket = socket
            self.count = count
            self.mocked = False

        def recv_multipart(self):
            self.count -= 1
            if not self.mocked or self.count:
                return self.socket.recv_multipart()
            else:
                raise IndexError

        def bind(self, addr):
            self.mocked = bool(addr[-4:] == "push")
            self.socket.bind(addr)

    class MockZMQInstance(object):
        def __init__(self):
            self.instance = zmq.Context.instance()

        def __call__(self):
            return self

        def socket(self, socket_type):
            socket = self.instance.socket(socket_type)
            if socket_type == zmq.PULL:
                return MockZMQSocket(socket, 3)
            else:
                return socket

    mock_zmq_instance = MockZMQInstance()
    monkeypatch.setattr(zmq.Context, "instance", mock_zmq_instance)

    url = "ipc://%s" % tmpdir.join("ReactOBus.test.push")
    inbound = "ipc://%s" % tmpdir.join("ReactOBus.test.inbound")

    p = ZMQPull("pull", {"url": url}, inbound)
    p.start()

    # Listen to events
    ctx = zmq.Context.instance()
    pull = ctx.socket(zmq.PULL)
    pull.bind(inbound)
    # Send events
    push = ctx.socket(zmq.PUSH)
    push.connect(url)

    # Send an invalid message that will be dropped
    push.send_multipart([b"test"])
    # Send a valid message
    orig_msg = [b"org.reactobus.test", b"uuid", b"2016-11-15",
                b"testing", b"{}"]
    push.send_multipart(orig_msg)

    msg = pull.recv_multipart()
    assert msg == orig_msg

    p.join()
