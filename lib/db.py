import datetime
import logging
import multiprocessing
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from setproctitle import setproctitle
import zmq
from zmq.utils.strtypes import u

LOG = logging.getLogger("ROB.lib.DB")


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

        while True:
            msg = self.sub.recv_multipart()
            try:
                (topic, uuid, dt, username, data) = (u(m) for m in msg)
            except (IndexError, ValueError):
                LOG.error("Invalid message: %s", msg)
                continue

            # Save into the database
            session = self.sessions()
            dt = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f')
            message = Message(topic=topic, uuid=uuid, datetime=dt, username=username, data=data)
            session.add(message)
            session.commit()
