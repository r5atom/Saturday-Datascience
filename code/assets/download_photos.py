import argparse
import configparser
import sys


# input arguments
parser = argparse.ArgumentParser(description='Download all photos from auction.')
parser.add_argument("-c", "--config_file", type=argparse.FileType('r'),
                    default='../drz-settings.ini', 
                    help='Config file with settings. default: "./drz-settings.ini"')
#TODO CONTINUE HERE maak dit net als auction_urls.py met maar 1 config file
#parser.add_argument("-c", "--config_file", default='./config.ini', help='Config file with settings. default: "./config.ini"')
parser.add_argument("-i", "--input_file", default='./source.csv', help='File with list of urls. default: "./source.csv"')
parser.add_argument("-o", "--output_file", default='./images.csv', help='File with list of image urls. default: "./images.csv"')
parser.add_argument("-d", "--destination_directory", default='./images/', help='Location where to store photos. default: "./images/"')
parser.add_argument("-v", "--verbose", action='store_true', help='Verbose')


# get arguments
args = parser.parse_args()
VERBOSE = args.verbose
settings_fid = args.config_file
source_list = args.input_file
output_file = args.output_file
dest_dir_root = args.destination_directory
dest_dir_root += '/' if not dest_dir_root.endswith('/') else '' # add "/"

import logging_helper
_log_message = lambda fn, msg: logging_helper.log_message(fn, f'{sys.argv[0]} {msg}', verbose=VERBOSE)

# config settings
cfg = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
with settings_fid as fid:
    cfg.read_file(fid)
    
status_file = cfg['FILE_LOCATION']['log_file']

# main
_log_message(status_file, 'Start.')
_log_message(status_file, str(args))
_log_message(status_file, logging_helper.dump_cfg(settings_fid,cfg))

import pandas as pd
import numpy as np
import scrape
import drz
import re
import os

if os.path.exists(output_file):

    # Load images from file
    _log_message(status_file, f'Load images from {output_file}.')
    images = pd.read_csv(output_file, sep=';', index_col=[0, 1])

else:

    _log_message(status_file, f'File {output_file} does not exist. Create from {source_list}')

    # load input
    source = pd.read_csv(source_list, sep=';', index_col=0)
    
    # create empty dataframe
    idx = pd.MultiIndex.from_product(
        iterables=[source.index, range(12)], # 12 images to start with. Too many will be trimmed and too less will be added
        names=[source.index.name, 'counter'])
    images = pd.DataFrame(index=idx, columns=['image_url'], dtype='str', data=None)
    
    # loop over input
    n_images = 0
    for i, lot_url in source.Source.items():
        base_url = re.findall('http.*//.*\.[a-z]+/', lot_url)[0][:-1] # store
    
        # scrape image urls
        image_urls = drz.get_image_urls(scrape.get_tree(lot_url))
    
        # save image urls
        for c, image_url in enumerate(image_urls):
            # check if resolution >1024
            fn, resy, resx = image_url.split('/')[:-4:-1]
            if (int(resx) < 1024) or (int(resy) < 1024):
                new = '/'.join(image_url.split('/')[:-3])
                new += '/'.join(['', '1024', '1024', fn]) # set both to 1024... it works
                image_url = new
            images.loc[(i, c), 'image_url'] = base_url + image_url
        n_images += c+1
        # progress
        _log_message(status_file, f'{c:4.0f} images in {i}. Total of {n_images:4.0f} stored sofar in dataframe ({images.shape[0]:.0f}).')
    
    # trim dataframe
    images.dropna(inplace=True)
    images.sort_index(inplace=True)
    _log_message(status_file, f'Finished: Total of {n_images} stored in dataframe ({images.shape[0]}).')
    
    # add filename
    images['filename'] = images.index.to_frame().apply(lambda x: f'{x[0]}-{x[1]:02.0f}.jpg', axis=1)

    # save
    _log_message(status_file, f'Save image urls to {output_file}')
    images.to_csv(output_file, sep=';')



    
# destination of photos
dest_sub_dir = '/'.join(images.index.get_level_values(0)[0].split('-')[:2]) + '/'
dest_dir = dest_dir_root + dest_sub_dir
if not os.path.exists(dest_dir):
    _log_message(status_file, f'Dir does not exist. Create {dest_dir}')
    os.makedirs(dest_dir)
else:
    _log_message(status_file, f'Destination dir is existing {dest_dir}.')

# save images to disk
for ix, (url, fn) in images.iterrows():
    r = scrape.download_image(url, dest_dir + fn, skip_when_exist=True)
    _log_message(status_file, r)








_log_message(status_file, 'Done.')
