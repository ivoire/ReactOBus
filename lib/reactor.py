import logging
import multiprocessing
import re
import subprocess
import zmq
from zmq.utils.strtypes import u

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
            out = subprocess.check_output(args, stderr=subprocess.STDOUT, timeout=self.timeout)
        except OSError as err:
            LOG.error("Unable to run %s (%s)", args, err)
        except subprocess.TimeoutExpired:
            LOG.error("Timeout when running %s", args)
        else:
            LOG.debug("=> %s", out)


class Reactor(multiprocessing.Process):
    def __init__(self, options, outbound):
        super().__init__()
        self.options = options
        self.matchers = []
        self.outbound = outbound

    def setup(self):
        # Connect to the stream
        self.context = zmq.Context()
        self.sub = self.context.socket(zmq.SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")
        self.sub.connect(self.outbound)

        # Loop on all rules
        for rule in self.options["rules"]:
            m = Matcher(rule)
            self.matchers.append(m)

    def run(self):
        self.setup()
        while True:
            msg = self.sub.recv_multipart()
            try:
                topic = u(msg[0])
                uuid  = u(msg[1])
                data  = u(msg[2])
            except IndexError:
                LOG.error("Invalid message: %s", msg)
                continue

            for m in self.matchers:
                if m.match(topic, uuid, data):
                    LOG.debug("%s matching %s", msg, m.name)
                    m.run(topic, uuid, data)
