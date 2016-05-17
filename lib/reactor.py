import logging
import multiprocessing
import re
import subprocess
import threading
import zmq
from zmq.utils.strtypes import b, u

LOG = logging.getLogger("ROB.lib.reactor")


class Matcher(object):
    def __init__(self, rule):
        self.name = rule["name"]
        self.field = rule["match"]["field"]
        self.pattern = re.compile(rule["match"]["pattern"])
        self.bin = rule["exec"]["path"]
        self.timeout = rule["exec"]["timeout"]
        self.args = rule["exec"]["args"]

    def match(self, topic, uuid, data):
        if self.field == "topic":
            return self.pattern.match(topic) is not None
        else:
            return self.pattern.match(uuid) is not None

    def run(self, topic, uuid, data):
        variables = {"topic": topic, "uuid": uuid}
        args = [self.bin]
        for arg in self.args:
            if arg[0] == '$':
                args.append(variables[arg[1:]])
            else:
                args.append(arg)

        LOG.debug("Running: %s", args)
        try:
            out = subprocess.check_output(args, stderr=subprocess.STDOUT,
                                          timeout=self.timeout)
        except OSError as err:
            LOG.error("Unable to run %s (%s)", args, err)
        except subprocess.TimeoutExpired:
            LOG.error("Timeout when running %s", args)
        else:
            LOG.debug("=> %s", out)


class Worker(threading.Thread):
    def __init__(self, matchers):
        super().__init__()
        self.matchers = matchers

    def run(self):
        self.context = zmq.Context.instance()
        self.sock = self.context.socket(zmq.DEALER)
        self.sock.connect("inproc://workers")
        while True:
            msg = self.sock.recv_multipart()
            matcher_index = int(msg[0])
            (topic, uuid, data) = msg[1:]
            LOG.debug("Running matcher n°%d on %s", matcher_index, self.name)
            self.matchers[matcher_index].run(topic, uuid, data)


class Reactor(multiprocessing.Process):
    def __init__(self, options, outbound):
        super().__init__()
        self.options = options
        self.matchers = []
        self.outbound = outbound
        self.workers = []

    def setup(self):
        # Connect to the stream
        self.context = zmq.Context.instance()
        self.sub = self.context.socket(zmq.SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")
        LOG.debug("Connecting to outbound (%s)", self.outbound)
        self.sub.connect(self.outbound)

        # Loop on all rules
        for rule in self.options["rules"]:
            m = Matcher(rule)
            self.matchers.append(m)

        # Create the workers
        self.ctrl = self.context.socket(zmq.DEALER)
        self.ctrl.bind("inproc://workers")

        LOG.debug("Starting %d workers", self.options["workers"])
        for _ in range(0, self.options["workers"]):
            w = Worker(self.matchers)
            w.start()
            self.workers.append(w)


    def run(self):
        self.setup()
        while True:
            msg = self.sub.recv_multipart()
            try:
                (topic, uuid, dt, data) = (u(m) for m in msg)
            except (IndexError, ValueError):
                LOG.error("Invalid message: %s", msg)
                continue

            for (i, m) in enumerate(self.matchers):
                if m.match(topic, uuid, data):
                    LOG.debug("%s matching %s", msg, m.name)
                    self.ctrl.send_multipart([b(str(i)),
                                              b(topic),
                                              b(uuid),
                                              b(dt),
                                              b(data)])
