import logging
import multiprocessing
import zmq


class Output(multiprocessing.Process):
    classname = ""

    @classmethod
    def select(cls, classname, name, options, outbound):
        for sub in cls.__subclasses__():
            if sub.classname == classname:
                return sub(name, options, outbound)
        raise NotImplementedError

    def setup(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class ZMQPub(Output):
    classname = "ZMQPub"

    def __init__(self, name, options, outbound):
        super().__init__()
        self.url = options["url"]
        self.LOG = logging.getLogger("ROB.lib.output.%s" % name)
        self.outbound = outbound

    def setup(self):
        self.LOG.debug("Setting up %s", self.name)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.PUB)
        self.LOG.debug("Listening on %s", self.url)
        self.sock.bind(self.url)

        self.sub = self.context.socket(zmq.SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")
        self.sub.connect(self.outbound)

    def run(self):
        self.setup()
        # TODO: this is a dummy class.
        while True:
            msg = self.sub.recv_multipart()
            self.LOG.debug(msg)
            self.sock.send_multipart(msg)
