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
import multiprocessing
from setproctitle import setproctitle
import zmq

LOG = logging.getLogger("ROB.core")


class Core(multiprocessing.Process):
    def __init__(self, inbound, outbound):
        super().__init__()
        self.inbound = inbound
        self.outbound = outbound

    def run(self):
        setproctitle("ReactOBus [core]")
        # Create the ZMQ context
        self.context = zmq.Context.instance()
        self.pull = self.context.socket(zmq.PULL)
        LOG.debug("Binding inbound (%s)", self.inbound)
        self.pull.bind(self.inbound)
        self.pub = self.context.socket(zmq.PUB)
        # Set 0 limit on input and output HWM
        self.pub.setsockopt(zmq.SNDHWM, 0)
        LOG.debug("Binding outbound (%s)", self.outbound)
        self.pub.bind(self.outbound)

        while True:
            msg = self.pull.recv_multipart()
            LOG.debug(msg)

            # TODO: use a proxy
            # Publish to all outputs
            self.pub.send_multipart(msg)
