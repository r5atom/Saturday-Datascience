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
# # Registration numbers
#
# Collect additional data from RDW based on registrations (kenteken)
#

# %% [markdown] slideshow={"slide_type": ""}
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

# %% slideshow={"slide_type": ""}
# run these apis

main_api = 'm9d7-ebf2' # gekentekende_voertuigen
keur_api = 'vkij-7mwc' # keuringen
apk_api = 'sgfe-77wx' # meldingen_keuringsinstantie
gebr_api = 'hx2c-gt7k' # gebreken
toe_api = 'sghb-dzxx' # toegevoegde_objecten

conf_api = '55kv-xf7m' # EEG_Voertuigtypegoedkeuring

# g2s6-ehxa Motor-Uitvoering

# byxc-wwua TGK Basis Uitvoering
# kyri-nuah TGK Merk Uitvoering
# xn6e-huse TGK-Rupsbandset-Uitvoering
# d3ex-xghj TGK-Koppeling-Uitvoering
# 4by9-ammk TGK-Aandrijving-Uitvoering
# m692-vvff TGK-Speciale-Doeleinden
# gr7t-qfnb TGK-Energiebron-Uitvoering
# 9s6a-b42z TGK-Intrekking-Typegoedkeuring

# wx3j-69ie     Basisgegevens_EEG_Uitvoering
# ahsi-8uyu     AS_Gegevens_EEG_Uitvoering
#  xhyb-w7xt     TGK-As-Uitvoering
# q7fi-ijjh     Carrosserie_Uitvoering_Klasse
# w2qp-idms     Carrosserie_Uitvoering
#  ky2r-jqad     TGK-Carrosserie-Uitvoering
# nypm-t8hx     Carrosserie_Uitvoering_Nummerieke_Co
# mdqe-txpd     Handelsbenaming_Uitvoering
#  x5v3-sewk     TGK-Handelsbenaming-Fabrikant
# fj7t-hhik     Merk_Uitvoering_Toegestaan
# g2s6-ehxa     Motor_Uitvoering
# 5w6t-p66a     Motor_Uitvoering_Brandstof
# mt8t-4ep4     Plaatsaanduiding_Uitvoering
# h9pa-e9ta     Subcategorie_Uitvoering
# 2822-t8sx     Uitvoering_Gebruiksgegevens_Per_Uitg
# r7cw-67gs     Versnellingsbak_Uitvoering
#  7rjk-eycs     TGK-Versnelling-Uitvoering

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
# # Main api 
#
# The main api: `api_gekentekende_voertuigen` points to subsequent apis.

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
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

# %% editable=true slideshow={"slide_type": ""}
# Get sub apis from main api
from_key = 'gekentekende_voertuigen'
sub_apis,_,_ = get_sub_apis(rdw_per_reg[from_key])
# add extra apis
sub_apis += ['3xwf-ince', '2ba7-embk', '7ug8-2dtt', 't49b-isb7', keur_api, apk_api, toe_api] #,'a34c-vvps', # some extra apis with registrations
print(f'{from_key}')
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
print(f'{from_key}')
for api_name in set(sub_apis):
    Info.set_api_name(api_name)
    Info.process_api()
    key = re.sub('\s', '_', Info.metadata_['name'].lower())
    key = re.sub(f'^{from_key}_', '', key)
    rdw_per_reg[key] = Info.get_df().copy()
    print(api_name, key)


# %%
# Use reference table to add info
df_left = rdw_per_reg['geconstateerde_gebreken'].copy()
df_right = rdw_per_reg['gebreken'].copy()
on_column = 'gebrek_identificatie'

for left_column, left in df_left.loc[:, df_left.columns.str.startswith(on_column)].items():
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
display(out.loc[:, (slice(None), 'TimeStamp')].bfill(axis=0).iloc[0,:].to_frame())

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

