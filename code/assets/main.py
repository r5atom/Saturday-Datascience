import argparse
import configparser
import pandas as pd
import sys
from time import sleep
from datetime import datetime

# input arguments
parser = argparse.ArgumentParser(description='Get price from all lots.')
#parser.add_argument("-p", "--pause", default='6hours', help='PAUSE: pandas Timedelta compatible string. e.g. "1sec". default "6hours"')
parser.add_argument("-c", "--config_file", type=argparse.FileType('r'),
                    default='../drz-settings.ini', 
                    help='Config file with settings. default: "./drz-settings.ini"')
parser.add_argument("-i", "--input_file", default='./source.csv', help='File with list of urls. default: "./source.csv"')
parser.add_argument("-v", "--verbose", action='store_true', help='Verbose')

# get arguments
args = parser.parse_args()
VERBOSE = args.verbose
settings_fid = args.config_file
source_list = args.input_file

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
_log_message(status_file, 'Start.')
_log_message(status_file, str(args))
_log_message(status_file, logging_helper.dump_cfg(settings_fid,cfg))

import scrape
import drz

source = pd.read_csv(source_list, sep=';', index_col=0)
source = source.Source # make type series, not dataframe

price = pd.DataFrame(index=pd.Index(source.index, name='lot'), columns = ['price', 'ts'], data='')
price.ts = str(datetime.now())
price = price.reset_index().set_index(['ts', 'lot'])

DO = True
while DO:
    try:
        for lot, url in source.items():
            prev_price = price.reset_index().set_index('lot').loc[[lot], :].sort_values(by='ts', ascending=True).price.values[-1]
            cur_price = drz.get_price(scrape.get_tree(url))
            if prev_price == cur_price:
                # same output, no need to log
                continue

            # log price (or other output)
            ts = str(datetime.now())
            idx = pd.MultiIndex.from_arrays([[ts], [lot]])[0]
            price.loc[idx, 'price'] = cur_price

            _log_message(status_file, f'{lot} price change on {ts} from <{prev_price}> to <{cur_price}>')
            
            
        DO = True
        
    except KeyboardInterrupt:
        _log_message(status_file, 'Cancel.')
        break
        
    # price with last ts is not filled
    todo = price.reset_index().sort_values(by='ts', ascending=False).groupby('lot').price.first().apply(
        lambda x: (len(x) == 0) or x.startswith('closed') or (x == 'empty') or x.startswith('running') 
    )
    _log_message(status_file, f'{sum(todo)}/{source.shape[0]} still without price. Try till {end_time}')
    DO = (todo.any())
    if DO and (end_time < pd.Timestamp.now()):
        msg =  f'[ERROR] No results. Tried till {end_time}'
        _log_message(status_file, msg)
        raise RuntimeError(msg)

# TODO: SAVE dataframe price

# ready
_log_message(status_file, 'Done.')
