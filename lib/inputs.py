import json
import logging
import multiprocessing
import zmq
from zmq.utils.strtypes import b, u


class Input(multiprocessing.Process):
    classname = ""

    @classmethod
    def select(cls, classname, name, options):
        for sub in cls.__subclasses__():
            if sub.classname == classname:
                return sub(name, options)
        raise NotImplementedError

    def setup(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class ZMQPull(Input):
    classname = "ZMQPull"

    def __init__(self, name,  options):
        super().__init__()
        self.url = options["url"]
        self.LOG = logging.getLogger("ROB.lib.input.%s" % name)

    def setup(self):
        self.LOG.debug("Setting up %s", self.name)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.PULL)
        self.LOG.debug("Listening on %s", self.url)
        self.sock.bind(self.url)
        self.LOG.debug("Connecting to inbound")
        self.push = self.context.socket(zmq.PUSH)
        self.push.connect("ipc:///tmp/ReactOBus.inbound")

    def run(self):
        self.setup()
        # TODO: add a way to do a clean quit
        while True:
            msg = self.sock.recv_multipart()
            # TODO: use a pipeline to transform the messages
            try:
                topic = msg[0]
                data = {}
                for (k, v) in zip(msg[1::2], msg[2::2]):
                    data[u(k)] = u(v)
            except IndexError:
                self.LOG.error("Droping invalid message")
                self.LOG.debug("=> %s", msg)
                continue
            self.LOG.debug("topic: %s, data: %s", u(topic), data)
            self.push.send_multipart([topic, b(json.dumps(data))])

    def __del__(self):
        # TODO: is it really useful to drop all messages?
        self.sock.close(linger=0)
        self.context.term()
