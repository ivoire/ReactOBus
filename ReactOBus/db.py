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

    def setup(self):
        setproctitle("ReactOBus [db]")
        context = zmq.Context.instance()
        self.sub = context.socket(zmq.SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")
        LOG.debug("Connecting to outbound (%s)", self.outbound)
        self.sub.connect(self.outbound)

        # Setup sqlalchemy
        self.engine = create_engine(self.options["url"])
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)

    def run(self):
        self.setup()

        max_db_commit_retry = 3
        while True:
            msg = self.sub.recv_multipart()
            try:
                (topic, uuid, dt, username, data) = (u(m) for m in msg)
                dt = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f')
            except (IndexError, ValueError):
                LOG.error("Invalid message: %s", msg)
                continue

            # Save into the database
            try:
                session = self.sessions()
                message = Message(topic=topic, uuid=uuid, datetime=dt,
                                  username=username, data=data)
                session.add(message)
            except SQLAlchemyError as err:
                LOG.error("Unable to build the new message row: %s", err)
                continue

            # Retry the database commit
            for retry in range(1, max_db_commit_retry + 1):
                try:
                    session.commit()
                except SQLAlchemyError as err:
                    if retry == max_db_commit_retry:
                        LOG.error("Unable to commit to the database, dropping the message")
                        LOG.error("Database error: %s", err)
                else:
                    break
