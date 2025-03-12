# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown] editable=true slideshow={"slide_type": ""}
# # NHTSA vpic
#
#
# Get additional data from The National Highway Traffic Safety Administration (NHTSA) based on VIN. 
#
# Product Information Catalog and Vehicle Listing (vPIC)  
# https://vpic.nhtsa.dot.gov/api/
#

# %% [markdown] slideshow={"slide_type": ""}
# ### User variables
#

# %% slideshow={"slide_type": ""}
import sys
import re
import json
from IPython.display import display

# %% editable=true slideshow={"slide_type": ""}
with open('../assets/drz-settings-current.json', 'r') as fid:
    cfg = json.load(fid)

OPBOD = cfg['AUCTION']['kind'] == 'opbod'
AUCTION_ID = cfg['AUCTION']['id']
DATE = cfg['AUCTION']['date']
DATA_DIR = cfg['FILE_LOCATION']['data_dir']
auction_month = DATE[:4] + '-' + DATE[4:6]
if cfg['AUCTION']['kind'] == 'inschrijving':
    month_counter = re.sub('(-)(\d{2})', '\g<1>', AUCTION_ID)[5:8]
elif cfg['AUCTION']['kind'] == 'opbod':
    month_counter = re.sub('(-)(\d{2})(\d{2})', '-\g<2>', AUCTION_ID)[5:8]

sys.path.insert(0, cfg['FILE_LOCATION']['code_dir'])

QUICK_MERGE = False
SKIPSAVE = False
OVIDATA = True
VERBOSE = 1

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### Modules and functions

# %%
import pandas as pd
import numpy as np
import re 
import os
# to keep api key hidden import this from sub dir
import assets.hidden_api_keys as hidden_api_keys
from rdw_info import *

# %% [markdown]
# ### Load auction results

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
file_name = f'{DATA_DIR}/auctions/results/drz-data-{auction_month}-{month_counter}.pkl'
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
if not os.path.isfile(file_name):
    # see if -without price- exists
    NO_PRICE = True
    if NO_PRICE:
        file_name = file_name.replace('auctions/results', 'auctions/without-price')
        file_name = file_name.replace('.pkl', '-without-price.pkl')
    if OPBOD:
        file_name = file_name.replace('-opbod-without-price.pkl', '-without-price-opbod.pkl')
#     else:
#         file_name = file_name.replace('.pkl', '-without-price.pkl')
else:
    NO_PRICE = False


print(file_name)
drz = pd.read_pickle(file_name)

# %%
# Load registrations
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-reg/rdw-reg-full-0-data-{auction_month}-{month_counter}{suffix}.pkl'
rdw_per_reg = pd.read_pickle(file_name)
rdw_per_reg.index.name = 'kenteken';

# %% [markdown]
# # Collect data from VINs

# %% editable=true slideshow={"slide_type": ""}
from vin_lookup import Nhtsa_batch

# %% editable=true slideshow={"slide_type": ""}
# empty dictionary
nhtsa_per_vin = dict()

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
key = 'vpic'
df_ =  drz.loc[:, ['Vin', 'Mfyear']].copy().replace({'': np.nan, 'onbekend': np.nan}) # copy from drz

# borrow mfyear from rdw info
rdw_mfy = pd.merge(  left = rdw_per_reg['registrations'].reset_index(),
                     right = rdw_per_reg['gekentekende_voertuigen'].datum_eerste_toelating.reset_index(),
                     how='left',
                     right_on='kenteken',
                     left_on='kenteken'
                    ).loc[:, ['lot_index', 'datum_eerste_toelating']].set_index('lot_index')
df_ =  pd.concat([df_, (rdw_mfy // 10000).astype(pd.Int16Dtype())], axis=1)
df_.update(df_.loc[:, ['Mfyear', 'datum_eerste_toelating']].bfill(axis=1))
df_.rename(columns={'Vin': 'VIN', 'Mfyear': 'MFY'}, inplace=True)
nhtsa_per_vin[key] = df_.loc[:, ['VIN', 'MFY']]

# lookup vins in batches
Batch = Nhtsa_batch(nhtsa_per_vin[key].iloc[:,:2].dropna(subset='VIN'), 
                    data_dict_fn = f"{cfg['FILE_LOCATION']['code_dir']}/assets/nhtsa-data-dict.csv",
                    verbose=VERBOSE)
Batch.full_parse()

# store in dict
out = Batch.data.copy()
out.loc[:, 'TimeStamp'] = pd.Timestamp.now().strftime('%Y%m%d')
nhtsa_per_vin[key] = pd.concat([
    nhtsa_per_vin[key],
    out.drop(columns=out.columns[out.columns.str.startswith('system') | out.columns.str.startswith('internal')])
], axis=1)

if VERBOSE > 1:
    display(nhtsa_per_vin[key])
else:
    print('\n'.join(nhtsa_per_vin.keys()))

# %%
# Merge with input and potentential other sources
nhtsa_per_vin['vpic'].index.name = 'lot_index'
Batch.data.index.name = 'lot_index'
df_vins = pd.concat([
    nhtsa_per_vin['vpic'].loc[:, ['VIN', 'MFY']], 
    Batch.data
], axis = 1)
# add timestamp
df_vins.loc[:, 'TimeStamp'] = pd.Timestamp.now().strftime('%Y%m%d')
# Set index to vin/mfy
df_vins = df_vins.reset_index().set_index(['VIN', 'MFY'])

# %%
out = df_vins.copy()
out.shape

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# Save
file_name = f'{DATA_DIR}/auctions/enriched-results/nhtsa-vpic/nhtsa-vpic-0-data-{auction_month}-{month_counter}.pkl'

if NO_PRICE:
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
    
if (SKIPSAVE==False) and (not(os.path.isfile(file_name))):
    print(file_name)
    out.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')
