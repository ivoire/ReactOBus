import logging
import threading

LOG = logging.getLogger('ReactOBus.lib.core')


class Core(threading.Thread):
    def __init__(self, queue_in):
        super().__init__()
        self.q_in = queue_in

    def run(self):
        while True:
            msg = self.q_in.get()
            LOG.debug("New message: %s", msg)
            # TODO: Dispatch on all listeners

            self.q_in.task_done()
