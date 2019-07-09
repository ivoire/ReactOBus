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
import subprocess
import zmq

from ReactOBus.reactor import Matcher, Worker
from . import mock


class DummyMatcher(object):
    def __init__(self):
        self.runned = False

    def run(self, topic, uuid, dt, username, data):
        assert not isinstance(data, str)
        self.runned = True
        self.topic = topic
        self.uuid = uuid
        self.dt = dt
        self.username = username
        self.data = data


def test_worker(monkeypatch):
    # Replace zmq.Context.instance()
    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)

    # Create the matchers
    matchers = [DummyMatcher(), DummyMatcher(), DummyMatcher()]
    w = Worker(matchers)
    # Run for nothing to create the sockets
    with pytest.raises(IndexError):
        w.run()

    dealer = zmq_instance.socks[zmq.DEALER]
    assert dealer.connected and not dealer.bound

    # Create some work
    data = [[b"0", b"org.reactobus.test", b"azertyuiop", b"2024",
             b"user", b"{}"],
            [b"2", b"org.reactobus.ci", b"qwertyuiop", b"1789", b"bla",
             b"{\"hello\": \"world\"}"]]
    dealer.recv = data

    with pytest.raises(IndexError):
        w.run()

    assert matchers[0].runned
    assert matchers[0].topic == "org.reactobus.test"
    assert matchers[0].uuid == "azertyuiop"
    assert matchers[0].dt == "2024"
    assert matchers[0].username == "user"
    assert matchers[0].data == {}
    assert not matchers[1].runned
    assert matchers[2].runned
    assert matchers[2].topic == "org.reactobus.ci"
    assert matchers[2].uuid == "qwertyuiop"
    assert matchers[2].dt == "1789"
    assert matchers[2].username == "bla"
    assert matchers[2].data == {"hello": "world"}
    assert dealer.recv == []

    # Send invalid messages
    matchers = [DummyMatcher(), DummyMatcher(), DummyMatcher()]
    w = Worker(matchers)

    data = [[b"a", b"org.reactobus.test", b"", b"", b"", b"{}"],
            [b"2", b"org.reactobus.test", b"", b"", b""],
            [b"42", b"org.reactobus.test", b"", b"", b"", b"{}"]]
    dealer.recv = data
    with pytest.raises(IndexError):
        w.run()
    assert not matchers[0].runned
    assert not matchers[1].runned
    assert not matchers[2].runned
    assert dealer.recv == []


def test_worker_and_matchers(monkeypatch):
    # Replace zmq.Context.instance()
    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)

    m_args = []
    m_input = ""
    m_timeout = 0

    def mock_check_output(args, stderr, input, timeout):
        nonlocal m_args
        nonlocal m_input
        nonlocal m_timeout
        m_args = args
        m_input = input
        m_timeout = timeout
        for arg in args:
            assert isinstance(arg, bytes)
        assert isinstance(input, bytes)
        return ""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    rule_1 = {"name": "first test",
              "match": {"field": "topic",
                        "patterns": "^org.reactobus.lava"},
              "exec": {"path": "/bin/true",
                       "args": ["topic", "$topic", "username", "$username"],
                       "timeout": 1}}
    rule_2 = {"name": "second test",
              "match": {"field": "username",
                        "patterns": ".*kernel.*"},
              "exec": {"path": "/bin/true",
                       "args": ["topic", "$topic", "username", "$username"],
                       "timeout": 1}}
    rule_3 = {"name": "data matching",
              "match": {"field": "data.submitter",
                        "patterns": "kernel-ci"},
              "exec": {"path": "/bin/true",
                       "args": ["topic", "$topic", "submitter",
                                "$data.submitter"],
                       "timeout": 1}}

    # Create the matchers
    matchers = [Matcher(rule_1), Matcher(rule_2), Matcher(rule_3)]
    w = Worker(matchers)

    # Run for nothing to create the sockets
    with pytest.raises(IndexError):
        w.run()

    dealer = zmq_instance.socks[zmq.DEALER]
    assert dealer.connected and not dealer.bound

    # Create some work for rule_1
    data = [[b"0", b"org.reactobus.lava", b"", b"", b"lavauser", b"{}"]]
    dealer.recv = data

    with pytest.raises(IndexError):
        w.run()

    assert m_args == [b"/bin/true", b"topic", b"org.reactobus.lava",
                      b"username", b"lavauser"]

    # Create some work for rule_2
    data = [[b"1", b"org.kernel.git", b"", b"", b"kernelci", b"{}"]]
    dealer.recv = data

    with pytest.raises(IndexError):
        w.run()

    assert m_args == [b"/bin/true", b"topic", b"org.kernel.git",
                      b"username", b"kernelci"]

    # Create some work for rule_3
    data = [[b"2", b"org.linaro.validation", b"", b"", b"lavauser",
             b"{\"submitter\": \"kernel-ci\"}"]]
    dealer.recv = data

    with pytest.raises(IndexError):
        w.run()

    assert m_args == [b"/bin/true", b"topic", b"org.linaro.validation",
                      b"submitter", b"kernel-ci"]

    m_args = []
    # Create some invalid work for rule_3
    data = [[b"2", b"org.linaro.validation", b"", b"", b"lavauser",
             b"{\"submitter: \"kernel-ci\"}"]]
    dealer.recv = data

    with pytest.raises(IndexError):
        w.run()

    assert m_args == []
