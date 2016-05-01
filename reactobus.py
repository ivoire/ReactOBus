#!/usr/bin/python3

import argparse
import itertools
import logging
import sys
import yaml


FORMAT = "%(asctime)-15s %(levelname)s %(message)s"
LOG = logging.getLogger("ReactOBus")


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
    from lib import inputs
    from lib import outputs

    LOG.info("Creating the pipeline")
    with open(conffile) as f_in:
        conf = yaml.load(f_in)

    # Parse inputs
    LOG.debug("Inputs:")
    ins = []
    outs = []
    for i in conf["inputs"]:
        LOG.debug("- %s (%s)", i["class"], i.get("name", ""))
        ins.append(inputs.Input.select(i["class"], i.get("options", {})))

    LOG.debug("Outputs:")
    for o in conf["outputs"]:
        LOG.debug("- %s (%s)", o["class"], o.get("name", ""))
        outs.append(outputs.Output.select(o["class"], o.get("options", {})))

    return (ins, outs)


def start_pipeline(inputs, outputs):
    LOG.info("Setting-up the pipeline")
    for i in inputs:
        i.start()
    for o in outputs:
        o.start()


def main():
    # Parse the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf", default="/etc/reactobus.yaml",
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
    (inputs, outputs) = configure_pipeline(options.conf)

    # Setup and start the pipeline
    start_pipeline(inputs, outputs)

    # TODO: start the core threads
    # TODO: handle Ctrl+C

    # Wait for all threads
    for t in itertools.chain(inputs, outputs):
        t.join()


if __name__ == '__main__':
    main()
