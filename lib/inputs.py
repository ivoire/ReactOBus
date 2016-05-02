import logging
import threading
import zmq


class Input(threading.Thread):
    name = ""

    @classmethod
    def select(cls, classname, name, queue, options):
        for sub in cls.__subclasses__():
            if sub.classname == classname:
                return sub(name, queue, options)
        raise NotImplementedError

    def setup(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class ZMQPull(Input):
    classname = "ZMQPull"

    def __init__(self, name, queue, options):
        super().__init__()
        self.queue = queue
        self.url = options["url"]
        self.LOG = logging.getLogger("ReactOBus.lib.inputs.%s" % name)

    def setup(self):
        self.LOG.debug("Setting up %s", self.name)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.PULL)
        self.LOG.debug("Listening on %s", self.url)
        self.sock.bind(self.url)

    def run(self):
        self.setup()
        while True:
            pass

    def __del__(self):
        # TODO: is it really useful to drop all messages
        self.sock.close(linger=0)
        self.context.term()
