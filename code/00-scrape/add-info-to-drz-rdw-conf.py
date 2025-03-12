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

# %% [markdown]
# # Conformity codes 
#
# Collect data from RDW based on conformity codes (TGK, typegoedkeuring)

# %% [markdown]
# ### User variables

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

# %% slideshow={"slide_type": ""}
if QUICK_MERGE:
    raise NotImplementedError

# %% [markdown]
# ### Collect number plate registrations

# %%
# Load registrations
suffix = '' if not OPBOD else '-opbod';
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-reg/rdw-reg-full-0-data-{auction_month}-{month_counter}{suffix}.pkl'
print(file_name)
rdw_per_reg = pd.read_pickle(file_name)
rdw_per_reg.index.name = 'kenteken';

# %%
if ('gekentekende_voertuigen', 'volgnummer_wijziging_eu_typegoedkeuring') not in rdw_per_reg.columns:
    raise 'Below is work-around.'
    rdw_per_reg.loc[:, ('gekentekende_voertuigen', 'volgnummer_wijziging_eu_typegoedkeuring')] = 0

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# see what lots have a Dutch registration (license number).
hasReg = (~drz.Reg.isnull()) & (drz.Reg != 'onbekend') & (drz.Reg != '') & (~drz.LotType.isin([
    'Vaartuig',
    'Jetski',
    'Sloep',
    'Speedboot',
    'Vaartuig (Type onbekend)',
    'Motorvaartuig met opbouw (Pleziervaartuig)',
]))

print('nr. of registrations:',sum(hasReg))

# adhoc fix
idx = '2022-08-5012' # check in pictures. reg is wrong
if idx in drz.index:
    drz.loc[idx, 'Reg'] = 'LM-82-14'
idx = '2022-29-5001' # check in pictures. reg is wrong
if idx in drz.index:
    drz.loc[idx, 'Reg'] = 'LM-82-14'
idx = '2022-29-2008' # check in pictures. reg is wrong
if idx in drz.index:
    drz.loc[idx, 'Reg'] = 'KT-05-40'



vc = drz.loc[hasReg, 'Reg'].str.upper().str.replace('-','').value_counts()
if any(vc > 1):
    display(vc[vc>1])
    display(drz[drz.Reg.str.upper().str.replace('-','').isin(vc[vc>1].index)])
    raise ValueError('Registration occurs in more than one lot.')
# assert all(vc == 1), [, display(vc[vc>1])]

# # make a copy and add info
# rdw = drz.copy()


# %% [markdown]
# # Query conformity codes

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# empty dict
rdw_per_confcode = dict()
# Conformity codes consists of four fields that make a composite key
conf = rdw_per_reg['gekentekende_voertuigen'][[
    'typegoedkeuringsnummer', 
    'uitvoering', 
    'variant', 
    'volgnummer_wijziging_eu_typegoedkeuring'
]].copy()

# drop nan
# conf.dropna(inplace=True, how='all')
conf = conf.query('typegoedkeuringsnummer != "nan"')

# Add shorter key "eu_type_goedkeuringssleutel"
conf = conf.merge(
    how='left', 
    right=long_to_short_conf(conf.typegoedkeuringsnummer).drop_duplicates(), 
    left_on='typegoedkeuringsnummer', right_index=True
)

# rename fields
conf.volgnummer_wijziging_eu_typegoedkeuring = conf.volgnummer_wijziging_eu_typegoedkeuring.astype('Int8').astype(str)
conf.rename(columns={
    'uitvoering': 'eeg_uitvoeringscode',
    'variant': 'eeg_variantcode',
    'volgnummer_wijziging_eu_typegoedkeuring': 'uitvoering_wijzigingsnummer',
}, inplace=True)

# duplicates
display(
    conf.loc[:, conf.columns]\
    .reset_index()\
    .groupby('eu_type_goedkeuringssleutel')\
    .nunique()\
    .replace(1,np.nan)\
    .dropna(how='all')\
    .fillna(1)\
    .astype(int)\
    .sort_values(by='kenteken', ascending=False)
)

key = 'conformity_codes'
rdw_per_confcode[key] = conf.reset_index().set_index(
    ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer']).copy()


# %%
short_confs = rdw_per_confcode['conformity_codes'].reset_index()\
.set_index('typegoedkeuringsnummer').eu_type_goedkeuringssleutel
full_confs = rdw_per_confcode['conformity_codes'].reset_index()\
.set_index('typegoedkeuringsnummer').loc[:, [
    'eu_type_goedkeuringssleutel', 
    'eeg_variantcode', 
    'eeg_uitvoeringscode', 
    'uitvoering_wijzigingsnummer',
    'kenteken'
]]
full_confs_with_long_and_reg = full_confs.reset_index().drop(columns=['eu_type_goedkeuringssleutel'])
rdw_per_confcode['kenteken'] = full_confs_with_long_and_reg

# For these apis reg is not needed.
full_confs_with_long = full_confs_with_long_and_reg.drop(columns=['kenteken']).copy()


# %%
out = rdw_per_confcode['conformity_codes'].reset_index().set_index('kenteken').copy()
out.shape

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# Save for later use
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-reg/rdw-reg-conf-0-data-{auction_month}-{month_counter}.pkl'

if NO_PRICE:
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
    
if (SKIPSAVE==False) and (not(os.path.isfile(file_name))):
    print(file_name)
    out.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')

# %% editable=true slideshow={"slide_type": ""}
# Get sub apis from main api
# This used to be a single api, now we use a "search" technique
from_key = 'tgk'
sub_apis, page_titles,_ = get_apis_with_search('title:"Open Data RDW: TGK"')
page_titles = iter(page_titles)
print(f'{from_key}')
for api_name in sub_apis:
    print(f'{api_name} {next(page_titles)}')
    if api_name == '9s6a-b42z':
        # This api (TGK-Intrekking-Typegoedkeuring) only needs one field as an index
        Info = RdwInfo(full_confs_with_long.typegoedkeuringsnummer, api_name, hidden_api_keys.socrata_apptoken)
    else:
        Info = RdwInfo(full_confs_with_long, api_name, hidden_api_keys.socrata_apptoken)
    Info.process_api()
    key = re.sub('\s', '_', Info.metadata_['name'].lower())
    key = re.sub(f'^{from_key}_', '', key)
    print(f'{api_name} {key}')
    rdw_per_confcode[key] = Info.get_df().copy()
    if api_name == 'x5v3-sewk':
        # rename typo in api handelsbenaming_fabrikant codevariantgk -> codevarianttgk (missing 't')
        rdw_per_confcode[key].index.names = [re.sub('codevariantgk', 'codevarianttgk', n) for n in rdw_per_confcode[key].index.names]



# %% [markdown] editable=true slideshow={"slide_type": ""}
# Merge dataframes from conformity codes apis

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
print('x: Data can be merged. (should be unique, 4 level key and contain data) /: will be saved differently')
full_codes = dict()
for k, df in rdw_per_confcode.items():
    if (k in ['conformity_codes', 'intrekking_typegoedkeuring', 'kenteken']):
        print(f'[/] {k:64s}', end='')
    elif (df.index.nlevels == 4) and (df.index.is_unique):
        assert df.index.names == ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering']
        df.reset_index(inplace=True)
        df.volgnummerrevisieuitvoering = df.volgnummerrevisieuitvoering.astype(int).astype(str)
        df.set_index(['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], inplace=True)
        full_codes[k] = df
        print(f'[x] {k:64s}', end='')
    else:
        print(f'[ ] {k:64s}', end='')

    print({True: '[idx: unique    ]', False: '[idx: NOT unique]'}[df.index.is_unique],
          f'[keys: {df.index.nlevels}]', 
          f'[shape: {df.shape[0]:3.0f},{df.shape[1]:3.0f}]'
         )

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# merge
out = pd.concat(full_codes, axis=1)
display(out.loc[:, (slice(None), 'TimeStamp')].bfill(axis=0).iloc[0,:].to_frame())

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# Save
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-conf/rdw-conf-0-data-{auction_month}-{month_counter}.pkl'

if NO_PRICE:
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
    
if (SKIPSAVE==False) and (not(os.path.isfile(file_name))):
    print(file_name)
    out.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')

# %%
out = rdw_per_confcode['intrekking_typegoedkeuring']
out.shape

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
# Save for later use
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-conf/rdw-conf-revoke-0-data-{auction_month}-{month_counter}.pkl'

if NO_PRICE:
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
    
if (SKIPSAVE==False) and (not(os.path.isfile(file_name))):
    print(file_name)
    out.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')
