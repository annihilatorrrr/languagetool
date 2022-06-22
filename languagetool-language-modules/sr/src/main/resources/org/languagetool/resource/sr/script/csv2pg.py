#!/usr/bin/env python3
# coding: utf-8

"""
Program reads input file line by line, parsing line conforming to Serbian word corpus entries.
Existence of words in each line is tested against database. If word is not found, it is inserted.
"""

import argparse
import configparser
import logging
import os
import psycopg2
import sys

# Custom modules section
import srptagging

_args_ = None
_logger_ = None
_out_file_ = None
_config_ = None
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(message)s'

def parse_args():
    parser = argparse.ArgumentParser(description='Checks words against PostgreSQL database containing Serbian word corpus.')
    parser.add_argument('-c', '--config-file',   default=None)
    parser.add_argument('-d', '--debug',         action ='store_true', default=False)
    parser.add_argument('-i', '--input-file',    default=None)
    parser.add_argument('-n', '--first-n-lines', default=0, type=int)
    parser.add_argument('-o', '--output-dir',    default='/tmp')

    global _args_, _logger_
    _args_ = parser.parse_args()
    if _args_.debug:
        _logger_.setLevel( logging.DEBUG )
    else:
        _logger_.setLevel( logging.INFO )
    _logger_.debug(f"Command-line arguments: {_args_}")
    if not _args_.input_file:
        _logger_.error("Input file (-i) was not specified, aborting ...")
        sys.exit(1)
    if not os.path.exists(_args_.input_file):
        _logger_.error(
            f"Unable to open input file '{_args_.input_file}', aborting ..."
        )

        sys.exit(1)
    if not _args_.config_file:
        _logger_.error("Configuration file (-c) was not specified, aborting ...")
        sys.exit(2)


def init():
    global _logger_, _config_
    logging.basicConfig(format=LOG_FORMAT)
    _logger_ = logging.getLogger("csv2pg")

def read_config():
    global _config_
    # Load configuration file
    if not os.path.exists(_args_.config_file):
        _logger_.error(
            f"Configuration file '{_args_.config_file}' does not exist, aborting ..."
        )

        sys.exit(2)
    _config_ = configparser.ConfigParser()
    _config_.read( _args_.config_file )


def open_out_file():
    global _out_file_
    # Create output file by concatenating base output directory with input file name
    out = os.path.join(_args_.output_dir, os.path.basename(_args_.input_file))
    _logger_.info(f"Writing output to file '{out}' ...")
    try:
        _out_file_ = open(out, "wb")
    except OSError:
        _logger_.error(f"Unable to open output file '{out}' for writing, aborting ...")
        sys.exit(1)

def open_database():
    global _conn_, _cursor_
    _logger_.debug(
        f"Opening database '{_config_['DB']['database']}' as user '{_config_['DB']['username']}' ..."
    )

    _conn_ = psycopg2.connect(
        f"dbname={_config_['DB']['database']} user={_config_['DB']['username']}"
    )

    _cursor_ = _conn_.cursor()


def close_out_file():
    _logger_.debug("Closing output file ...")
    _out_file_.close()


# Returns TRUE if line is filtered, FALSE otherwise
def is_filtered(line):
    return (
        line.find('W') != -1
        or line.find('w') != -1
        or line.find('Y') != -1
        or line.find('y') != -1
        or line.find('X') != -1
        or line.find('x') != -1
    )


def close_database():
    _logger_.debug("Closing database ...")
    _cursor_.close()
    _conn_.commit()
    _conn_.close()


# Checks for specially defined word types - i.e. reflexive verbs
def check_word_in_db(wordform, lemma, msd):
    _cursor_.execute(_config_['DB']['word_exists'], (wordform, lemma, f'{msd}%'))
    ret = _cursor_.fetchone()[0] # Take first element of resulting tuple
    _logger_.debug(
        f"Checked existence of (wordform, lemma, msd) = ({wordform}, {lemma}, {msd}%), got: {ret}"
    )

    return ret


def insert_word_in_db(wordform, lemma, tag, frequency):
    # _cursor_.execute(_config_['DB']['word_insert'], (wordform, lemma, tag, frequency,) )
    #_conn_.commit()
    _logger_.info(f"Inserted: ({wordform}, {lemma}, {tag}, {frequency})")


# Parse input file
def parse_file():
    cnt = 0
    _logger_.info(f"Started processing input file '{_args_.input_file}' ...")

    with open(_args_.input_file) as f:
        for line in f:
            # Remove end of line
            line = line.strip()
            cnt += 1
            # Get words, tags etc.
            lparts = line.split('\t')
            # Check if there is a tag
            if len(lparts) == 4:
                if is_filtered(line):
                    # Line should be skipped, write to output file
                    _logger_.debug(f"Skipping filtered line '{line}' ...")
                    _out_file_.write(line.encode('utf-8'))
                elif not check_word_in_db(lparts[0], lparts[1], lparts[2]):
                    # Insert everything in DB
                    insert_word_in_db(lparts[0], lparts[1], lparts[2], lparts[3])
            else:
                _logger_.warn(f"Non-compliant line, skipping: '{lparts}' ...")
            if cnt > _args_.first_n_lines > 0:
                break
        f.close()
    _logger_.info(
        f"Finished processing input file '{_args_.input_file}': total {cnt} lines."
    )

    _logger_.info("Skipped lines are in output file.")


if __name__ == "__main__":
    init()
    parse_args()
    read_config()
    open_out_file()
    open_database()
    parse_file()
    close_out_file()
    close_database()
