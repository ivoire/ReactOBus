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
    from reactobus.inputs import Input, ZMQPull, ZMQSub

    i = Input.select("ZMQPull", "pull", {"url": ""}, "")
    assert isinstance(i, ZMQPull)

    i = Input.select("ZMQSub", "sub", {"url": ""}, "")
    assert isinstance(i, ZMQSub)

    with pytest.raises(NotImplementedError):
        Input.select("ZMQ", "zmq", {}, "")


def test_zmq_class():
    from reactobus.inputs import ZMQ

    with pytest.raises(NotImplementedError):
        ZMQ("", {"url": ""}, "").secure_setup()


def test_zmq_pull(monkeypatch, tmpdir):
    # Reload the base class "Pipe"
    import reactobus.utils

    imp.reload(reactobus.utils)
    import reactobus.inputs

    imp.reload(reactobus.inputs)
    from reactobus.inputs import ZMQPull

    # Replace zmq.Context.instance()
    imp.reload(zmq)

    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)

    url = "ipc://%s" % tmpdir.join("ReactOBus.test.push")
    inbound = "ipc://%s" % tmpdir.join("ReactOBus.test.inbound")

    # Create the sockets and the data
    pull = zmq_instance.socket(zmq.PULL)
    push = zmq_instance.socket(zmq.PUSH)

    # send an invalid message then a valid one
    data = [
        [b"test"],
        [b"org.reactobus.test", b"uuid", b"2016-11-15", b"testing", b"{}"],
    ]
    pull.recv.extend(data)

    p = ZMQPull("pull", {"url": url}, inbound)
    with pytest.raises(IndexError):
        p.run()

    assert pull.bound and not pull.connected
    assert pull.url == url
    assert pull.recv == []

    assert push.url == inbound
    assert push.connected and not push.bound
    assert push.send == [
        [b"org.reactobus.test", b"uuid", b"2016-11-15", b"testing", b"{}"]
    ]


def test_zmq_pull_filtering(monkeypatch, tmpdir):
    # Reload the base class "Pipe"
    import reactobus.utils

    imp.reload(reactobus.utils)
    import reactobus.inputs

    imp.reload(reactobus.inputs)
    from reactobus.inputs import ZMQPull

    # Replace zmq.Context.instance()
    imp.reload(zmq)

    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)

    url = "ipc://%s" % tmpdir.join("ReactOBus.test.push")
    inbound = "ipc://%s" % tmpdir.join("ReactOBus.test.inbound")

    # Create the sockets and the data
    pull = zmq_instance.socket(zmq.PULL)
    push = zmq_instance.socket(zmq.PUSH)

    # send valid message that will be filtered out
    data = [
        [b"org.reactobus.test", b"uuid", b"2016-11-15", b"rob", b"{}"],
        [b"org.reactobus.test", b"uuid", b"2016-11-15", b"testing", b"{}"],
    ]
    pull.recv.extend(data)

    p = ZMQPull(
        "pull",
        {"url": url, "filters": [{"field": "username", "pattern": "rob"}]},
        inbound,
    )
    with pytest.raises(IndexError):
        p.run()

    assert pull.bound and not pull.connected
    assert pull.url == url
    assert pull.recv == []

    assert push.url == inbound
    assert push.connected and not push.bound
    assert push.send == [[b"org.reactobus.test", b"uuid", b"2016-11-15", b"rob", b"{}"]]

    # send valid message that will be filtered out
    data = [
        [b"org.reactobus.test", b"uuid", b"2016-11-15", b"rob", b'{"hello": "world"}'],
        [b"org.reactobus.test", b"uuid", b"2016-11-15", b"testing", b"{}"],
    ]
    push.send = []
    pull.recv.extend(data)

    p = ZMQPull(
        "pull",
        {"url": url, "filters": [{"field": "data.hello", "pattern": "world"}]},
        inbound,
    )
    with pytest.raises(IndexError):
        p.run()

    assert pull.bound and not pull.connected
    assert pull.url == url
    assert pull.recv == []

    assert push.url == inbound
    assert push.connected and not push.bound
    assert push.send == [
        [b"org.reactobus.test", b"uuid", b"2016-11-15", b"rob", b'{"hello": "world"}']
    ]


def test_zmq_sub(monkeypatch, tmpdir):
    # Reload the base class "Pipe"
    import reactobus.utils

    imp.reload(reactobus.utils)
    import reactobus.inputs

    imp.reload(reactobus.inputs)
    from reactobus.inputs import ZMQSub

    # Replace zmq.Context.instance()
    imp.reload(zmq)

    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)

    url = "ipc://%s" % tmpdir.join("ReactOBus.test.push")
    inbound = "ipc://%s" % tmpdir.join("ReactOBus.test.inbound")

    # Create the sockets and the data
    sub = zmq_instance.socket(zmq.SUB)
    push = zmq_instance.socket(zmq.PUSH)

    # send an invalid message then a valid one
    data = [
        [b"test"],
        [b"org.reactobus.test", b"uuid", b"2016-11-15", b"testing", b"{}"],
    ]
    sub.recv.extend(data)

    p = ZMQSub("pull", {"url": url}, inbound)
    with pytest.raises(IndexError):
        p.run()

    assert sub.connected and not sub.bound
    assert sub.url == url
    assert sub.opts == {zmq.SUBSCRIBE: b""}
    assert sub.recv == []

    assert push.url == inbound
    assert push.connected and not push.bound
    assert push.send == [
        [b"org.reactobus.test", b"uuid", b"2016-11-15", b"testing", b"{}"]
    ]
