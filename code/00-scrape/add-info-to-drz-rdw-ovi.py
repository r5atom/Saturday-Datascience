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
# # RDW OVI
#
# OVI: "Open voertuig informatie". This scrapes the ovi website of RDW.  
# https://ovi.rdw.nl/
#
# This is disfunctional due to redirect technique that prevents scraping.

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

# %% [markdown] editable=true slideshow={"slide_type": ""}
# # Scrape data from rdw website

# %% editable=true slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
VERBOSE = 100
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
    if 'eigenaren' in rdw_ovi.index:
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

# %% editable=true slideshow={"slide_type": ""}
out = rdw_ovi.copy()
out.shape

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# Save
file_name = f'{DATA_DIR}/auctions/enriched-results/rdw-ovi/rdw-ovi-0-data-{auction_month}-{month_counter}.pkl'

if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
    
if (SKIPSAVE==False) and (not(os.path.isfile(file_name))):
    print(file_name)
    out.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')

# %%
#DEBUG

# %% [raw]
# Info.verbose_level_ = 100
# Info._url
# # web_request(Info._url, params = {'kenteken': Info.get_current_reg()})
# import requests
# headers =  {"User-Agent": "Mozilla/5.0"}
# resp = requests.request('GET', Info._url, params = {'kenteken': Info.get_current_reg()}, headers=headers)
# resp.url, resp.status_code, resp.reason
# # resp.text

# %% [raw]
# # was
# # {
# # 'Server': 'Microsoft-Azure-Application-Gateway/v2',
# # 'Date': 'Wed, 11 Dec 2024 17:44:57 GMT',
# # 'Content-Type': 'text/html',
# # 'Content-Length': '179',
# # 'Connection': 'keep-alive'}
# # is
# # {'Date': 'Wed, 11 Dec 2024 17:45:25 GMT',
# # 'Content-Type': 'text/html',
# # 'Content-Length': '1539',
# # 'Connection': 'keep-alive',
# # 'Accept-Ranges': 'bytes',
# # 'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
# # 'Content-Encoding': 'gzip',
# # 'ETag': '"0e367799c44db1:0"',
# # 'Last-Modified': 'Mon, 02 Dec 2024 09:27:58 GMT',
# # 'Vary': 'Accept-Encoding',
# # 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
# # 'X-XSS-Protection': '1; mode=block',
# # 'X-Content-Type-Options': 'nosniff',
# # 'Referrer-Policy': 'same-origin',
# # 'Content-Security-Policy': "default-src 'self'; script-src 'self' az416426.vo.msecnd.net https://*.googletagmanager.com https://tagmanager.google.com https://www.google-analytics.com; connect-src 'self' https: https://*.google-analytics.com https://*.analytics.google.com https://*.googletagmanager.com https://*.g.doubleclick.net https://*.google.com; img-src 'self' data: https://*.google-analytics.com https://*.analytics.google.com https://*.googletagmanager.com https://*.g.doubleclick.net https://*.google.com; style-src 'self'; font-src 'self'; object-src 'none';  frame-ancestors https://authenticatie1.rdw.nl https://authenticatie2.rdw.nl;"
# }
# resp.headers

# %%
### ISSUE: site calls several .js scripts that generate info page. 

# %% [raw]
# Info.tree_.xpath('//*/app-ovi//*/p/text()')
