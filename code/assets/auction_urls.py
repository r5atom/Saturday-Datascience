import argparse
import configparser
import pandas as pd
import sys
from time import sleep
import drz

# input arguments
parser = argparse.ArgumentParser(description='Get all urls from auction.')
parser.add_argument("auction_id", type=str, metavar='AUCTION_ID', 
                    help='Auction id. The "name" of the auction. e.g. 2023-0023')
parser.add_argument("auction_kind", type=str, metavar='O|I', choices=['O', 'I'], default='I',
                    help='Kind of auction. O: Opbod (default), I: Inschrijving)')
parser.add_argument("-p", "--pause", default='6hours', help='PAUSE: pandas Timedelta compatible string. e.g. "1sec". default "6hours"')
parser.add_argument("-c", "--config_file", type=argparse.FileType('r'),
                    default='../drz-settings.ini',
                    help='Config file with settings. default: "./drz-settings.ini"')
parser.add_argument("-o", "--output_file", default='./source.csv', help='File with list of urls. default: "./source.csv"')
parser.add_argument("-v", "--verbose", action='store_true', help='Verbose')

# get arguments
args = parser.parse_args()
auction_code = args.auction_id
OPBOD = args.auction_kind == 'O'
VERBOSE = args.verbose
wait = args.pause
settings_fid = args.config_file
output_file = args.output_file

# helper function
import logging_helper
_log_message = lambda fn, msg: logging_helper.log_message(fn, f'{sys.argv[0]} {msg}', verbose=VERBOSE)

# config settings
cfg = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
with settings_fid as fid:
    cfg.read_file(fid)
    
status_file = cfg['FILE_LOCATION']['log_file']
max_wait = cfg['GENERAL']['max_wait_between_auctions']
end_time = pd.Timestamp.now() + pd.Timedelta(max_wait)

# main
print(status_file)
_log_message(status_file, 'Start.')
_log_message(status_file, str(args))
_log_message(status_file, logging_helper.dump_cfg(settings_fid.name, cfg))

# get all urls

DO = True; c=0
while DO:
    try:
        source = drz.all_pages(auction_code, OPBOD, VERBOSE)
        DO = False
    except ConnectionError as ex:
        if not ex.args[0].startswith('status 404. Page <http'):
            _log_message(status_file, ex.args[0])
            raise
        # action does not exist
        source = None
        DO = end_time > pd.Timestamp.now()
        _log_message(status_file, f'{ex.args[0]}. No results (yet) at try {c}. Wait {wait} and try again till {end_time}.')
        sleep(pd.Timedelta(wait).seconds)
        c+=1

# Urls available?
if source is None:
    # Error if empty
    msg =  f'[ERROR] No results. Tried till {end_time}'
    _log_message(status_file, msg)
    raise RuntimeError(msg)

# Write to table
source.to_csv(output_file, sep=';')
_log_message(status_file, f'{output_file} written')







_log_message(status_file, 'Done.')
