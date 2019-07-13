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
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy.orm
import uuid
import zmq

from . import mock


def test_run(monkeypatch, tmpdir):
    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)
    monkeypatch.setattr(zmq, "Poller", mock.ZMQPoller)

    from reactobus.db import DB, Message

    dbname = tmpdir.join("testing.sqlite3")
    db_url = "sqlite:///%s" % dbname
    db = DB({"url": db_url}, "inproc://test_run")
    with pytest.raises(IndexError):
        db.run()
    sub = zmq_instance.socks[zmq.SUB]
    assert len(sub.recv) == 0
    assert sub.connected is True
    assert sub.opts == {zmq.SUBSCRIBE: b""}

    # Test that wrong message will not make the process crash
    sub.recv = [[]]
    with pytest.raises(IndexError):
        db.run()
    assert len(sub.recv) == 0

    # Check that the db is empty
    session = db.sessions()
    assert session.query(Message).count() == 0

    # Test that wrong message will not make the process crash
    sub.recv = [
        [
            "org.reactobus.1",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
            json.dumps({}),
        ],
        [
            "org.reactobus.2",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
            json.dumps({}),
        ],
        [
            "org.reactobus.3",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
            json.dumps({}),
        ],
        [
            "org.reactobus.4",
            str(uuid.uuid1()),
            "2016/01/01",
            "lavaserver",
            json.dumps({}),
        ],
        [
            "org.reactobus.5",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
            json.dumps({}),
        ],
    ]
    with pytest.raises(IndexError):
        db.run()
    # Force the databse flush
    db.save_to_db()
    assert len(sub.recv) == 0

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
        self.raise_on_bulk = False

    def bulk_save_objects(self, messages):
        if self.raise_on_bulk:
            self.messages = 0
            raise SQLAlchemyError
        else:
            self.messages = len(messages)

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
    zmq_instance = mock.ZMQContextInstance()
    monkeypatch.setattr(zmq.Context, "instance", zmq_instance)
    sessions_mock = SessionsMock()

    def mock_sessionmaker(bind):
        return sessions_mock

    monkeypatch.setattr(sqlalchemy.orm, "sessionmaker", mock_sessionmaker)
    monkeypatch.setattr(zmq, "Poller", mock.ZMQPoller)

    # Reload the module to apply the monkey patching
    import reactobus.db
    from reactobus.db import DB

    imp.reload(reactobus.db)

    # Create the DB
    dbname = tmpdir.join("testing.sqlite3")
    db_url = "sqlite:///%s" % dbname
    db = DB({"url": db_url}, "inproc://test_run")

    # Run a first time to do the setup
    with pytest.raises(IndexError):
        db.run()
    sub = zmq_instance.socks[zmq.SUB]

    # Run with two messages
    sub.recv = [
        [
            "org.reactobus.1",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
            json.dumps({}),
        ],
        [
            "org.reactobus.1",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
            json.dumps({}),
        ],
    ]

    with pytest.raises(IndexError):
        db.run()
    db.save_to_db()
    assert len(sub.recv) == 0
    assert sessions_mock.session_mock.messages == 2
    assert sessions_mock.session_mock.commits == 3

    # Re-run with two messages but raise on session.add()
    sub.recv = [
        [
            "org.reactobus.1",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
            json.dumps({}),
        ],
        [
            "org.reactobus.1",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
            json.dumps({}),
        ],
    ]
    sessions_mock.session_mock.raise_on_bulk = True
    sessions_mock.session_mock.messages = 4212
    sessions_mock.session_mock.commits = 0
    with pytest.raises(IndexError):
        db.run()
    db.save_to_db()
    assert len(sub.recv) == 0
    assert sessions_mock.session_mock.messages == 0
    assert sessions_mock.session_mock.commits == 0

    # Re-run with two invalid messages
    sub.recv = [
        [
            "org.reactobus.1",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
        ],
        [
            "org.reactobus.1",
            str(uuid.uuid1()),
            datetime.datetime.utcnow().isoformat(),
            "lavaserver",
            json.dumps({}),
        ],
    ]
    sessions_mock.session_mock.raise_on_bulk = False
    sessions_mock.session_mock.messages = 0
    sessions_mock.session_mock.commits = 0
    with pytest.raises(IndexError):
        db.run()
    db.save_to_db()
    assert len(sub.recv) == 0
    assert sessions_mock.session_mock.messages == 1
    assert sessions_mock.session_mock.commits == 3
