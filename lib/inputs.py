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
        # TODO: add a way to do a clean quit
        while True:
            msg = self.sock.recv_multipart()
            # TODO: use a pipeline to transform the messages
            try:
                topic = msg[0]
                data = {}
                for (k, v) in zip(msg[1::2], msg[2::2]):
                    data[k] = v
            except IndexError:
                self.LOG.error("Droping invalid message")
                self.LOG.debug("=> %s", msg)
                continue
            self.LOG.debug("topic: %s, data: %s", topic, data)
            self.queue.put((topic, data))

    def __del__(self):
        # TODO: is it really useful to drop all messages?
        self.sock.close(linger=0)
        self.context.term()
