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
from zmq.auth import load_certificate
from zmq.auth.thread import ThreadAuthenticator

from .utils import Pipe


class Output(Pipe):
    pass


class ZMQ(Output):
    def __init__(self, name, options, outbound):
        super().__init__()
        self.url = options["url"]
        self.LOG = logging.getLogger("ROB.output.%s" % name)
        self.procname = name
        self.outbound = outbound

    def secure_setup(self):
        raise NotImplementedError

    def setup(self):
        self.LOG.debug("Setting up")
        setproctitle("ReactOBus [out-%s-%s]" % (self.name, self.procname))
        self.context = zmq.Context.instance()

        self.sock = self.context.socket(self.socket_type)
        if self.socket_type == zmq.PUB:
            self.LOG.debug("Listening on %s", self.url)
            self.sock.bind(self.url)
        else:
            self.LOG.debug("Connecting to %s", self.url)
            self.sock.connect(self.url)

        self.LOG.debug("Connecting to outbound")
        self.sub = self.context.socket(zmq.SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")
        self.sub.connect(self.outbound)

    def run(self):
        self.setup()
        # TODO: this is a dummy class.
        while True:
            msg = self.sub.recv_multipart()
            self.LOG.debug(msg)
            self.sock.send_multipart(msg)


class ZMQPub(ZMQ):
    classname = "ZMQPub"

    def __init__(self, name, options, outbound):
        super().__init__(name, options, outbound)
        self.socket_type = zmq.PUB

    def secure_setup(self):
        # Load certificates
        # TODO: handle errors
        self.auth = ThreadAuthenticator(self.context)
        self.auth.start()
        self.LOG.debug("Server keys in %s", self.secure_config["self"])
        sock_pub, sock_priv = load_certificate(self.secure_config["self"])
        if self.secure_config.get("clients", None) is not None:
            self.LOG.debug("Client certificates in %s",
                           self.secure_config["clients"])
            self.auth.configure_curve(domain='*',
                                      location=self.secure_config["clients"])
        else:
            self.LOG.debug("Every clients can connect")
            self.auth.configure_curve(domain='*',
                                      location=zmq.auth.CURVE_ALLOW_ANY)

        # Setup the socket
        self.sock.curve_publickey = sock_pub
        self.sock.curve_secretkey = sock_priv
        self.sock.curve_server = True


class ZMQPush(ZMQ):
    classname = "ZMQPush"

    def __init__(self, name, options, outbound):
        super().__init__(name, options, outbound)
        self.socket_type = zmq.PUSH

    def secure_setup(self):
        # TODO: handle errors
        (sock_pub, sock_priv) = load_certificate(self.secure_setup["self"])
        (server_public, _) = load_certificate(self.secure_setup["server"])
        self.sock.curve_publickey = sock_pub
        self.sock.curve_secretkey = sock_priv
        self.sock.curve_serverkey = server_public
