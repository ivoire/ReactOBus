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

import datetime
import json
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import subprocess
import time
import uuid
import zmq
from zmq.utils.strtypes import b

from ReactOBus.db import Message

def test_help():
    help_str = """usage: reactobus [-h] [-c CONFIG] [-l {DEBUG,ERROR,INFO,WARN}]
                 [--log-file LOG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        ReactOBus configuration

Logging:
  -l {DEBUG,ERROR,INFO,WARN}, --level {DEBUG,ERROR,INFO,WARN}
                        Log level (DEBUG, ERROR, INFO, WARN), default to INFO
  --log-file LOG_FILE   Log file, use '-' for stdout
"""
    assert subprocess.check_output(["python", "reactobus", "--help"],
                                   universal_newlines=True) == help_str


def test_simple_forward(tmpdir):
    conf_filename = str(tmpdir.join("conf.yaml"))
    pull_url = tmpdir.join("input.socket")
    push_url = tmpdir.join("output.socket")
    db_url = tmpdir.join("db.sqlite3")
    inbound = tmpdir.join("inbound")
    outbound = tmpdir.join("outbound")
    stdout = tmpdir.join("stdout")
    stderr = tmpdir.join("stderr")
    with open(conf_filename, "w+") as f:
        f.write("inputs:\n")
        f.write("- class: ZMQPull\n")
        f.write("  name: testing-input\n")
        f.write("  options:\n")
        f.write("    url: ipc://%s\n" % pull_url)
        f.write("db:\n")
        f.write("  url: sqlite:///%s\n" % db_url)
        f.write("core:\n")
        f.write("  inbound: ipc://%s\n" % inbound)
        f.write("  outbound: ipc://%s\n" % outbound)
        f.write("outputs:\n")
        f.write("- class: ZMQPush\n")
        f.write("  name: testing-out\n")
        f.write("  options:\n")
        f.write("    url: ipc://%s\n" % push_url)
    args = ["python", "reactobus", "--conf", conf_filename, "--level", "DEBUG",
            "--log-file", "-"]
    proc = subprocess.Popen(args, stdout=open(str(stdout), "w"),
                            stderr=open(str(stderr), "w"))

    ctx = zmq.Context.instance()
    in_sock = ctx.socket(zmq.PUSH)
    in_sock.connect("ipc://%s" % pull_url)
    out_sock = ctx.socket(zmq.PULL)
    out_sock.bind("ipc://%s" % push_url)

    # Allow the process sometime to setup and connect
    time.sleep(1)

    # Send many messages
    for i in range(0, 1000):
        data = [b"org.reactobus.test.py",
                b(str(uuid.uuid1())),
                b(datetime.datetime.utcnow().isoformat()),
                b"py.test",
                b(json.dumps({'pipeline': True}))]
        in_sock.send_multipart(data)
        assert out_sock.recv_multipart() == data

    time.sleep(2)

    proc.terminate()
    proc.wait()

    # Check the database
    Base = declarative_base()
    engine = create_engine("sqlite:///%s" % db_url)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)

    session = sessions()
    assert session.query(Message).count() == 1000
    assert session.query(Message).filter_by(topic="org.reactobus.test.py").count() == 1000
