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

from .utils import Pipe


class Output(Pipe):
    pass


class ZMQPub(Output):
    classname = "ZMQPub"

    def __init__(self, name, options, outbound):
        super().__init__()
        self.url = options["url"]
        self.LOG = logging.getLogger("ROB.lib.output.%s" % name)
        self.outbound = outbound

    def setup(self):
        self.LOG.debug("Setting up %s", self.name)
        setproctitle("ReactOBus [out-%s]" % self.name)
        self.context = zmq.Context.instance()
        self.pub = self.context.socket(zmq.PUB)
        self.LOG.debug("Listening on %s", self.url)
        self.pub.bind(self.url)

        self.sub = self.context.socket(zmq.SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")
        self.sub.connect(self.outbound)

    def run(self):
        self.setup()
        # TODO: this is a dummy class.
        while True:
            msg = self.sub.recv_multipart()
            self.LOG.debug(msg)
            self.pub.send_multipart(msg)
