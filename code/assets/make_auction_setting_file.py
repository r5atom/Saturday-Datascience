#!/bin/python3

import argparse
import configparser
import sys
import os
import re
import json
import logging_helper

sys.path.insert(0, f'polling/')

# input arguments
parser = argparse.ArgumentParser(
    prog='make_auction_settings_file',
    description='Generate a .json file based on config file elsewhere and input arguments of this script. The .json file can be used to serve as an settings file for the analyses.',

)
parser.add_argument("auction_id", type=str, metavar='AUCTION_ID', 
                    help='Auction id. The "name" of the auction. e.g. 2023-0023')
parser.add_argument("auction_kind", type=str, metavar='O|I', choices=['O', 'I'], default='I',
                    help='Kind of auction. O: Opbod (default), I: Inschrijving)')
parser.add_argument("auction_date", type=str, metavar='AUCTION_DATE', 
                    help='Auction date. Formatted as YYYYMM(DD). e.g. 20231225')
parser.add_argument("-v", "--verbose", action='store_true',
                    help='Verbose')
parser.add_argument("-c", "--config_file", type=argparse.FileType('r'),
                    default='./code/assets/drz-settings-general.ini', 
                    help='Config file with settings. default: "./code/assets/drz-settings-general.ini"')
parser.add_argument("-s", "--current_auction_settings", type=argparse.FileType('w+'),
                    default='./code/assets/drz-settings-current.json', 
                    help='Output file with settings of current file. default: "./code/assets/drz-settings-current.json"')

# get arguments
args = parser.parse_args()
VERBOSE = args.verbose
settings_fid = args.config_file
out_fid = args.current_auction_settings
if args.auction_kind == 'O':
    kind = 'opbod'
elif args.auction_kind == 'I':
    kind = 'inschrijving'
else:
    raise NotImplementedError


_log_message = lambda fn, msg: logging_helper.log_message(fn, f'{sys.argv[0]} {msg}', verbose=VERBOSE)

# config settings
cfg = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
with settings_fid as fid:
    cfg.read_file(fid)

status_file = cfg['FILE_LOCATION']['log_file']

# main
_log_message(status_file, 'Start.')
_log_message(status_file, str(args))
_log_message(status_file, logging_helper.dump_cfg(settings_fid.name, cfg))

# Replace config text elements
#
# first element: "<tag to be replaced>"
# the first element should exist as input argument to this script
# second element (two parts): "[SECTION IN INI FILE]", "field of section": <tag> 
# second part of second element contains the to be replaced tag.
tags = [
    ('foo', 'bar'), # does not exist as input. Will be skipped
    ('auction_id', ('URL', f'{kind}')),
    ('auction_id', ('URL.data', 'veilingen')),
]
# Replace
for tag, fld in tags:
    if tag not in args:
        continue
    val = vars(args)[tag] # value from input this script
    sect, key = fld 
    cfg[sect][key] = cfg[sect][key].replace(f'<{tag}>', val)

# store arguments
cfg.add_section('AUCTION')
cfg.set('AUCTION', 'kind', kind)
cfg.set('AUCTION', 'id', args.auction_id)
cfg.set('AUCTION', 'date', args.auction_date)
cfg.set('FILE_LOCATION', 'auction_settings_file', os.path.realpath(out_fid.name))


def as_dict(config):
    """
    Converts a ConfigParser object into a dictionary.

    The resulting dictionary has sections as keys which point to a dict of the
    sections options as key => value pairs.
    """
    the_dict = {}
    for section in config.sections():
        the_dict[section] = {}
        for key, val in config.items(section):
            the_dict[section][key] = val
    return the_dict

with out_fid as fid:
    fid.write(json.dumps((as_dict(cfg))))

print(as_dict(cfg))
