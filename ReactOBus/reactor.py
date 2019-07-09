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

import json
import logging
import multiprocessing
import re
from setproctitle import setproctitle
import subprocess
import threading
import zmq
from zmq.utils.strtypes import b, u

from .utils import lookup

LOG = logging.getLogger("ROB.reactor")


class Matcher(object):
    def __init__(self, rule):
        self.name = rule["name"]
        self.field = rule["match"]["field"]
        self.patterns = []
        patterns = rule["match"]["patterns"]
        if isinstance(patterns, list):
            for pattern in patterns:
                self.patterns.append(re.compile(pattern))
        else:
            self.patterns = [re.compile(patterns)]
        self.binary = rule["exec"]["path"]
        self.timeout = rule["exec"]["timeout"]
        self.args = rule["exec"]["args"]

    def match(self, variables, data):
        # Returne True if the field does match, overwise return False
        try:
            value = lookup(self.field, variables, data)
            return any([p.match(value) is not None for p in self.patterns])
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
                args.append(lookup(field[1:], variables, data))
            elif field.startswith("stdin:"):
                if field[6:].startswith("$"):
                    stdin.append(lookup(field[7:], variables, data))
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
            out = subprocess.check_output([b(a)for a in args],
                                          stderr=subprocess.STDOUT,
                                          input=b(stdin_s), timeout=self.timeout)
        except subprocess.TimeoutExpired:
            LOG.error("Timeout when running %s", args)
        except (OSError, subprocess.SubprocessError) as exc:
            LOG.error("Unable to run %s (%s)", args, exc)
        else:
            LOG.debug("=> '%s'", u(out))


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
                (topic, uuid, dt, username, data) = (u(m) for m in msg[1:])
                data_parsed = json.loads(data)
                LOG.debug("Running matcher num %d on %s",
                          matcher_index, self.name)
                self.matchers[matcher_index].run(topic, uuid, dt,
                                                 username, data_parsed)
            # No need to except JSONDecodeError which is a subclass of
            # ValueError. Moreover, in python3.4 JSONDecodeError does not
            # exist.
            except ValueError:
                LOG.error("Invalid message %s", msg)


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
                (topic, uuid, datetime, username, data) = msg[:]
                data_parsed = json.loads(u(data))
            # No need to except JSONDecodeError which is a subclass of
            # ValueError. Moreover, in python3.4 JSONDecodeError does not
            # exist.
            except ValueError:
                LOG.error("Invalid message: %s", msg)
                continue

            variables = {"topic": u(topic),
                         "uuid": u(uuid),
                         "datetime": u(datetime),
                         "username": u(username)}
            for (i, m) in enumerate(self.matchers):
                if m.match(variables, data_parsed):
                    LOG.debug("%s matching %s", msg, m.name)
                    self.ctrl.send_multipart([b(str(i)),
                                              topic,
                                              uuid,
                                              datetime,
                                              username,
                                              data])
