#!/usr/bin/env python3
# coding: utf-8

"""
Program reads input file line by line, matching PoS tags. Each is replaced by an LT tag.
LT tags are provided by function srptagging.get_tag -
"""

import argparse
import logging
import os
import sys

import srptagging

_args_ = None
_logger_ = None
_out_file_ = None
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
DIST_TAGS = []

def parse_args():
    parser = argparse.ArgumentParser(description='Changes PoS tags to LT tags in file containing Serbian word corpus.')
    parser.add_argument('-d', '--debug',      action ='store_true', default=False)
    parser.add_argument('-i', '--input-file', default=None)
    parser.add_argument('-n', '--first-n-lines', default=0, type=int)
    parser.add_argument('-o', '--output-dir', default='/tmp')

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
    if not os.path.exists(_args_.input_file):
        _logger_.error(f"Unable to open file '{_args_.input_file}', aborting ...")
        sys.exit(1)


def init():
    global _logger_
    logging.basicConfig(format=LOG_FORMAT)
    _logger_ = logging.getLogger("pos2lt")


def open_out_file():
    global _out_file_
    # Create output file by concatenating base output directory with input file name
    out = os.path.join(_args_.output_dir, os.path.basename(_args_.input_file))
    _logger_.info(f"Writing output to file '{out}' ...")
    try:
        _out_file_ = open(out, "wb")
    except OSError:
        _logger_.error(f"Unable to open file '{out}' for writing, aborting ...")
        sys.exit(1)


def close_out_file():
    _out_file_.close()


# Checks for specially defined word types - i.e. reflexive verbs
def check_word_type(lemma, postag, lttag):
    return lttag

def count_tags(lttag):
    global DIST_TAGS
    taglist = lttag.split(':')
    for tag in taglist:
        if tag not in DIST_TAGS:
            DIST_TAGS.append(tag)

# Parse input file
def parse_file():
    cnt = 0
    _logger_.info(f"Started processing input file '{_args_.input_file}' ...")

    with open(_args_.input_file) as f:
        for line in f:
            # Remove end of line
            line = line.strip()
            cnt += 1
            # Get PoS tag
            lparts = line.split('\t')
            # Check if there is a tag
            if len(lparts[2]) > 0:
                try:
                    lttag = srptagging.get_tag(lparts[2], ':')
                    if lttag.find('ERROR') != -1:
                        _logger_.error(f"{lttag} for wordform {lparts[0]}, lemma {lparts[1]}")
                        continue
                    count_tags(lttag)
                except KeyError:
                    _logger_.error(
                        f"Getting LT tag: wordform {lparts[0]}, lemma {lparts[1]}, tag {lparts[2]}"
                    )

                    continue
                # Handle special cases and word types
                newltag = check_word_type(lparts[1], lparts[2], lttag)
                if lttag not in (None, ''):
                    _out_file_.write(f"{lparts[0]}\t{lparts[1]}\t{newltag}\n".encode('utf-8'))
                else:
                    _logger_.warn("For PoS tag '{}' no LT tag found. Line: '{}'".format(line))
            else:
                _logger_.warn(f"No PoS tag found on line: {line}")
            if cnt > _args_.first_n_lines > 0:
                break
        f.close()
    _logger_.info(
        f"Finished processing input file '{_args_.input_file}': total {cnt} lines."
    )

    _logger_.info(f"Found following distinctive LT tags: {sorted(DIST_TAGS)}")


if __name__ == "__main__":
    init()
    parse_args()
    open_out_file()
    parse_file()
    close_out_file()
