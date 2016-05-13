import logging
import multiprocessing
import uuid
import zmq
from zmq.utils.strtypes import b

LOG = logging.getLogger("ROB.lib.core")


class Core(multiprocessing.Process):
    def __init__(self, inbound, outbound):
        super().__init__()
        self.inbound = inbound
        self.outbound = outbound

    def run(self):
        # Create the ZMQ context
        self.context = zmq.Context.instance()
        self.pull = self.context.socket(zmq.PULL)
        self.pull.bind(self.inbound)
        self.pub = self.context.socket(zmq.PUB)
        # Set 0 limit on input and output HWM
        self.pub.setsockopt(zmq.SNDHWM, 0)
        LOG.debug("Binding outbound (%s)", self.outbound)
        self.pub.bind(self.outbound)

        while True:
            msg = self.pull.recv_multipart()
            LOG.debug(msg)

            # Add an UUID
            uid = uuid.uuid1()
            new_msg = [msg[0], b(str(uid)), msg[1]]

            # Publish to all outputs
            self.pub.send_multipart(new_msg)
