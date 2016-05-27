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
import zmq
from zmq.utils.strtypes import u

from .utils import Pipe


class Input(Pipe):
    pass


class ZMQ(Input):
    def __init__(self, name, options, inbound):
        super().__init__()
        self.url = options["url"]
        self.LOG = logging.getLogger("ROB.lib.input.%s" % name)
        self.inbound = inbound

    def setup(self):
        self.LOG.debug("Setting up %s", self.name)
        setproctitle("ReactOBus [in-%s]" % self.name)
        self.context = zmq.Context.instance()
        self.sock = self.context.socket(self.socket_type)
        if self.socket_type == zmq.PULL:
            self.LOG.debug("Listening on %s", self.url)
            self.sock.bind(self.url)
        else:
            self.LOG.debug("Connecting to %s", self.url)
            # TODO: add option
            self.sock.setsockopt(zmq.SUBSCRIBE, b"")
            self.sock.connect(self.url)

        self.LOG.debug("Connecting to inbound")
        self.push = self.context.socket(zmq.PUSH)
        self.push.connect(self.inbound)

    def run(self):
        self.setup()
        while True:
            msg = self.sock.recv_multipart()
            # TODO: use a pipeline to transform the messages
            try:
                (topic, uuid, dt, username, data) = msg[:]
            except IndexError:
                self.LOG.error("Droping invalid message")
                self.LOG.debug("=> %s", msg)
                continue
            self.LOG.debug("topic: %s, data: %s", u(topic), data)
            self.push.send_multipart(msg)


class ZMQPull(ZMQ):
    classname = "ZMQPull"

    def __init__(self, name, options, inbound):
        super().__init__(name, options, inbound)
        self.socket_type = zmq.PULL


class ZMQSub(ZMQ):
    classname = "ZMQSub"

    def __init__(self, name, options, inbound):
        super().__init__(name, options, inbound)
        self.socket_type = zmq.SUB
