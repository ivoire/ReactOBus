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
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
from zmq.utils.strtypes import u

from .utils import Pipe


class Input(Pipe):
    pass


class ZMQ(Input):
    def __init__(self, name, options, inbound):
        super().__init__()
        self.url = options["url"]
        self.secure_config = options.get("encryption", None)
        self.LOG = logging.getLogger("ROB.input.%s" % name)
        self.procname = name
        self.inbound = inbound
        self.auth = None

    def secure_setup(self):
        raise NotImplementedError

    def setup(self):
        self.LOG.debug("Setting up")
        setproctitle("ReactOBus [in-%s-%s]" % (self.name, self.procname))
        self.context = zmq.Context.instance()
        self.sock = self.context.socket(self.socket_type)
        # Setup encryption if needed
        if self.secure_config is not None:
            self.LOG.debug("Starting encryption")
            self.secure_setup()

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
            except ValueError:
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

    def secure_setup(self):
        # Load certificates
        # TODO: handle errors
        self.auth = ThreadAuthenticator(self.context)
        self.auth.start()
        self.LOG.debug("Server keys in %s", self.secure_config["self"])
        sock_pub, sock_priv = zmq.auth.load_certificate(self.secure_config["self"])
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


class ZMQSub(ZMQ):
    classname = "ZMQSub"

    def __init__(self, name, options, inbound):
        super().__init__(name, options, inbound)
        self.socket_type = zmq.SUB

    def secure_setup(self):
        # Load certificates
        # TODO: handle errors
        sock_pub, sock_priv = zmq.auth.load_certificate(self.secure_config["self"])
        server_public, _ = zmq.auth.load_certificate(self.secure_config["server"])
        self.sock.curve_publickey = sock_pub
        self.sock.curve_secretkey = sock_priv
        self.sock.curve_serverkey = server_public
