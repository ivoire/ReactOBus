import logging
import multiprocessing
import zmq


class Output(multiprocessing.Process):
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


class ZMQPub(Output):
    classname = "ZMQPub"

    def __init__(self, name, options):
        super().__init__()
        self.url = options["url"]
        self.LOG = logging.getLogger("ROB.lib.output.%s" % name)

    def setup(self):
        self.LOG.debug("Setting up %s", self.name)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.PUB)
        self.LOG.debug("Listening on %s", self.url)
        self.sock.bind(self.url)

    def run(self):
        self.setup()
        #while True:
        #    pass

    def __del__(self):
        # TODO: is it really useful to drop all messages
        self.sock.close(linger=0)
        self.context.term()
