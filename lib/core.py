import json
import logging
import multiprocessing
import uuid
import zmq
from zmq.utils.strtypes import b

LOG = logging.getLogger("ROB.lib.core")


class Core(multiprocessing.Process):
    def __init__(self):
        super().__init__()

    def run(self):
        # Create the ZMQ context
        context = zmq.Context()
        pull = context.socket(zmq.PULL)
        pull.bind("ipc:///tmp/ReactOBus.inbound")
        pub = context.socket(zmq.PUB)
        pub.bind("ipc:///tmp/ReactOBus.outbound")

        # TODO: add a way to quit
        i = 0
        while True:
            i += 1
            msg = pull.recv_multipart()
            LOG.debug("Receiving: %s", msg)

            # Create a uniq id
            uid = uuid.uuid1()

            # Publish to all outputs
            pub.send_multipart([msg[0], b(str(uid)), msg[1]])

            if i % 1000 == 0:
                LOG.info(i)
