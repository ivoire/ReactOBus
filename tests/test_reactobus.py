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
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import subprocess
import time
import uuid
import zmq
from zmq.auth import create_certificates, load_certificate
from zmq.auth.thread import ThreadAuthenticator
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
    assert subprocess.check_output(["python3", "reactobus", "--help"],
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
    with open(conf_filename, "w") as f:
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
    args = ["python3", "reactobus", "--conf", conf_filename, "--level", "DEBUG",
            "--log-file", "-"]
    proc = subprocess.Popen(args,
                            stdout=open(str(stdout), "w"),
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
    assert session.query(Message).filter_by(topic="org.reactobus.test.py")\
                  .count() == 1000


def test_reactor(tmpdir):
    conf_filename = str(tmpdir.join("conf.yaml"))
    pull_url = tmpdir.join("input.socket")
    inbound = tmpdir.join("inbound")
    outbound = tmpdir.join("outbound")
    stdout = tmpdir.join("stdout")
    stderr = tmpdir.join("stderr")
    script = tmpdir.join("script.sh")
    script_stdin = tmpdir.join("script.stdin")
    script_args = tmpdir.join("script.args")

    with open(str(script), "w") as f:
        f.write("#!/bin/sh\n")
        f.write("cat /dev/stdin > %s\n" % script_stdin)
        f.write("echo $@ > %s\n" % script_args)
    os.chmod(str(script), 0o755)

    with open(conf_filename, "w") as f:
        f.write("inputs:\n")
        f.write("- class: ZMQPull\n")
        f.write("  name: testing-input\n")
        f.write("  options:\n")
        f.write("    url: ipc://%s\n" % pull_url)
        f.write("reactor:\n")
        f.write("  workers: 2\n")
        f.write("  rules:\n")
        f.write("  - name: org.videolan.git\n")
        f.write("    match:\n")
        f.write("      field: topic\n")
        f.write("      pattern: ^org\.videolan\.git$\n")
        f.write("    exec:\n")
        f.write("      path: %s\n" % script)
        f.write("      timeout: 1\n")
        f.write("      args:\n")
        f.write("      - topic\n")
        f.write("      - $topic\n")
        f.write("      - data.url\n")
        f.write("      - $data.url\n")
        f.write("      - data\n")
        f.write("      - $data\n")
        f.write("      - stdin:user\n")
        f.write("      - stdin:$username\n")
        f.write("      - stdin:url\n")
        f.write("      - stdin:$data.url\n")
        f.write("core:\n")
        f.write("  inbound: ipc://%s\n" % inbound)
        f.write("  outbound: ipc://%s\n" % outbound)
    args = ["python3", "reactobus", "--conf", conf_filename, "--level", "DEBUG",
            "--log-file", "-"]
    proc = subprocess.Popen(args,
                            stdout=open(str(stdout), "w"),
                            stderr=open(str(stderr), "w"))

    ctx = zmq.Context.instance()
    in_sock = ctx.socket(zmq.PUSH)
    in_sock.connect("ipc://%s" % pull_url)

    # Allow the process sometime to setup and connect
    time.sleep(1)

    data = {"url": "https://code.videolan.org/éêï",
            "username": "git"}
    in_sock.send_multipart([b"org.videolan.git",
                            b(str(uuid.uuid1())),
                            b(datetime.datetime.utcnow().isoformat()),
                            b("vidéolan-git"),
                            b(json.dumps(data))])

    time.sleep(1)
    proc.terminate()
    proc.wait()

    with open(str(script_args), "r") as f:
        line = f.readlines()[0]
        (begin, data_recv) = line.split("{")
        data_recv = json.loads("{" + data_recv)
        assert data == data_recv
        assert begin == "topic org.videolan.git data.url https://code.videolan.org/éêï data "
    with open(str(script_stdin), "r") as f:
        lines = f.readlines()
        assert len(lines) == 4
        assert lines[0] == "user\n"
        assert lines[1] == "vidéolan-git\n"
        assert lines[2] == "url\n"
        assert lines[3] == "https://code.videolan.org/éêï"


def test_encryption(tmpdir):
    # Create the tmp names
    conf_filename = str(tmpdir.join("conf.yaml"))
    pull_url = tmpdir.join("input.pull.socket")
    pull_cert_dir = tmpdir.mkdir("input.pull")
    pull_clients_cert_dir = pull_cert_dir.mkdir("clients")
    sub_url = tmpdir.join("input.sub.socket")
    sub_cert_dir = tmpdir.mkdir("input.sub")
    push_url = tmpdir.join("output.push.socket")
    inbound = tmpdir.join("inbound")
    outbound = tmpdir.join("outbound")
    stdout = tmpdir.join("stdout")
    stderr = tmpdir.join("stderr")

    # Create the certificates
    create_certificates(str(pull_cert_dir), "pull")
    create_certificates(str(pull_clients_cert_dir), "client1")
    create_certificates(str(pull_clients_cert_dir), "client2")
    create_certificates(str(sub_cert_dir), "sub")
    create_certificates(str(sub_cert_dir), "sub-server")

    with open(conf_filename, "w") as f:
        f.write("inputs:\n")
        f.write("- class: ZMQPull\n")
        f.write("  name: in-pull\n")
        f.write("  options:\n")
        f.write("    url: ipc://%s\n" % pull_url)
        f.write("    encryption:\n")
        f.write("      self: %s\n" % pull_cert_dir.join("pull.key_secret"))
        f.write("      clients: %s\n" % pull_clients_cert_dir)
        f.write("- class: ZMQSub\n")
        f.write("  name: in-sub\n")
        f.write("  options:\n")
        f.write("    url: ipc://%s\n" % sub_url)
        f.write("    encryption:\n")
        f.write("      self: %s\n" % sub_cert_dir.join("sub.key_secret"))
        f.write("      server: %s\n" % sub_cert_dir.join("sub-server.key"))
        f.write("core:\n")
        f.write("  inbound: ipc://%s\n" % inbound)
        f.write("  outbound: ipc://%s\n" % outbound)
        f.write("outputs:\n")
        f.write("- class: ZMQPush\n")
        f.write("  name: out-push\n")
        f.write("  options:\n")
        f.write("    url: ipc://%s\n" % push_url)
    args = ["python3", "reactobus", "--conf", conf_filename, "--level", "DEBUG",
            "--log-file", "-"]
    proc = subprocess.Popen(args,
                            stdout=open(str(stdout), "w"),
                            stderr=open(str(stderr), "w"))

    # Create the input sockets
    ctx = zmq.Context.instance()
    in_sock = ctx.socket(zmq.PUSH)
    (server_public, _) = load_certificate(str(pull_cert_dir.join("pull.key")))
    in_sock.curve_serverkey = server_public
    (client_public, client_private) = load_certificate(str(pull_clients_cert_dir.join("client1.key_secret")))
    in_sock.curve_publickey = client_public
    in_sock.curve_secretkey = client_private
    in_sock.connect("ipc://%s" % pull_url)

    out_sock = ctx.socket(zmq.PULL)
    out_sock.bind("ipc://%s" % push_url)

    pub_sock = ctx.socket(zmq.PUB)
    auth = ThreadAuthenticator(ctx)
    auth.start()
    auth.configure_curve(domain="*", location=str(sub_cert_dir))
    (server_public, server_secret) = load_certificate(str(sub_cert_dir.join("sub-server.key_secret")))
    pub_sock.curve_publickey = server_public
    pub_sock.curve_secretkey = server_secret
    pub_sock.curve_server = True
    pub_sock.bind("ipc://%s" % sub_url)

    # Allow the process sometime to setup and connect
    time.sleep(1)

    # Send some data
    data = [b"org.videolan.git",
            b(str(uuid.uuid1())),
            b(datetime.datetime.utcnow().isoformat()),
            b("videolan-git"),
            b(json.dumps({"url": "https://code.videolan.org/éêï",
                          "username": "git"}))]
    in_sock.send_multipart(data)
    msg = out_sock.recv_multipart()
    assert msg == data

    data = [b"org.videolan.git",
            b(str(uuid.uuid1())),
            b(datetime.datetime.utcnow().isoformat()),
            b("videolan-git"),
            b(json.dumps({"url": "https://code.videolan.org/éêï",
                          "username": "git"}))]
    pub_sock.send_multipart(data)
    msg = out_sock.recv_multipart()
    assert msg == data

    # End the process
    proc.terminate()
    proc.wait()
