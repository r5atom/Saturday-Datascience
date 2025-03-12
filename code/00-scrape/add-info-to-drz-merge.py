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
# # Merge additional data
#
# Now we have a couple of dataset that can be merged.
#
# `rdw_per_reg` dictionary  
# `rdw_per_confcode` combined in another dictionary `full_codes`  
# `rdw_ovi` a single dataframe  
# `nhtsa_per_vin` has only one field and is combined in dataframe `df_vins`  
#
#
# 1. Merge dataframes from `rdw_per_reg` with primary key `kenteken`
# 2. 
#     1) Add conformity codes from `rdw_per_confcode`
#     2) Add basic conformity info from `rdw_per_confcode.eeg_voertuigtypegoedkeuring`
# 3. Merge all conformity code information from other apis `full_codes`
# 4. Merge with OVI
# 5. Merge with vpic (nhtsa)
# 6. Merge with auction results
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

# %%
# Load registrations
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-reg/rdw-reg-full-0-data-{auction_month}-{month_counter}{suffix}.pkl'
rdw_per_reg = pd.read_pickle(file_name)
rdw_per_reg.index.name = 'kenteken';
print(file_name)

# %%
# Load registrations with conformity codes
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-reg/rdw-reg-conf-0-data-{auction_month}-{month_counter}{suffix}.pkl'
rdw_per_reg_conf = pd.read_pickle(file_name)
rdw_per_reg_conf.index.name = 'kenteken';
print(file_name)

# %%
# Load conformity codes
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-conf/rdw-conf-0-data-{auction_month}-{month_counter}{suffix}.pkl'
rdw_per_confcode = pd.read_pickle(file_name)
print(file_name)

# %%
# Load revoke dates of conformity codes
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-conf/rdw-conf-revoke-0-data-{auction_month}-{month_counter}{suffix}.pkl'
rdw_per_confcode_revoke = pd.read_pickle(file_name)
print(file_name)

# %%
# Load ovi
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-ovi/rdw-ovi-0-data-{auction_month}-{month_counter}{suffix}.pkl'
rdw_ovi = pd.read_pickle(file_name)
print(file_name)

# %%
# Load nhtsa
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/enriched-results/nhtsa-vpic/nhtsa-vpic-0-data-{auction_month}-{month_counter}{suffix}.pkl'
nhtsa_per_vin = pd.read_pickle(file_name)
print(file_name)

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# load drz auction results
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/results/drz-data-{auction_month}-{month_counter}{suffix}.pkl'
drz = pd.read_pickle(file_name)
print(file_name)

# %% [markdown]
# # Merge datasets

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# Merge first set
# rich = pd.concat(rdw_per_reg, axis=1)
# rich = pd.concat([rich], keys=['rdw'], axis=1)
rich = pd.concat([rdw_per_reg], keys=['rdw'], axis=1)
rich.index.name='kenteken'
print(f'{rich.shape[1]} columns {rich.shape[0]} {rich.index.name} ')

# Add conformity_codes
codes = rdw_per_reg_conf.copy()
codes = pd.concat([codes], keys=['conformity_codes'], axis=1)
codes = pd.concat([codes], keys=['rdw'], axis=1)
rich = rich.merge(
    codes, # add level
    how='outer',
    left_index = True,
    right_index = True,
)
print(f'{rich.shape[1]} columns {rich.shape[0]} {rich.index.name}')

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# Add data with one level EU keys
codes = rdw_per_confcode_revoke.reset_index()
# add levels to dataframe
codes = pd.concat([codes], keys=['intrekking_typegoedkeuring'], axis=1)
codes = pd.concat([codes], keys=['rdw'], axis=1)
if codes.shape[0] > 0:
    rich = rich.reset_index().merge(
        codes, 
        how='outer',
        left_on = [('rdw', 'conformity_codes', 'typegoedkeuringsnummer')],
        right_on = [('rdw', 'intrekking_typegoedkeuring', 'typegoedkeuringsnummer')],
    ).set_index('kenteken')
else:
    rich = rich.reset_index().set_index('kenteken')
print(f'{rich.shape[1]} columns {rich.shape[0]} {rich.index.name}')

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# Add full_codes
# codes = pd.concat(full_codes, axis=1)#.drop(columns='conformity_codes')
codes = rdw_per_confcode.copy()
codes = pd.concat([codes], keys=['rdw'], axis=1)
# rename index names to match existing
existing_idx_names = [{
    'typegoedkeuringsnummer': 'typegoedkeuringsnummer',
    'codevarianttgk': 'eeg_variantcode',
    'codeuitvoeringtgk': 'eeg_uitvoeringscode',
    'volgnummerrevisieuitvoering': 'uitvoering_wijzigingsnummer'}[c] for c in codes.index.names]
codes.index.names = existing_idx_names
rich = rich.merge(
    codes,
    how='outer',
    left_on = [('rdw', 'conformity_codes', c) for c in codes.index.names],
    right_index=True
)
print(f'{rich.shape[1]} columns {rich.shape[0]} {rich.index.name}')

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# Add ovi
codes = pd.concat([rdw_ovi], keys=['ovi'], axis=1)
codes = pd.concat([codes], keys=['rdw'], axis=1)
rich = rich.merge(
    codes,
    how='outer',
    left_index = True,
    right_index = True,
)
print(f'{rich.shape[1]} columns {rich.shape[0]} {rich.index.name}')

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# Add vpic
codes = nhtsa_per_vin.copy()
codes = pd.concat([codes.reset_index().set_index('lot_index')], keys=[('nhtsa', 'vpic')], axis=1)
rich = rich.reset_index().merge(
    codes,
    how='outer',
    left_on = [('rdw', 'registrations', 'lot_index')],
    right_index = True
    #right_on = [('nhtsa', 'lot_index')]
).set_index(('rdw', 'registrations', 'lot_index')) # set to 3d index
rich.index.name = 'lot_index' # make 1d index again
print(f'{rich.shape[1]} columns {rich.shape[0]} {rich.index.name}')

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
rich.columns.map(lambda x: '_'.join(x))
rich

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# Three level column index
existing = pd.concat([drz], keys=[''], axis=1)
existing = pd.concat([existing], keys=['drz'], axis=1)
print(f'{existing.shape[1]} columns {existing.shape[0]} {existing.index.name}')
# Add rich to existing to make enriched
enriched = pd.merge(
    left = existing,
    right = rich,
    how = 'left',
    left_index = True,
    right_index = True
)
print(f'{enriched.shape[1]} columns {enriched.shape[0]} {enriched.index.name}')

# %% [markdown] editable=true slideshow={"slide_type": ""}
# # Saving

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# load drz auction results
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-data-{auction_month}-{month_counter}{suffix}.pkl'
if (SKIPSAVE==False) and (not(os.path.isfile(file_name))):
    print(file_name)
    enriched.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')
