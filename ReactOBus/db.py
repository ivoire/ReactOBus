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
import logging
import multiprocessing
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from setproctitle import setproctitle
import time
import zmq
from zmq.utils.strtypes import u

LOG = logging.getLogger("ROB.DB")


Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    topic = Column(String, index=True)
    uuid = Column(String, index=True)
    datetime = Column(DateTime(timezone=True), index=True)
    username = Column(String, index=True)
    data = Column(String)


class DB(multiprocessing.Process):
    def __init__(self, options, outbound):
        super().__init__()
        self.options = options
        self.outbound = outbound
        self.engine = None
        self.sessions = None
        self.messages = []

    def setup(self):
        setproctitle("ReactOBus [db]")
        # Subscribe to outbound
        context = zmq.Context.instance()
        self.sub = context.socket(zmq.SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")
        LOG.debug("Connecting to outbound (%s)", self.outbound)
        self.sub.connect(self.outbound)
        # Add a poller for the subscription
        self.poller = zmq.Poller()
        self.poller.register(self.sub, zmq.POLLIN)

        # Setup SQLAlchemy
        self.engine = create_engine(self.options["url"])
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)

    def save_to_db(self):
        session = self.sessions()
        max_db_commit_retry = 3
        # Retry the database commit
        err_msg = ""
        for retry in range(1, max_db_commit_retry + 1):
            try:
                session.bulk_save_objects(self.messages)
                session.commit()
                self.messages = []
                return
            except SQLAlchemyError as err:
                err_msg = str(err)
        # Impossible to commit the message
        LOG.error("Unable to commit to the database, "
                  "dropping the message")
        LOG.error("Database error: %s", err_msg)

    def run(self):
        self.setup()

        # Create a session
        last_save = time.time()
        self.messages = []
        while True:
            sockets = dict(self.poller.poll(1000))
            if sockets.get(self.sub) == zmq.POLLIN:
                msg = self.sub.recv_multipart()
                try:
                    (topic, uuid, dt, username, data) = (u(m) for m in msg)
                    dt = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f')
                    self.messages.append(Message(topic=topic, uuid=uuid,
                                                 datetime=dt,
                                                 username=username, data=data))
                except ValueError:
                    LOG.error("Invalid message: %s", msg)
                    continue
                except SQLAlchemyError as err:
                    LOG.error("Unable to build the new message row: %s", err)
                    continue

            # Save to DB only every one second
            now = time.time()
            if len(self.messages) >= 1000 or now - last_save > 1:
                LOG.info("saving to db")
                self.save_to_db()
                last_save = now
