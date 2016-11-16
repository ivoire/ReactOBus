#!/usr/bin/python3
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

import argparse
import itertools
import logging
import signal
import sys
import yaml

from ReactOBus.core import Core


FORMAT = "%(asctime)-15s %(levelname)7s %(name)s %(message)s"
LOG = logging.getLogger("ROB")


def configure_logger(log_file, level):
    if level == "ERROR":
        LOG.setLevel(logging.ERROR)
    elif level == "WARN":
        LOG.setLevel(logging.WARN)
    elif level == "INFO":
        LOG.setLevel(logging.INFO)
    else:
        LOG.setLevel(logging.DEBUG)

    if log_file == "-":
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(log_file, "a")
    handler.setFormatter(logging.Formatter(FORMAT))
    LOG.addHandler(handler)


def configure_pipeline(conffile):
    from ReactOBus.inputs import Input
    # TODO: only import if needed
    from ReactOBus.outputs import Output

    LOG.info("Creating the pipeline")
    with open(conffile) as f_in:
        conf = yaml.load(f_in)

    # Parse inputs
    LOG.debug("Inputs:")
    ins = []
    outs = []
    for i in conf["inputs"]:
        LOG.debug("- %s (%s)", i["class"], i["name"])
        new_in = Input.select(i["class"], i["name"],
                              i.get("options", {}),
                              conf["core"]["inbound"])
        ins.append(new_in)

    LOG.debug("Outputs:")
    for o in conf.get("outputs", []):
        LOG.debug("- %s (%s)", o["class"], o["name"])
        new_out = Output.select(o["class"], o["name"],
                                o.get("options", {}),
                                conf["core"]["outbound"])
        outs.append(new_out)

    core = [Core(conf["core"]["inbound"], conf["core"]["outbound"])]
    if conf.get("reactor", None) is not None:
        # Import the Reactor only when used
        from ReactOBus.reactor import Reactor
        core.append(Reactor(conf["reactor"], conf["core"]["outbound"]))

    if conf.get("db", None) is not None:
        # Import DB here (hence also SQLAlchemy) only when needed
        from ReactOBus.db import DB
        core.append(DB(conf["db"], conf["core"]["outbound"]))

    return (core, ins, outs)


def start_pipeline(stages):
    LOG.info("Starting the pipeline")
    # Ignore the signals in the sub-processes. The main process will take care
    # of the propagation

    default_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Start the stages
    for stage in itertools.chain(*stages):
        stage.start()

    # Restaure the default signal handler
    signal.signal(signal.SIGINT, default_handler)


def main():
    # Parse the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="/etc/reactobus.yaml",
                        help="ReactOBus configuration")
    loggrp = parser.add_argument_group('Logging')
    loggrp.add_argument("-l", "--level", default="INFO", type=str,
                        choices=["DEBUG", "ERROR", "INFO", "WARN"],
                        help="Log level (DEBUG, ERROR, INFO, WARN), default to INFO")
    loggrp.add_argument("--log-file", default="-", type=str,
                        help="Log file, use '-' for stdout")

    options = parser.parse_args()

    # Configure everything
    configure_logger(options.log_file, options.level)
    stages = configure_pipeline(options.config)

    # Setup and start the pipeline
    start_pipeline(stages)

    # Wait for a signal and then quit
    LOG.info("Waiting for a signal")
    try:
        signal.pause()
    except KeyboardInterrupt:
        pass

    LOG.info("Signal received, leaving")

    # Wait for all threads
    for t in itertools.chain(*stages):
        t.terminate()
        t.join()

    LOG.info("Leaving")


if __name__ == '__main__':
    main()
