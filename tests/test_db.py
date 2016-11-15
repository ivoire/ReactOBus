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

import datetime
import imp
import json
import pytest
import uuid
import zmq
import sqlalchemy.orm


class ZMQMockSocket(object):
    def __init__(self):
        self.connected = False
        self.opts = {}
        self.url = None
        self.msgs = []

    def setsockopt(self, key, value):
        self.opts[key] = value

    def connect(self, url):
        self.connected = True
        self.url = url

    def recv_multipart(self):
        return self.msgs.pop(0)


class ZMQMock(object):
    def __init__(self):
        self.sock = ZMQMockSocket()

    def socket(self, sock_type):
        return self.sock


def test_run(monkeypatch, tmpdir):
    zmq_mock = ZMQMock()

    def mock_zmq_context():
        nonlocal zmq_mock
        return zmq_mock

    monkeypatch.setattr(zmq.Context, "instance", mock_zmq_context)

    from ReactOBus.db import DB, Message

    dbname = tmpdir.join('testing.sqlite3')
    db_url = "sqlite:///%s" % dbname
    db = DB({'url': db_url}, "inproc://test_run")
    with pytest.raises(IndexError):
        db.run()
    assert zmq_mock.sock.connected is True
    assert zmq_mock.sock.opts == {zmq.SUBSCRIBE: b''}

    # Test that wrong message will not make the process crash
    zmq_mock.sock.msgs = [[]]
    with pytest.raises(IndexError):
        db.run()

    # Check that the db is empty
    session = db.sessions()
    assert session.query(Message).count() == 0

    # Test that wrong message will not make the process crash
    zmq_mock.sock.msgs = [
                          ["org.reactobus.1", str(uuid.uuid1()),
                           datetime.datetime.utcnow().isoformat(),
                           "lavaserver", json.dumps({})],
                          ["org.reactobus.2", str(uuid.uuid1()),
                           datetime.datetime.utcnow().isoformat(),
                           "lavaserver", json.dumps({})],
                          ["org.reactobus.3", str(uuid.uuid1()),
                           datetime.datetime.utcnow().isoformat(),
                           "lavaserver", json.dumps({})],
                          ["org.reactobus.4", str(uuid.uuid1()),
                           "2016/01/01",
                           "lavaserver", json.dumps({})],
                          ["org.reactobus.5", str(uuid.uuid1()),
                           datetime.datetime.utcnow().isoformat(),
                           "lavaserver", json.dumps({})]
                          ]
    with pytest.raises(IndexError):
        db.run()

    # Check that the db is empty
    session = db.sessions()
    assert session.query(Message).count() == 4
    assert session.query(Message).get(1).topic == "org.reactobus.1"
    assert session.query(Message).get(2).topic == "org.reactobus.2"
    assert session.query(Message).get(3).topic == "org.reactobus.3"
    assert session.query(Message).get(4).topic == "org.reactobus.5"


class SessionMock(object):
    def __init__(self):
        self.messages = 0
        self.commits = 0

    def add(self, message):
        self.messages += 1

    def commit(self):
        self.commits += 1
        from sqlalchemy.exc import SQLAlchemyError
        raise SQLAlchemyError


class SessionsMock(object):
    def __init__(self):
        self.session_mock = SessionMock()

    def __call__(self):
        return self.session_mock


def test_errors(monkeypatch, tmpdir):
    zmq_mock = ZMQMock()
    zmq_mock.sock.msgs = [
                          ["org.reactobus.1", str(uuid.uuid1()),
                           datetime.datetime.utcnow().isoformat(),
                           "lavaserver", json.dumps({})],
                          ["org.reactobus.1", str(uuid.uuid1()),
                           datetime.datetime.utcnow().isoformat(),
                           "lavaserver", json.dumps({})]]

    def mock_zmq_context():
        nonlocal zmq_mock
        return zmq_mock
    monkeypatch.setattr(zmq.Context, "instance", mock_zmq_context)

    sessions_mock = SessionsMock()

    def mock_sessionmaker(bind):
        return sessions_mock
    monkeypatch.setattr(sqlalchemy.orm, "sessionmaker", mock_sessionmaker)

    # Reload the module to apply the monkey patching
    import ReactOBus.db
    from ReactOBus.db import DB
    imp.reload(ReactOBus.db)

    # Create the DB
    dbname = tmpdir.join('testing.sqlite3')
    db_url = "sqlite:///%s" % dbname
    db = DB({'url': db_url}, "inproc://test_run")

    # Run with two messages
    with pytest.raises(IndexError):
        db.run()
    assert sessions_mock.session_mock.messages == 2
    assert sessions_mock.session_mock.commits == 6
