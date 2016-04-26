#!/usr/bin/python3

import argparse
import logging
import sys

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

    # Configure the logger
    configure_logger(options.log_file, options.level)

    LOG.error("une erreur")
    LOG.warning("un warning")
    LOG.info("une info")
    LOG.debug("une ligne de debug")


if __name__ == '__main__':
    main()
