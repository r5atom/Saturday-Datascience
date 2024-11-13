# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown] editable=true slideshow={"slide_type": ""}
# # Download images from the auction results
#
# Use the url from the auction result to download all images from the auction.

# %%
auction_settings_file = '../assets/drz-settings-current.json'

# %%
import re
import json
import pandas as pd
import os

# %% slideshow={"slide_type": ""}
with open(auction_settings_file, 'r') as fid:
    cfg = json.load(fid)

print(cfg['AUCTION'])

OPBOD = cfg['AUCTION']['kind'] == 'opbod'
AUCTION_ID = cfg['AUCTION']['id']
DATE = cfg['AUCTION']['date']
DATA_DIR = cfg['FILE_LOCATION']['data_dir']
IMAGE_DIR = cfg['FILE_LOCATION']['image_dir']
auction_month = DATE[:4] + '-' + DATE[4:6]
if cfg['AUCTION']['kind'] == 'inschrijving':
    month_counter = re.sub('(-)(\d{2})', '\g<1>', AUCTION_ID)[5:8]
    URL = cfg['URL']['inschrijving']
elif cfg['AUCTION']['kind'] == 'opbod':
    month_counter = re.sub('(-)(\d{2})(\d{2})', '-\g<2>', AUCTION_ID)[5:8]
    URL = cfg['URL']['opbod']

VERBOSE = int(cfg['GENERAL']['verbose'])
#SAVE_METHOD = cfg['GENERAL']['save_method']



# %%
print('Use this to copy from raspberry pi to local:\n')
sub = 'opbod/' if OPBOD else ''
remote_dir = f'/home/pi/data/satdatsci-images/{sub}{DATE[:4]}/{month_counter}/'
local_dir = remote_dir.replace('pi', 'tom')
print(f"rsync -avr --dry-run 'pi@rpi4b.local:{remote_dir}' '{local_dir}'")


# %% slideshow={"slide_type": ""}
def download_images_from_lot(lot, path=cfg['FILE_LOCATION']['image_dir'], skip=True):
    '''
    Download .jpg to disk
    '''
    import urllib.request
    import re
    
    urls = lot.Images

    fn_patt = '{}/{}-{}.jpg'.format(path,lot.name,'{:02g}')

    c = 0
    for i,url in enumerate(urls):
        # change url to get larger image
        url = re.sub('1024/768','1024/1024',url)
        # apply format: add counter
        fn = fn_patt.format(i)
        if os.path.isfile(fn) & skip:
            continue
            
        print(url, '->', fn,end='',flush=True)
        urllib.request.urlretrieve(url, fn)
        print('',end='\r')
        
        c+=1
        
    return c # nr of images in this lot



# %% [markdown]
# # Load auction results
#
# (Can also use rdw data here.)

# %% slideshow={"slide_type": ""}
file_name = f'{DATA_DIR}/auctions/results/drz-data-{auction_month}-{month_counter}.pkl'
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
    
if not os.path.isfile(file_name):
    # see if -unparsed- exist
    file_name = file_name.replace('auctions/results', 'auctions/temp-results')
    file_name = file_name.replace('drz-data-', 'drz-data-unparsed-')
    if not os.path.isfile(file_name):
        # see if -unparsed without price- exists
        file_name = file_name.replace('auctions/temp-results', 'auctions/without-price')
        if OPBOD:
            file_name = file_name.replace('-opbod.pkl', '-without-price-opbod.pkl')
        else:
            file_name = file_name.replace('.pkl', '-without-price.pkl')

        if not os.path.isfile(file_name):
            # see if -without price- exists (but not unparsed)
            file_name = file_name.replace('drz-data-unparsed-', 'drz-data-')

print(file_name)
drz = pd.read_pickle(file_name)
print(drz.shape[0], 'lots')
print(drz.N_images.sum(), 'pictures')

# %% [markdown]
# # Download

# %% slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
if OPBOD:
    images_dir = IMAGE_DIR + '/opbod/' + DATE[:4] + os.path.sep + month_counter
else:
    images_dir = IMAGE_DIR + os.path.sep + DATE[:4] + os.path.sep + month_counter
    
if not os.path.exists(images_dir):
    print(f'Dir does not exist. Create [{images_dir}]')
    os.makedirs(images_dir)
    
# start_idx = pd.np.where(drz.index == '2019-5-8332')[0][0]
start_idx = 0
npic = drz.iloc[start_idx:,:].apply(
    lambda lot:download_images_from_lot(lot, path=images_dir)
    , axis='columns')

print('saved')
print(npic.shape[0], 'lots')
print(npic.sum(), 'pictures')
assert npic.equals(drz.N_images) | (npic.sum() == 0)


# %% [markdown] editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# # Next: upload to cloud backup
#
# When images are stored locally it is advised to back them up in the cloud.
