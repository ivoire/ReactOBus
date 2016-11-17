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

import zmq


class ZMQSock(object):
    def __init__(self, sock_type):
        self.sock_type = sock_type
        self.connected = False
        self.bound = False
        self.url = None
        self.opts = {}
        self.send = []
        self.recv = []

    def setsockopt(self, key, value):
        if self.sock_type == zmq.SUB:
            assert key == zmq.SUBSCRIBE
            assert value == b""
        else:
            assert self.sock_type == zmq.PUB
            assert key == zmq.SNDHWM
            assert value == 0
        self.opts[key] = value

    def connect(self, url):
        assert self.sock_type in [zmq.DEALER, zmq.PUSH, zmq.SUB]
        self.url = url
        self.connected = True

    def bind(self, url):
        assert self.sock_type in [zmq.DEALER, zmq.PUB, zmq.PULL]
        self.url = url
        self.bound = True

    def recv_multipart(self):
        return self.recv.pop(0)

    def send_multipart(self, msg):
        self.send.append(msg)


class ZMQContextInstance(object):
    def __init__(self):
        self.socks = {}

    def __call__(self):
        return self

    def socket(self, sock_type):
        if sock_type not in self.socks:
            self.socks[sock_type] = ZMQSock(sock_type)
        return self.socks[sock_type]
