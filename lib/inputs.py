import json
import logging
import zmq
from zmq.utils.strtypes import b, u

from .utils import Pipe


class Input(Pipe):
    pass


class ZMQ(Input):
    def __init__(self, name, options, inbound):
        super().__init__()
        self.url = options["url"]
        self.LOG = logging.getLogger("ROB.lib.input.%s" % name)
        self.inbound = inbound

    def setup(self):
        self.LOG.debug("Setting up %s", self.name)
        self.context = zmq.Context.instance()
        self.sock = self.context.socket(self.socket_type)
        if self.socket_type == zmq.PULL:
            self.LOG.debug("Listening on %s", self.url)
            self.sock.bind(self.url)
        else:
            self.LOG.debug("Connecting to %s", self.url)
            # TODO: add option
            self.sock.setsockopt(zmq.SUBSCRIBE, b"")
            self.sock.connect(self.url)

        self.LOG.debug("Connecting to inbound")
        self.push = self.context.socket(zmq.PUSH)
        self.push.connect(self.inbound)

    def run(self):
        self.setup()
        while True:
            msg = self.sock.recv_multipart()
            # TODO: use a pipeline to transform the messages
            try:
                (topic, uuid, dt, username, data) = msg[:]
            except IndexError:
                self.LOG.error("Droping invalid message")
                self.LOG.debug("=> %s", msg)
                continue
            self.LOG.debug("topic: %s, data: %s", u(topic), data)
            self.push.send_multipart(msg)


class ZMQPull(ZMQ):
    classname = "ZMQPull"

    def __init__(self, name, options, inbound):
        super().__init__(name, options, inbound)
        self.socket_type = zmq.PULL


class ZMQSub(ZMQ):
    classname = "ZMQSub"

    def __init__(self, name, options, inbound):
        super().__init__(name, options, inbound)
        self.socket_type = zmq.SUB
