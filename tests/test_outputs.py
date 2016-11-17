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
import pytest
import zmq

from . import mock


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
    # Reload the base class "Pipe"
    import ReactOBus.utils
    imp.reload(ReactOBus.utils)
    import ReactOBus.outputs
    imp.reload(ReactOBus.outputs)
    from ReactOBus.outputs import ZMQPush

    # Replace zmq.Context.instance()
    imp.reload(zmq)

    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)

    url = "ipc://%s" % tmpdir.join("ReactOBus.test.push")
    outbound = "ipc://%s" % tmpdir.join("ReactOBus.test.outbound")

    # Create the sockets and the data
    push = zmq_instance.socket(zmq.PUSH)
    sub = zmq_instance.socket(zmq.SUB)

    # send an invalid message then a valid one
    data = [[b"test"],
            [b"org.reactobus.test", b"uuid", b"2016-11-15",
             b"testing", b"{}"]]
    sub.recv.extend(data)

    p = ZMQPush("push", {"url": url}, outbound)
    with pytest.raises(IndexError):
        p.run()

    assert sub.connected and not sub.bound
    assert sub.url == outbound
    assert sub.recv == []

    assert push.connected and not push.bound
    assert push.url == url
    assert push.send == data


def test_zmq_pub(monkeypatch, tmpdir):
    # Reload the base class "Pipe"
    import ReactOBus.utils
    imp.reload(ReactOBus.utils)
    import ReactOBus.outputs
    imp.reload(ReactOBus.outputs)
    from ReactOBus.outputs import ZMQPub

    # Replace zmq.Context.instance()
    imp.reload(zmq)

    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)

    url = "ipc://%s" % tmpdir.join("ReactOBus.test.push")
    outbound = "ipc://%s" % tmpdir.join("ReactOBus.test.outbound")

    # Create the sockets and the data
    pub = zmq_instance.socket(zmq.PUB)
    sub = zmq_instance.socket(zmq.SUB)

    # send an invalid message then a valid one
    data = [[b"test"],
            [b"org.reactobus.test", b"uuid", b"2016-11-15",
             b"testing", b"{}"]]
    sub.recv.extend(data)

    p = ZMQPub("pub", {"url": url}, outbound)
    with pytest.raises(IndexError):
        p.run()

    assert sub.connected and not sub.bound
    assert sub.url == outbound
    assert sub.recv == []

    assert pub.bound and not pub.connected
    assert pub.url == url
    assert pub.send == data
