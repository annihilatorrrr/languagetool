#!/usr/bin/env python3
# coding: utf-8

"""
Program reads input file line by line, matching PoS tags. They are written
to the output file in order of appearance. Each tag is written to output
file only once.
"""

import argparse
import logging
import re
import os
import sys

_args_ = None
_logger_ = None
_out_file_ = None
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
# Types of regex to match input, selectable from command line
REGEX_TYPE = {
    "lex" : "^([!\"\'\(\),\-\.:;\?]|[a-zčćžšđâîôﬂǌüA-ZČĆŽŠĐ0-9_\-]+)\s+([!\"\'\(\),\-\.:;\?]|[a-zčćžšđâîôﬂǌüA-ZČĆŽŠĐ0-9_\-]+)\s+([a-zA-Z0-9\-]+)*",
    "wac" : "^([a-zčćžšđâîôﬂǌüA-ZČĆŽŠĐ0-9_\-]+)\s+([!\"\'\(\),\-\.:;\?]|[a-zčćžšđâîôﬂǌüA-ZČĆŽŠĐ0-9_\-]+)\s+([!\"\'\(\),\-\.:;\?]|[a-zčćžšđâîôﬂǌüA-ZČĆŽŠĐ0-9_\-]+)\s+([a-zA-Z0-9\-]+)*"
}


def parse_args():
    parser = argparse.ArgumentParser(description='Processes file containing Serbian word corpus.')
    parser.add_argument('-b', '--base-dir',   default='/tmp')
    parser.add_argument('-d', '--debug',      action ='store_true', default=False)
    parser.add_argument('-i', '--input-file', default=None)
    parser.add_argument('-n', '--first-n-lines', default=0, type=int)
    parser.add_argument('-o', '--output-file', default='out.txt')
    parser.add_argument('-r', '--regex',      default=None)

    global _args_, _logger_
    _args_ = parser.parse_args()
    if _args_.debug:
        _logger_.setLevel( logging.DEBUG )
    else:
        _logger_.setLevel( logging.INFO )
    _logger_.debug(f"Command-line arguments: {_args_}")
    if not _args_.input_file:
        _logger_.error("Input file was not specified, aborting ...")
        sys.exit(1)
    if not _args_.regex:
        sys.exit(1)
    if not os.path.exists(_args_.input_file):
        _logger_.error(f"Unable to open file '{_args_.input_file}', aborting ...")
        sys.exit(1)


def init():
    global _logger_
    logging.basicConfig(format=LOG_FORMAT)
    _logger_ = logging.getLogger("lex2lt")


def open_out_file():
    global _out_file_
    _out_file_ = open(_args_.output_file, "w")


def close_out_file():
    _out_file_.close()


# Parse input file
def parse_file():
    cnt = 0
    matchcnt = 0
    tags = []
    if _args_.regex in REGEX_TYPE:
        pattern = re.compile(REGEX_TYPE[ _args_.regex ])
    else:
        _logger_.error(
            f"Regular expression of type '{_args_.regex}' does not exist in configuration, aborting ..."
        )

        sys.exit(1)
    _logger_.info(f"Started processing input file '{_args_.input_file}' ...")

    with open(_args_.input_file) as f:
        for line in f:
            # Remove end of line
            line = line.strip()
            cnt += 1
            if match := pattern.match(line):
                matchcnt += 1
                _logger_.debug(f"Matched groups: {match.groups()}")
                if len(match.groups()) < 4:
                    posgr = match.group(3)
                elif len(match.groups()) < 5:
                    posgr = match.group(4)
                _logger_.debug(f'posgr={posgr}')

                if posgr not in tags:
                    tags.append( posgr )
                    _out_file_.write(f"{posgr}\n")

            else:
                _logger_.warn(f"Unmatched line: {line}")
            if cnt > _args_.first_n_lines > 0:
                break
        f.close()
    _logger_.info(
        f"Finished processing input file '{_args_.input_file}': total {cnt} lines, {matchcnt} matching lines."
    )


if __name__ == "__main__":
    init()
    parse_args()
    open_out_file()
    parse_file()
    close_out_file()
