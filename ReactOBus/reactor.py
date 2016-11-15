# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2016 Rémi Duraffort
# This file is part of ReactOBus.
#
# ReactOBus is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ReactOBus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with ReactOBus.  If not, see <http://www.gnu.org/licenses/>

import logging
from setproctitle import setproctitle
import multiprocessing
import re
import subprocess
import threading
import zmq
from zmq.utils.strtypes import b, u

LOG = logging.getLogger("ROB.reactor")


class Matcher(object):
    def __init__(self, rule):
        self.name = rule["name"]
        self.field = rule["match"]["field"]
        self.pattern = re.compile(rule["match"]["pattern"])
        self.binary = rule["exec"]["path"]
        self.timeout = rule["exec"]["timeout"]
        self.args = rule["exec"]["args"]

    @classmethod
    def lookup(cls, name, variables, data):
        # Lookup in variables and fallback to data if the name is of the form
        # "data.key"
        if name in variables:
            return variables[name]
        elif name == "data":
            return data
        elif name.startswith("data."):
            sub_name = name[5:]
            if sub_name in data:
                return data[sub_name]
        raise KeyError(name)

    def match(self, variables, data):
        # Returne True if the field does match, overwise return False
        try:
            value = self.lookup(self.field, variables, data)
            return self.pattern.match(value) is not None
        except KeyError:
            return False

    def build_args(self, topic, uuid, datetime, username, data):
        variables = {"topic": topic,
                     "uuid": uuid,
                     "datetime": datetime,
                     "username": username}

        args = [self.binary]
        stdin = []
        # Make the substitution
        for field in self.args:
            if field.startswith("$"):
                args.append(self.lookup(field[1:], variables, data))
            elif field.startswith("stdin:"):
                if field[6:].startswith("$"):
                    stdin.append(self.lookup(field[7:], variables, data))
                else:
                    stdin.append(field[6:])
            else:
                args.append(field)
        return (args, "\n".join(stdin))

    def run(self, topic, uuid, datetime, username, data):
        try:
            (args, stdin_s) = self.build_args(topic, uuid, datetime, username,
                                              data)
        except KeyError as exc:
            LOG.error("Unable to build the argument list: %s", exc)
            return

        LOG.debug("Running: %s", args)
        try:
            out = subprocess.check_output(args, stderr=subprocess.STDOUT,
                                          universal_newlines=True,
                                          input=stdin_s, timeout=self.timeout)
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
            try:
                matcher_index = int(msg[0])
                (topic, uuid, dt, username, data) = msg[1:]
                LOG.debug("Running matcher num %d on %s", matcher_index, self.name)
                self.matchers[matcher_index].run(topic, uuid, dt, username, data)
            except ValueError:
                LOG.error("Invalid message")


class Reactor(multiprocessing.Process):
    def __init__(self, options, outbound):
        super().__init__()
        self.options = options
        self.matchers = []
        self.outbound = outbound
        self.workers = []

    def setup(self):
        setproctitle("ReactOBus [reactor]")
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
                (topic, uuid, datetime, username, data) = (u(m) for m in msg)
            except (IndexError, ValueError):
                LOG.error("Invalid message: %s", msg)
                continue

            variables = {"topic": topic,
                         "uuid": uuid,
                         "datetime": datetime,
                         "username": username}
            for (i, m) in enumerate(self.matchers):
                if m.match(variables, data):
                    LOG.debug("%s matching %s", msg, m.name)
                    self.ctrl.send_multipart([b(str(i)),
                                              b(topic),
                                              b(uuid),
                                              b(datetime),
                                              b(username),
                                              b(data)])
