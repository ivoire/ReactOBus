#!/usr/bin/python3

import argparse


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

if __name__ == '__main__':
    main()
