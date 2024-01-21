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

# %% [markdown] slideshow={"slide_type": ""}
# <a id='rdw_top'>

# %% [markdown]
# # Add extra information from RDW open data
#
# Query to the open data dataset of the RDW.
#
#
# 1. <a href="#rdw_registrations">Registration numbers</a>  
#     Apis with license plates as key
# 2. <a href="#rdw_confcodes">Conformity codes</a>  
#     Cars get a conformity code when certified.
# 3. <a href="#rdw_other_apis">Other APIs</a>  
#     Query all conformity codes in belonging to data set.
# 4. <a href="#rdw_ovi">Website data</a>  
#     Get data from OVI RDW website. This takes a while because of time out enforced by website. Use config to disable.
# 5. <a href="#rdw_merge">Merge results</a>  
#     Combine all dataframes and save
# 6. <a href="#rdw_save">Save results</a>  
# - - - - 

# %% [markdown] slideshow={"slide_type": ""}
# ### User variables
#

# %% slideshow={"slide_type": ""}
import sys
import re
import json
from IPython.display import display

# %% slideshow={"slide_type": ""}
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

# %% [markdown]
# ### Modules and functions

# %%
import pandas as pd
import numpy as np
import re 
import os
# to keep api key hidden import this from sub dir
import assets.hidden_api_keys as hidden_api_keys
from rdw_info import *

# %% slideshow={"slide_type": ""}
main_api = 'm9d7-ebf2'
keur_api = 'vkij-7mwc'
apk_api = 'sgfe-77wx'
gebr_api = 'hx2c-gt7k'
toe_api = 'sghb-dzxx'

conf_api = '55kv-xf7m'

# %% [markdown]
# ### Load auction results

# %% [raw]
# OPBOD = False
# NO_PRICE = False
# auction_month = '2015-03'
# month_counter = ''
# file_name = f'../data/pdf-data-{auction_month}.pkl'
#

# %% tags=["nbconvert_instruction:remove_all_outputs"]
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
# <a href="#rdw_top" id='rdw_registrations'><font size=+1><center>^^ TOP ^^</center></font></a>
#
# ---

# %% [markdown]
# # Main api 
#
# The main api: `api_gekentekende_voertuigen` points to subsequent apis.

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# empty dictionary
rdw_per_reg = dict()

# first element of dict is registrations
key = 'registrations'
rdw_per_reg[key] = drz.loc[hasReg,['Reg', 'LotType']].copy() # copy from drz
rdw_per_reg[key]['kenteken'] = rdw_per_reg[key].Reg.apply(lambda r: r.replace('-','').upper())
rdw_per_reg[key].index.name = 'lot_index'
rdw_per_reg[key] = rdw_per_reg[key].reset_index().set_index('kenteken')
with pd.option_context('display.max_rows', 999):
    display(rdw_per_reg[key].reset_index().set_index(['LotType', 'kenteken']).sort_index())

print('\n'.join(rdw_per_reg.keys()))

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# Assess these registrations
regs = rdw_per_reg['registrations'].Reg.values

# Main rdw api
Info = RdwInfo(regs, main_api, hidden_api_keys.socrata_apptoken)
Info.process_api()
key = re.sub('\s', '_', Info.metadata_['name'].lower())
rdw_per_reg[key] = Info.get_df().copy()
print(Info)

# %% [markdown]
# Sub apis

# %%
# Get sub apis from main api
from_key = 'gekentekende_voertuigen'
sub_apis,_,_ = get_sub_apis(rdw_per_reg[from_key])
# add extra apis
sub_apis += ['3xwf-ince', '2ba7-embk', '7ug8-2dtt', 't49b-isb7', keur_api, apk_api, toe_api] #,'a34c-vvps', # some extra apis with registrations
for api_name in sub_apis:
    Info.set_api_name(api_name)
    Info.process_api()
    key = re.sub('\s', '_', Info.metadata_['name'].lower())
    key = re.sub(f'^{from_key}_', '', key)
    rdw_per_reg[key] = Info.get_df().copy()
    print(api_name, key)

# Get apis from apk api
from_key = 'meldingen_keuringsinstantie'
sub_apis,_,_ = get_sub_apis(rdw_per_reg[from_key])
for api_name in set(sub_apis):
    Info.set_api_name(api_name)
    Info.process_api()
    key = re.sub('\s', '_', Info.metadata_['name'].lower())
    key = re.sub(f'^{from_key}_', '', key)
    rdw_per_reg[key] = Info.get_df().copy()
    print(api_name, key)


# %% [markdown]
# add info from reference tables

# %%
# Use reference table to add info
df_left = rdw_per_reg['geconstateerde_gebreken'].copy()
df_right = rdw_per_reg['gebreken'].copy()
on_column = 'gebrek_identificatie'

for left_column, left in df_left.loc[:, df_left.columns.str.startswith(on_column)].iteritems():
    suffix = re.sub(on_column, '', left_column)
    df_merge = pd.merge(
        left=left.reset_index(),
        right=df_right,
        how='left',
        left_on=left_column,
        right_on=on_column,
    ).set_index('kenteken')
    df_merge = df_merge.drop(columns=[left_column, on_column, 'TimeStamp']).add_suffix(suffix)
    df_left = df_left.merge(df_merge, left_index=True, right_index=True)

# add extra table
rdw_per_reg['geconstateerde_gebreken_met_beschrijving'] = df_left
# clean up: 
#    remove reference table
del rdw_per_reg['gebreken']
#    remove table without description
del rdw_per_reg['geconstateerde_gebreken']

# %% tags=["nbconvert_instruction:remove_all_outputs"]
out = pd.concat(rdw_per_reg, axis=1)
display(out.loc[:, (slice(None), 'TimeStamp')].bfill(axis=0).iloc[-1,:].to_frame())

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# Save
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-reg/rdw-reg-full-0-data-{auction_month}-{month_counter}.pkl'

if NO_PRICE:
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
    
if (SKIPSAVE==False) and (not(os.path.isfile(file_name))):
    print(file_name)
    out.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')


# %% [markdown]
# <a href="#rdw_top" id='rdw_confcodes'><font size=+1><center>^^ TOP ^^</center></font></a>
#
# ---

# %% [markdown]
# # Conformity codes

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# empty dict
rdw_per_confcode = dict()
# Conformity codes consists of four fields that make a composite key
conf = rdw_per_reg['gekentekende_voertuigen'][[
    'typegoedkeuringsnummer', 
    'uitvoering', 
    'variant', 
    'volgnummer_wijziging_eu_typegoedkeuring'
]].copy()
conf.dropna(inplace=True)

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
# drop nan
conf = conf.query('typegoedkeuringsnummer != "nan"')

# duplicates
display(
    conf.loc[:, conf.columns]\
    .reset_index()\
    .groupby('eu_type_goedkeuringssleutel')\
    .nunique()\
    .replace(1,np.NaN)\
    .dropna(how='all')\
    .fillna(1)\
    .astype(int)\
    .sort_values(by='kenteken', ascending=False)
)

key = 'conformity_codes'
rdw_per_confcode[key] = conf.reset_index().set_index(['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer']).copy()


# %%
short_confs = rdw_per_confcode['conformity_codes'].reset_index()\
.set_index('typegoedkeuringsnummer').eu_type_goedkeuringssleutel
full_confs = rdw_per_confcode['conformity_codes'].reset_index()\
.set_index('typegoedkeuringsnummer').loc[:, ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer']]

# %%
# Main conformity code api
Info = RdwInfo(short_confs, conf_api, hidden_api_keys.socrata_apptoken)
Info.process_api()
key = re.sub('\s', '_', Info.metadata_['name'].lower())
key = re.sub(f'^{from_key}_', '', key)
rdw_per_confcode[key] = Info.get_df().copy()
print(key)

# %%
# Get sub apis from main api
from_key = 'eeg_voertuigtypegoedkeuring'
sub_apis,_,_ = get_sub_apis(rdw_per_confcode[from_key])
Info = RdwInfo(full_confs, sub_apis[0], hidden_api_keys.socrata_apptoken)
for api_name in sub_apis:
    Info.set_api_name(api_name)
    Info.process_api()
    key = re.sub('\s', '_', Info.metadata_['name'].lower())
    key = re.sub(f'^{from_key}_', '', key)
    rdw_per_confcode[key] = Info.get_df().copy()
    print(api_name, key)


# %% [markdown]
# Merge dataframes from conformity codes apis

# %% tags=["nbconvert_instruction:remove_all_outputs"]
print('x: Data can be merged. (should be unique, 4 level key and contain data)')
full_codes = dict()
for k, df in rdw_per_confcode.items():
    if (k != 'conformity_codes') and (df.index.nlevels == 4) and (df.index.is_unique):
        assert df.index.names == ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer']
        df.reset_index(inplace=True)
        df.uitvoering_wijzigingsnummer = df.uitvoering_wijzigingsnummer.astype(int).astype(str)
        df.set_index(['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'], inplace=True)
        full_codes[k] = df
        print(f'[x] {k:64s}', end='')
    else:
        print(f'[ ] {k:64s}', end='')

    print({True: '[idx: unique    ]', False: '[idx: NOT unique]'}[df.index.is_unique],
          f'[keys: {df.index.nlevels}]', 
          f'[shape: {df.shape[0]:3.0f},{df.shape[1]:3.0f}]'
         )

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# merge
out = pd.concat(full_codes, axis=1)
display(out.loc[:, (slice(None), 'TimeStamp')].bfill(axis=0).iloc[0,:].to_frame())

# %% tags=["nbconvert_instruction:remove_all_outputs"]
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

# %% [markdown]
# <a href="#rdw_top" id='rdw_ovi'><font size=+1><center>^^ TOP ^^</center></font></a>
#
# ---

# %% [markdown]
# # Data from rdw website (OVI)
# Optionally get data from rdw website

# %% slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
if OVIDATA == False:
    rdw_ovi = None
else:
    regs = rdw_per_reg['registrations'].Reg.to_list()
    Info = OviInfo(regs, verbose=VERBOSE)
    Info.process_api()
    print(Info)

    rdw_ovi = Info.data_.copy()
    # make fields lowercase and add "ovi_"
    rdw_ovi.index.name='kenteken'
    rdw_ovi.columns = [re.sub(r'([A-Z])',r'_\1', c).lower() if c != 'TimeStamp' else c for c in rdw_ovi.columns] # after capital, add _ 
    rdw_ovi.columns = [re.sub(r'^_','', c) for c in rdw_ovi.columns] # remove trailing _
    # Basic operations
    rdw_ovi = pd.concat(
        [rdw_ovi, 
         rdw_ovi.eigenaren.str.split('/', expand=True).rename(columns = {0: 'eigenaren_private', 1: 'eigenaren_company'}).astype('Int8')
        ], axis=1)
    rdw_ovi['eigenaren_total'] = rdw_ovi.eigenaren_private + rdw_ovi.eigenaren_company
    #rdw_ovi['ovi_wachten_op_keuring_ind'] = rdw_ovi.ovi_wachten_op_keuring.apply(lambda x: {'Ja': True, 'Nee': False}[x] if isinstance(x, str) else x).astype('boolean')

    if VERBOSE > 1:
        rdw_ovi
    else:
        print(rdw_ovi.shape)

# %% [raw]
# rdw_ovi = Info.data_.copy()
# # make fields lowercase and add "ovi_"
# rdw_ovi.index.name='kenteken'
# rdw_ovi.columns = [re.sub(r'([A-Z])',r'_\1', c).lower() if c != 'TimeStamp' else c for c in rdw_ovi.columns]
# rdw_ovi.columns = [re.sub(r'^_','', c) for c in rdw_ovi.columns]
# rdw_ovi

# %%
out = rdw_ovi.copy()

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# Save
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-ovi/rdw-ovi-0-data-{auction_month}-{month_counter}.pkl'

if NO_PRICE:
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
    
if (SKIPSAVE==False) and (not(os.path.isfile(file_name))):
    print(file_name)
    out.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')

# %% [markdown]
# <a href="#rdw_top" id='rdw_merge'><font size=+1><center>^^ TOP ^^</center></font></a>
#
# ---

# %% [markdown]
# # Data from The National Highway Traffic Safety Administration (NHTSA)
# Based on VIN. Product Information Catalog and Vehicle Listing (vPIC)
# https://vpic.nhtsa.dot.gov/api/

# %%
from vin_lookup import Nhtsa_batch

# %%
# empty dictionary
nhtsa_per_vin = dict()

# %% slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
key = 'vpic'
df_ =  drz.loc[:, ['Vin', 'Mfyear']].copy().replace({'': np.NaN, 'onbekend': np.NaN}) # copy from drz

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
out = Batch.data.copy()

# store in dict
nhtsa_per_vin[key] = pd.concat([
    nhtsa_per_vin[key],
    out.drop(columns=out.columns[out.columns.str.startswith('system') | out.columns.str.startswith('internal')])
], axis=1)

if VERBOSE > 1:
    display(nhtsa_per_vin[key])
else:
    print('\n'.join(nhtsa_per_vin.keys()))

# %%
# Merge with input
nhtsa_per_vin['vpic'].index.name = 'lot_index'
Batch.data.index.name = 'lot_index'
df_vins = pd.concat([
    nhtsa_per_vin['vpic'].loc[:, ['VIN', 'MFY']], 
    Batch.data
], axis = 1)
# add timestamp
df_vins.loc[:, 'TimeStamp'] = pd.Timestamp.now().strftime('%Y%m%d')
df_vins = df_vins.reset_index().set_index(['VIN', 'MFY'])

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

# %% [markdown]
# # Merge datasets
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

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# Merge first set
rich = pd.concat(rdw_per_reg, axis=1)
rich = pd.concat([rich], keys=['rdw'], axis=1)
rich.index.name='kenteken'
print(rich.shape, )

# Add conformity_codes
codes = rdw_per_confcode['conformity_codes'].reset_index().set_index('kenteken')
codes = pd.concat([codes], keys=['conformity_codes'], axis=1)
codes = pd.concat([codes], keys=['rdw'], axis=1)
rich = rich.merge(
    codes, # add level
    how='outer',
    left_index = True,
    right_index = True,
)
print(rich.shape)

# Add basic conformity info
codes = rdw_per_confcode['eeg_voertuigtypegoedkeuring'].reset_index()
# add levels
codes = pd.concat([codes], keys=['eeg_voertuigtypegoedkeuring'], axis=1)
codes = pd.concat([codes], keys=['rdw'], axis=1)
rich = rich.reset_index().merge(
    codes, 
    how='outer',
    left_on = [('rdw', 'conformity_codes', 'typegoedkeuringsnummer')],
    right_on = [('rdw', 'eeg_voertuigtypegoedkeuring', 'typegoedkeuringsnummer')],
).set_index('kenteken')
print(rich.shape)

# Add full_codes
codes = pd.concat(full_codes, axis=1)#.drop(columns='conformity_codes')
codes = pd.concat([codes], keys=['rdw'], axis=1)
rich = rich.merge(
    codes,
    how='outer',
    left_on = [('rdw', 'conformity_codes', c) for c in codes.index.names],
    right_index=True
)
print(rich.shape)

# Add ovi
codes = pd.concat([rdw_ovi], keys=['ovi'], axis=1)
codes = pd.concat([codes], keys=['rdw'], axis=1)
rich = rich.merge(
    codes,
    how='outer',
    left_index = True,
    right_index = True,
)
print(rich.shape)

# Add vpic
codes = pd.concat(nhtsa_per_vin, axis=1)
codes = pd.concat([codes], keys=['nhtsa'], axis=1)
rich = rich.reset_index().merge(
    codes,
    how='outer',
    left_on = [('rdw', 'registrations', 'lot_index')],
    right_index = True,
).set_index(('rdw', 'registrations', 'lot_index'))
rich.index.name = 'lot_index'
print(rich.shape)

# %%
rich.columns.map(lambda x: '_'.join(x))
rich

# %%
existing = pd.concat([drz], keys=[''], axis=1)
existing = pd.concat([existing], keys=['drz'], axis=1)
enriched = pd.merge(
    left = existing,
    right = rich,
    how = 'left',
    left_index = True,
    right_index = True
)

# %% [markdown]
# <a href="#rdw_top" id='rdw_save'><font size=+1><center>^^ TOP ^^</center></font></a>
#
# ---

# %% [markdown]
# # Saving

# %% tags=["nbconvert_instruction:remove_all_outputs"]
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-data-{auction_month}-{month_counter}.pkl'
if NO_PRICE:
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
    
if (SKIPSAVE==False) and (not(os.path.isfile(file_name))):
    print(file_name)
    enriched.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')

# %% [markdown]
# # Next: download images (or parallel)
#
# Because images might be taken down from the drz site, it is advisable to run the notebook that downloads images soon.
