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
# <a id='auct_top'>

# %% [markdown]
# # Scrape results of auction
# Monthy results of auction are publicized on https://verkoop.domeinenrz.nl. This Notebook scrapes the result from the drz website and parses the text and stores it in a dataframe.
#
# 1. <a href="#auct_dl_results">Download results</a>  
#     This will read all raw text from pages.  
# 2. <a href="#auct_basic_parse">Basic parsing</a>  
#     Raw text is parsed for the first time. Some basics elements are stored in a pandas.DataFrame (price, image urls, title, ..)
# 3. <a href="#auct_regex">Regex parsing</a>   
#     Do some more sophisticated parsing by using regular expressions.  
# 4. <a href="#auct_save">Save to disk</a>
#
# - - - 

# %% slideshow={"slide_type": ""}
# First create a settings file for current auction.
# This file may already exist.
# !cd ..; \
# python3 assets/make_auction_setting_file.py "2024-0013" I "20240706" \
# -v -c assets/drz-settings.ini \
# -s assets/drz-settings-current.json

# %%
def piplist2dict(lst, QUIET=True):
    out={};
    for i,l in enumerate(lst):
        if i==0 and l.startswith('Package'):
            if not QUIET: print(l)
            continue
        elif i==1 and l.startswith('---'):
            if not QUIET: print(l)
            continue
        item = (l.split(' ')[0], l.split(' ')[-1])
        out[item[0]] = item[1]
    if not QUIET: print(f'{len(out)} packages in list.')
    return out

def diffpipdict(old, new, QUIET=True):
    isequal=True
    for i,v in new.items():
        if i not in old:
            if not QUIET: print(f'{i} not in old')
            isequal = False
            continue
        if v == old[i]:
            if not QUIET: print(f'{i} equal')
            continue
        if not QUIET: print(i, dcur[i], v)
        isequal = False
    return isequal

with open("../../assets/python-env-current.txt",'r') as fid:
    current = fid.read()
current = current.splitlines()
# new = !pip list

dcur = piplist2dict(current)
dnew = piplist2dict(new)
if diffpipdict(dcur, dnew) == False:
    print('Replace pip list')
    # !mv --backup=numbered ../../assets/python-env-current.txt ../../assets/python-env-bup.txt
    with open("../../assets/python-env-current.txt",'w') as fid:
        fid.write('\n'.join(new))

# %%
auction_settings_file = '../assets/drz-settings-current.json'

# %% [markdown]
# ### Read settings

# %% slideshow={"slide_type": ""}
import json
import sys
import os
import re


# %% tags=["nbconvert_instruction:remove_all_outputs"]
with open(auction_settings_file, 'r') as fid:
    cfg = json.load(fid)
print(cfg['AUCTION'])

OPBOD = cfg['AUCTION']['kind'] == 'opbod'
AUCTION_ID = cfg['AUCTION']['id']
DATE = cfg['AUCTION']['date']
DATA_DIR = cfg['FILE_LOCATION']['data_dir']
REGEX_DIR = cfg['FILE_LOCATION']['regex_dir']
auction_month = DATE[:4] + '-' + DATE[4:6]
if cfg['AUCTION']['kind'] == 'inschrijving':
    month_counter = re.sub('(-)(\d{2})', '\g<1>', AUCTION_ID)[5:8]
    URL = cfg['URL']['inschrijving']
elif cfg['AUCTION']['kind'] == 'opbod':
    month_counter = re.sub('(-)(\d{2})(\d{2})', '-\g<2>', AUCTION_ID)[5:8]
    URL = cfg['URL']['opbod']
URL_DATA = cfg['URL.data']

sys.path.insert(0, cfg['FILE_LOCATION']['code_dir'])

EXTEND_URL = False
VERBOSE = int(cfg['GENERAL']['verbose'])
SAVE_METHOD = cfg['GENERAL']['save_method']
RUN_EXAMPLES = True # Run examples after defining functions. These might result in errors, so supressing them here avoids breaking the script.

# %%
SAVE_METHOD='always_overwrite' # override setting, because this is the first step

# %% tags=["nbconvert_instruction:remove_all_outputs"]
URL,URL_DATA,month_counter,auction_month


# %%
if SAVE_METHOD == 'skip_when_exist':
    do_save = lambda fn: not(os.path.isfile(fn))
elif SAVE_METHOD == 'always_overwrite':
    do_save = lambda _: True
elif SAVE_METHOD == 'skip_save':
    do_save = lambda _: False
else:
    raise NotImplementedError(f'SAVE_METHOD: {SAVE_METHOD} not implemented')

# %% [markdown]
# ### Import modules

# %%
# virtualenv
M = re.match('\((.*?)\) ', os.popen('echo $PS1').read())
# os.popen('echo -n $VIRTUAL_ENV').read()
if M is not None:
    print(f'Virtual environment: {M[1]}')
else:
    print('Virtual environment not activated')

# %%
import pandas as pd
from datetime import datetime
import warnings

# needed for as of feb '18 url format
import locale
try:
    locale.setlocale(locale.LC_TIME,'nl_NL')
except:
    locale.setlocale(locale.LC_TIME,'nl_NL.utf8')



# %%
auct_dates = pd.read_csv('../../assets/auction-dates-current.csv', sep=';')
for fld in ['Start online veiling', 'Sluiting online veiling']:
    auct_dates.loc[:, fld] = \
    auct_dates.loc[:, ['Verkoop', fld]].apply(
        lambda x: datetime.strptime(f'{x.Verkoop.split("-")[0]} {x.loc[fld]}', '%Y %d %B %H:%M uur')
        , axis=1
)
auct_dates.set_index('Verkoop', inplace=True)
for col in ['Start online veiling', 'Sluiting online veiling']:
    auct_dates.loc[:,col] = auct_dates.loc[:,col].astype('datetime64[ns]')



# %% tags=["nbconvert_instruction:remove_all_outputs"]
now = pd.Timestamp.now()
expected = pd.to_datetime(auction_month,format='%Y-%m')
expected = auct_dates.loc[AUCTION_ID].values[0]
print(f"""Dates
Today:    {now.strftime('%Y-%m') } ({now.strftime('%A %d %B')})
Settings: {DATE} ({expected.strftime('%A %d %B')})""")
if now.strftime('%Y-%m') != expected.strftime('%Y-%m'):
    warnings.warn(f'''
    Settings file has date set at [{DATE}] but expected [{now.strftime('%Y-%m')}]. Has <{cfg['FILE_LOCATION']['auction_settings_file']}> file been updated?
    With older auctions it sometimes works to add [url_add_veilingen=True]
    ''', RuntimeWarning)
    # If auction was in past. Url needs to be extended by setting `add_veilingen = True`:
    EXTEND_URL = True
    

del(now)


# %% [markdown]
# ### Functions

# %% tags=["nbconvert_instruction:remove_all_outputs"]
def get_kavel_url(OPBOD, base_url, url_data, lot_id):
    
    '''
    Create url
    '''

    import urllib
    
   
    # Add field to dicts that are passed to urlencode
    urldata = {}
    if not OPBOD:
        # to create '=&'. This might be a bug in the site 
        urldata[''] = ''
    
    # Add auction id
    for k,v in URL_DATA.items():
        urldata[k] = v
    
#     if add_veilingen:
#         # get date from url
#         date_string = re.findall(r'_([0-9]{4}-[0-9]{4})', base_url)
#         urldata['veilingen'] = ''.join(date_string)

    # Status is specific for "opbod"
    if OPBOD:
        urldata['status'] = 'both' # or "closed"        

    # Add lot number
    urldata['meerfotos'] = lot_id
    
    # Generate string by using urldata
    kavel_url = base_url + '?' + urllib.parse.urlencode(urldata)

    return kavel_url

# example
if RUN_EXAMPLES:
    ids = [
        f'K{auction_month[2:4]}00{month_counter}1800', 
        f'K{auction_month[2:4]}00{month_counter}1801', 
        f'K{auction_month[2:4]}00{month_counter}1900', 
        f'K{auction_month[2:4]}00{month_counter}1901', 
        f'K{auction_month[2:4]}00{month_counter}1000', 
        f'K{auction_month[2:4]}00{month_counter}1001',
        f'K{auction_month[2:4]}00{month_counter}1002',
        f'K{auction_month[2:4]}00{month_counter}1003',
        f'K{auction_month[2:4]}00{month_counter}1004',
        f'K{auction_month[2:4]}00{month_counter}1009',
        f'K{auction_month[2:4]}00{month_counter}1031',
        f'K{auction_month[2:4]}00{month_counter}1007',
        f'K{auction_month[2:4]}00{month_counter}1005',
    ]
    if OPBOD:
        ids = [f'K{auction_month[2:4]}{auction_month[-2:]}01{id[-4:]}' for id in ids]
    
    for example_lot_id in ids:
        example_url = URL
        _add_veiling = EXTEND_URL
        print(get_kavel_url(OPBOD, example_url, URL_DATA, example_lot_id))


# %% tags=["nbconvert_instruction:remove_all_outputs"]
def gettree(kavel_url, disp=False):
    
    '''
    get html tree from string
    '''
    
    import requests
    import codecs
    from lxml import html, etree
    
    # Request page
    
    req_success = False; c=0 # Try several times
    
    while req_success == False:
        c+=1
        
        try:
            page = requests.get(kavel_url)
            if disp:
                print(page, c)

            # raise error within try if status is not OK (OK=200)
            assert page.status_code == 200
            
            # Otherwise ok
            req_success = True
        
        except KeyboardInterrupt:
            raise
        except:
            if c == 1:
                print('retry', end=',')
            elif c > 100:
                raise Exception(f'Retried {c} times, but failed')
            else:
                if c > 50:
                    # Add extra pause after many tries
                    time.sleep(c-50)
                print(f'{c}', end='x')
                req_success = False

    # find encoding in header
    DecodeType = page.headers["Content-type"]
    T = 'charset='
    DecodeType = DecodeType[DecodeType.find(T)+len(T):]
    # and convert to unicode
    htmlstring = codecs.decode(page.content, DecodeType)
    
    # Convert string to tree object
    tree = html.fromstring(htmlstring)
    
    return tree


# Example
if RUN_EXAMPLES:
    gettree(
        get_kavel_url(False, example_url, False, example_lot_id),
        True
    )


# %% slideshow={"slide_type": ""} tags=["nbconvert_instruction:remove_all_outputs"]
class Lot:
    
    
    def __init__(self, tree, OPBOD, disp=False):
        self.tree = tree
        self.OPBOD = OPBOD
        self.disp = disp

        # Has content? Price should be bold.
        # if nothing is bold. Page may exist but results are not in yet.
        paths = [
            '//*[@id="content"]/div[1]/div[1]/strong/text()',
            '//*[@id="content"]/div[1]/div[1]/b/text()',
            '//*[@id="content"]/div[1]/b/text()',
            '//*[@id="content"]/div[1]/p/b/text()', # <<- OPBOD needs this
        ]
        contents = [self.tree.xpath(path) for path in paths]
        content = [c[0] for c in contents if len(c)>0]
        
        if len(content) > 0:
            if content[0] == 'Niets gevonden.':
                self.has_result = -1
            else:
                self.has_result = True
        else:
            self.has_result = False

        
    def __str__(self):
        out = self.tree.xpath('/html/head/title/text()')
        if hasattr(self, 'title_'):
            out += [self.title_]
        if hasattr(self, 'lot_index_'):
            out += [self.lot_index_]
        if hasattr(self, 'date_'):
            out += [self.date_]
        if hasattr(self, 'price_'):
            out += [f'EUR {self.price_:6.0f}']
            if hasattr(self, 'draw_') and (self.draw_):
                out[-1] += ' (draw)'
        if hasattr(self, 'nextlot_'):
            out += [f'next [{self.nextlot_:4.0f}]']
        if hasattr(self, 'images_'):
            out += [f'{len(self.images_):3.0f} images']
        if hasattr(self, 'text_'):
            out += [f'{len(self.text_):3.0f} text lines']
            
        if self.has_result == -1:
            out += ['no content.']
        elif self.has_result == False:
            out += ['no result.']
        return ' | '.join(out)

        
    
    def get_title(self):
        
        '''
        Return title of this page. This can be found in a H4 with class name 'title'.
        '''

        path = '//h4[@class="title"]/text()'
        
        self.title_ = self.tree.xpath(path)[0].strip()
        
        
    def get_images(self):
        
        '''
        Return urls (src) of images. These are inside divs of class 'photo'
        '''
        
        lines = [item.get('src') for item in self.tree.xpath('//div[@class="photo"]/a/img')]
    
        self.images_ = lines
    
    def get_text(self):
        
        '''
        Just return all relevant text, which is in class 'catalogusdetailitem split-item-first'.
        '''
        
        lines = self.tree.xpath('//div[@class="catalogusdetailitem split-item-first"]/text()')
        
        self.text_ = lines
        
    def split_title(self):
        
        '''
        Split title into fields:
        year, month, counter, lotnr
        '''
        
        if not hasattr(self, 'title_'):
            self.get_title()

        lot_id = re.match('(Kavel )?(.*)',self.title_).group(2)
        if lot_id.startswith('K'):
            #M = re.match('^K([0-9]{2})(00|01)(0[1-9]|1[0-2])([0-9]{4})$', lot_id)
            #argout = tuple([M[i] for i in range(1, 5)])
            # Added counter
            #M = re.match('^K([0-9]{2})(00|01)((0|1)[1-9]|1[0-2])([0-9]{4})$', lot_id)
            # Reorder fields if needed
            if not OPBOD:
                fields = ['^',
                          'K([0-9]{2})',         # K21 year
                          '([0,1]{2})',          # 01, 00
                          '([0-9]{2})',          # mm month
                          '([0-9]{4})',          # iiii lotnr
                          '$'
                         ]
            elif OPBOD:
                fields = ['^',
                          'K([0-9]{2})',         # K21 year
                          '([0-9]{2})',          # mm month
                          '([0,1]{2})',          # 01, 00
                          '([0-9]{4})',          # iiii lotnr
                          '$'
                         ]
            M = re.match(''.join(fields), lot_id)
            if not OPBOD:
                argout = tuple([M[i] for i in [1, 2, 3, 4]])
            elif OPBOD:
                argout = tuple([M[i] for i in [1, 3, 2, 4]])
        else:
            lot_nr = int(lot_id)
            argout =(None, None, None, lot_nr)
            
        if self.disp: print(argout)

       
        return lot_id, argout[0], argout[1], argout[2], argout[3]
    
    def get_date(self):
        '''
        Return date based on title
        '''
        _, yy, _, mm, _ = self.split_title()
        
        self.date_ = f'20{yy}-{mm}'
    
    def get_date_from_tree(self):
        
        '''
        Return date of this auction by taking the title of the page.
        This is pretty obsolete, because date is given at start of this notebook.
        '''
        
        lines = self.tree.xpath('//title/text()')
        date = lines[0]
        
        if 'Verkoop catalogus ' in date:
            # title like "Verkoop catalogus 2017-12"
            date = re.match('Verkoop catalogus (.*)',date)[1]

        elif 'Verkoop bij inschrijving ' in date:
            # title like "Verkoop bij inschrijving 2019-0001 januari"
            M = re.match('Verkoop bij inschrijving (20[0-9]{2})-00([0-9]{2}).*',date)
            date = '-'.join([M.group(1),M.group(2)])

        else:
            raise NotImplementedError(f'TODO: implement a date formatted as <{date}>.')
       
        self.date_ = date
    
    
    def get_nextlot(self):
        
        '''
        Return number of next lot by checking out the link to the next lot in the current page.
        'K1900011801' will become 1801
        '''
        
        xpaths = [
            r'//div[@class="catalogusdetailitem split-item-first"]/div[2]/div[3]/a',
            r'//div[@class="catalogusdetailitem split-item-first"]/div[3]/div[3]/a', # when auction is still active
        ]
        
        # link to next lot
        trycount = 0
        maxtries = len(xpaths)
        OK = False
        while (OK == False) and (trycount < maxtries):
            xpath = xpaths[trycount]
            Link = self.tree.xpath(xpath)
            if len(Link) == 0:
                print('Item not found. Try next option.', end = ' ')
                trycount += 1
            else:
                if trycount > 0:
                    print('Item found.')
                OK = True
        Tar = Link[0].get("href")
       
        # extract lot name
        nextLot = re.match('.*[\?,\&]meerfotos=(.*)(\&.*)?',Tar).group(1)

        if "&veilingen=" in nextLot:
            nextLot = re.match('(.*)&',nextLot).group(1)
            
        # convert to integer
        nextLot = int(nextLot[-4:])

        if self.disp:
            print(nextLot,Tar,etree.tostring(Link[0]))
                
        self.nextlot_ = nextLot
    
    def get_price(self):
        
        '''
        Return price as float
        '''

        def get_price_opbod(self, price_line):
            # Starts with status
            if (len(price_line) == 1) and (price_line[0] == 'Deze kavel is gesloten.'):
                
                # Check for first line whether bid was assigned
                if not hasattr(self, 'text_'):
                    self.get_text()
                if self.text_[0] == 'Niet gegund':
                    price_line = 'Niet gegund'
                    return price_line

                print('closed? cancelled?')
                
                return None
            if (len(price_line) < 1):
                # fall back: no bold
                price_line = [self.tree.xpath('//div[@class="catalogusdetailitem split-item-first"]/text()')[0]]
            if (price_line[0] == 'Huidig bod:'):
                # still active
                price_line = ['Huidig bod:' + self.tree.xpath('//div[@class="catalogusdetailitem split-item-first"]/text()')[0]]

    
            # Drop first
            if price_line[0] == 'Deze kavel is gesloten.':
                price_line = price_line[1:]    
            
            if len(price_line) > 1:
                print('Opbod has more than 1 prices. Take last')
                print(price_line)
            elif len(price_line) == 0:
                print('Price not found, return None')
                return None
            
            return price_line[-1] # Return scalar, not list
                
        def get_price_insch(self, price_line):
            if len(price_line) == 0:
                price_line = self.tree.xpath('//b/text()')
                
            if len(price_line) == 0:
                print('Price not found, return None')
                return None
            return price_line[0] # Return scalar, not list        
        
        def parse_line(price_line):
            tags = ['Zie kavel','Zie massakavel', 'Zie Kavel'] # part of combination lot
            if any([t in price_line for t in tags]) :
                price = 0
            elif price_line == 'Niet gegund':
                price = 0
            else:
                value_pat = '\u20ac *([0-9,.]*\,[0-9]{2})'
                pats = [
                    f'Gegund voor: {value_pat} *\(excl. alle eventuele bijkomende kosten en belastingen\)',
                    f'Huidig bod: {value_pat}'
                ]
                for pat in pats:
                    M = re.match(pat, price_line)
                    if M is not None:
                        break
                if self.disp: print(M.group(0))
                price = float(M.group(1).replace('.','').replace(',','.'))
            return price

        # Input error
        if self.OPBOD is None:
            raise ValueError('Set [OPBOD] before running this function.')
        
        # price can be bold or strong
        price_line = self.tree.xpath('//div[@class="catalogusdetailitem split-item-first"]/strong/text()')

        if not self.OPBOD:
            price_line = get_price_insch(self, price_line)
        else:
            price_line = get_price_opbod(self, price_line)
            

        if self.disp: print(price_line)
            
        if (price_line is None) or (len(price_line) == 0):
            print('No price found! use 0 for now')
            print(*self.tree.xpath('//*[@class="catalogusdetailitem split-item-first"]/text()'))
            price_line = 'Niet gegund'
            raise Exception('Fix this')
            
        if price_line == 'Na loting':
            price_line = self.tree.xpath('//strong/text()')[0]
            Draw = True
        else:
            Draw = False        

        Price = parse_line(price_line)

        
        self.price_ = Price
        self.draw_ = Draw
        
        
    def get_index(self):
        
        '''
        Unique id to this lot. Includes date.
        yyyy-mm-xxxx
        '''
        
        _, yy, _, mm, lot_nr = self.split_title()
        
        self.lot_index_  = f'20{yy}-{mm}-{lot_nr}'
        
    def get_images_v1(self):
        
        '''
        Return urls (src) of images. These are inside divs of class 'photo'
        '''
        
        lines = [item.get('src') for item in self.tree.xpath('//div[@class="photo"]/img')]
            
        self.images_ = lines

    def get_nextlot_v1(self):
        
        '''
        Return number of next lot by checking out the link to the next lot in the current page.
        'K1900011801' will become 1801
        
        update 202007: layout changed. Link for next lot is in diffent div
        '''
        
        
        # link to next lot
        link = self.tree.xpath('//div[@class="catalogusdetailitem split-item-first"]/div[4]/div[3]/a')
        tar = link[0].get("href")
        
        # extract lot name
        nextLot = re.match('.*[\?,\&]meerfotos=(.*)(\&.*)?', tar).group(1)

        if "&veilingen=" in nextLot:
            nextLot = re.match('(.*)&',nextLot).group(1)
            
        # convert to integer
        nextLot = int(nextLot[-4:])

        if self.disp:
            print(nextLot, Tar, etree.tostring(Link[0]))
                
        self.nextlot_ = nextLot
            
# Example
if RUN_EXAMPLES:
    c = 0
    OK = False
    while OK == False:
        try:
            example_lot_id = ids[c]
            kavel_url = get_kavel_url(OPBOD, example_url, _add_veiling, example_lot_id)
            print(kavel_url)
            tree = gettree(kavel_url, True)
            Item = Lot(tree, OPBOD)
            print(Item)
            Item.get_index()
            OK = True
        except IndexError:
            c = c + 1
            if c > len(ids): raise RuntimeError
            OK = False
    print(Item)
    Item.get_date()
    print(Item)
    Item.get_title()
    print(Item)
    Item.get_nextlot()
    print(Item)
    Item.get_images()
    print(Item)
    Item.get_text()
    print(Item)
    try:
        # This might throw an error if auction is still open
        Item.disp=True
        Item.get_price()
    except:
        print('Ignore error in retrieving price.')
        Item.price_ = -1
    print(Item)
    Item.has_result, Item.price_, 


# %% [markdown]
# <a href="#auct_top" id='auct_dl_results'><font size=+1><center>^^ TOP ^^</center></font></a>
#
# ---

# %% [markdown]
# # Get all results from all pages
#
# The "**next lot**" is linked in the current result. The function will look for this link and proceed. 
# Because it is not know what the first lot will be, it is hard coded at `lot_counter = 1799`. 
# It will increment with a step of `+1` to find the first lot.  
# Searching for next lots will continue untill the next lot has a **smaller** value that the current. This will cause the routine to stop when the last lot points back to the first lot.
#

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# info
print('+: add 1 to lot number\n>: follow link to go to next\nX: Done. Reached first lot in carousel\n')

DOLOOP = True; all_lots = dict()
# first lot
if OPBOD:
    lot_counter = 999
    lot_pat = 'K{:s}{:s}01{:.0f}' # 'K1809011800': Kyymm01llll
else:
    lot_counter = 1799
    lot_pat = 'K{:s}00{:s}{:.0f}' # 'K1800091800': Kyy00mmllll
    
while DOLOOP:
    all_lots[lot_counter] = dict()
    # get lot
    lot_id = lot_pat.format(auction_month[2:4], month_counter, lot_counter)
    lot_url = get_kavel_url(OPBOD, URL, EXTEND_URL, lot_id)
    lot_tree = gettree(lot_url, disp = VERBOSE > 2)
    lot_item = Lot(lot_tree, OPBOD)
    
    # continue with next if no content
    if lot_item.has_result == -1:
        next_lot = lot_counter + 1
        print(lot_counter, end='+')
        lot_counter = next_lot
        if VERBOSE > 2: print('', end='\n')
        continue

    # find next number
    try:
        lot_item.get_nextlot()
        next_lot = lot_item.nextlot_
    except KeyboardInterrupt:
        raise
    except:
        # Do not go to next, but try this one again
        print(lot_url)
        print('try again',end='>')
        next_lot = lot_counter
        lot_item.get_nextlot()

        

    # add current results to list
    all_lots[lot_counter]['url'] = lot_url
    all_lots[lot_counter]['item'] = lot_item
    print(lot_counter, end='>')
    
    if VERBOSE > 2: print(lot_item)

    if next_lot in all_lots.keys() :
        # First lot_counter again. Break loop before entering a carousel
        # If there is ony one lot. next_lot equals lot_counter
        DOLOOP = False
    else :
        # continue with next_lot
        lot_counter = next_lot
        
print('X') # done

# %% [markdown]
# <a href="#auct_top" id='auct_basic_parse'><font size=+1><center>^^ TOP ^^</center></font></a>
#
# ---

# %% [markdown]
# # Basic parsing
#
# Simple stuff, without regex.

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# Filter out empty lots
all_lots = {k: v for k,v in all_lots.items() if 'item' in v}

# Get indices and read info from tree
lot_indices = []
for lot_nr, lot in all_lots.items():
    lot_item = lot['item']
    lot_url = lot['url']
    lot_item.get_title()
    try:
        lot_item.get_price()
    except:
        print('catch: no price ', end='')
        lot_item.price_ = -1
        lot_item.draw_ = False
    lot_item.get_date()
    lot_item.get_images()
    lot_item.get_text()
    lot_item.get_index()
    if VERBOSE>0: print(lot_nr, lot_item)

out = pd.DataFrame(
    columns = ['Source', 'Title', 'Price', 'Draw', 'Raw_text', 'N_images', 'Images'],
    index = [i['item'].lot_index_ for i in all_lots.values()],
    data = {
        'Source': [i['url'] for i in all_lots.values()],
        'Title': [i['item'].title_ for i in all_lots.values()],
        'Price': [i['item'].price_ for i in all_lots.values()],
        'Draw': [i['item'].draw_ for i in all_lots.values()],
        'Raw_text': [i['item'].text_ for i in all_lots.values()],
#         'Images': [
#             [re.sub('\/catalog((us)|(i))','',baseurl) + jpg for jpg in i['item'].images] 
#             for i in all_lots.values()
#         ],
        'Images': [
            [re.search(r'^http://.*?/',URL)[0] + jpg[1:] for jpg in i['item'].images_] # [1:] remove leading "/"
            for i in all_lots.values()
        ]
    }
)
out.N_images = out.Images.apply(len)
out.loc[:, 'lot_counter'] = all_lots.keys()

out

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# ran when auction was still open
if (sum(out.Price == -1) / out.shape[0] > 0.8):
    # add "without-price" to file name
    NO_PRICE = True
else:
    NO_PRICE = False

file_name = f'{DATA_DIR}/auctions/temp-results/drz-data-unparsed-{auction_month}-{month_counter}.pkl'
if NO_PRICE:
    file_name = file_name.replace('auctions/temp-results', 'auctions/without-price')
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')

if do_save(file_name):
    print(f'Save to {file_name}.')
    out.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings. (method: {SAVE_METHOD})')

# %% [markdown]
# <a href="#auct_top" id='auct_regex'><font size=+1><center>^^ TOP ^^</center></font></a>
#
# ---

# %% [markdown]
# # In depth parsing
# Use `Raw_text` as input.  
# Modify regex files if fragment is not recognized.
#

# %%
# Read regex patterns
import read_regex_patterns

read_regex_patterns.read_tag_value(path=REGEX_DIR+'/')
tags, flagtags, repfragments = read_regex_patterns.read_all(path=REGEX_DIR+'/')

# Replace dataframe stored in memory with dataframe that was just saved to disk.
file_name = f'{DATA_DIR}/auctions/temp-results/drz-data-unparsed-{auction_month}-{month_counter}.pkl'
if NO_PRICE:
    file_name = file_name.replace('auctions/temp-results', 'auctions/without-price')
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
out = pd.read_pickle(file_name)

# # NB This might fail if "drz-data-unparsed-{auction_month}.pkl" does not exist because price is not available yet and ran when auction was still open.
# # It is safe to continue with the dataframe that is still in memory
# file_name = file_name.replace('.pkl', '-without-price.pkl')
# out = pd.read_pickle(file_name)


# %%

if '2022-02-4006' in out.index:
    out.drop('2022-02-4006', inplace=True) # page is empty
if '2024-07-7158' in out.index:
    out.drop('2024-07-7158', inplace=True) # has pictures (Audi A1) and a 4400 price, but nothing more.


# %% [raw]
# file_name = '/home/tom/data/satdatsci-data-link/auctions/temp-results/drz-data-unparsed-2024-03-06.pkl'; OPBOD=True
# out = pd.read_pickle(file_name)
# VERBOSE = 1
# out, out.Raw_text[0]

# %% tags=["nbconvert_instruction:remove_all_outputs"]
# parse raw text
for IX in out.index :
    
    # find info
    
    rt = out.loc[IX,"Raw_text"]
    
    # Trim auction results (price) from raw_text
    if OPBOD:
        M1 = re.match(r'\s*\u20ac *([0-9,.]*\,[0-9]{2})', rt[0])
        M2 = re.match(r'\(excl\. alle eventuele bijkomende kosten en belastingen\)', rt[1])
        if (M1 is not None) and (M2 is not None):
            rt = rt[2:]
        else:
            if VERBOSE > 2:
                print(M1, M2, rt)
                print('skip trimming price')
    
    # first line:
    Val = rt.pop(0) 

    # Is first line something else?
    if Val == 'Na loting':
        Val = rt.pop(0) # val is now kavelnr
        out.loc[IX,"Draw"] = True
    else:
        out.loc[IX,"Draw"] = False
    if Val == 'Niet gegund':
        Val = rt.pop(0) # val is now kavelnr
        assert out.loc[IX,"Price"] == 0
    
    # when lot number is followed by an asteriks there is a note
    if Val.endswith('*\r'):
        Val = Val[0:-2]
        out.loc[IX,"Note"] = True
    else :
        Val = Val.strip()
        out.loc[IX,'Note'] = False
        
    if VERBOSE>0:
        print(Val)

    # store lot nr        
    out.loc[IX,"LotNr"]=Val
    
    
    # second line
    out.loc[IX,"LotType"]=rt.pop(0).strip()


    # third line
    Val = rt.pop(0).strip()
    # This line is brand or optional line with type of lot
    # All caps is brand
    
    # starts with 'Merk BRANDNAME'
    if Val.startswith('Merk '):
        Val = re.sub(r'^Merk ', '', Val)
        
    # It is not brand name. Add this Val to LotType
    if Val in [
        'Quad','Kampeerwagen/ camper','Pleziervaart motorvaartuig met opbouw en open kuip','Rubberboot','Kampeerwagen / camper'
    ] or not Val.isupper():
        out.loc[IX,"LotType"] += ''.join([' (' + Val + ')'])
        if VERBOSE>0:print(Val, out.loc[IX,"LotType"])
        if rt[0].isupper():
            Val = rt.pop(0).strip() # next line is now brand name
        else:
            Val = ''
        
    out.loc[IX,"ItemBrand"]=Val

    
    
    # escape characters, repair typos and translate 
    for i in range(len(rt)):
        
        # encode string as bytes
        rt[i] = rt[i].encode('ascii',errors='xmlcharrefreplace')
        
        # replace text
        for pat,sub in zip(repfragments.Pattern,repfragments.Replace):
            rt[i] = re.sub(pat.encode('ascii',errors='xmlcharrefreplace'),sub.encode('ascii',errors='xmlcharrefreplace'),rt[i])
        
        # decode back to string, but special characters escaped to xml
        rt[i]=rt[i].decode('ascii')

    # Pull value after trailing or leading pattern (bgntag/endtag)
    for Tag,Field in zip(tags.Pattern,tags.Field):
        M = re.search(Tag,'\n'.join(rt))
        if M:
            Val = M.group('val')
            if VERBOSE>2:
                print('\t' + str(Field) + ' : ' + M.group(0).replace('\n','[newline]') + '\n\t' + '|' + Val + '|')
            # remove pattern and make rt a list again.
            rt = '\n'.join(rt).replace(M.group(0),'').split('\n')
        else:
            Val = ''
        out.loc[IX,Field] = Val        

    # Pattern in full text? (flagtag)
    for Tag,Field in zip(flagtags.Pattern,flagtags.Field):
        # flagtags might occur more than once, hence a list of finditer results
        Ms = list(re.finditer(Tag,'\n'.join(rt)))    
        if Ms:
            Val = True
            for M in Ms:
                if VERBOSE>2:
                    print('\t' + str(Field) + ' : ' + M.group(0).replace('\n','[newline]') + '\n\t' + '|' + str(Val) + '|')
                # remove pattern and make rt a list again.
                rt = '\n'.join(rt).replace(M.group(0),'').split('\n')
        else:
            Val = False
        out.loc[IX,Field] = Val

        
        
    # loop trough remaining lines

    for line in rt:
               
        # do comparison in bytes
        line = line.encode('ascii',errors='xmlcharrefreplace')
        if VERBOSE>2:
            print(f'\tremaining : {line}')
            
        # parsing
        isParsed = False # some accounting: in the end this line should be parsed
         
        # line is empty.. skip .. next
        if not line :# empty
            isParsed = True
            continue
            
        # line starting with '*' is a note
        if out.loc[IX,'Note'] and line.startswith(bytes('*','ascii')):
            if VERBOSE>2:
                print('\tNote:',end='')
                print(out.loc[IX,'Note'],end='')
                print(line)
            Val = line[1:].decode('ascii')
            out.loc[IX,'Note'] = Val
            isParsed = True
            continue
        elif line.startswith(bytes('*','ascii')):
            Val = line[1:].decode('ascii')
            if Val.lower() in ['kavel is vervallen.', 'kavel vervallen.', 'deze kavel ']:
                if VERBOSE>2:
                    print('\tNote:',end='')
                    print(out.loc[IX,'Note'],end='')
                    print(line)
                out.loc[IX,'Note'] = Val
                isParsed = True
                continue            
            elif VERBOSE>2:
                print('Is this line not a NB?')
                print(line)
                raise
                
        if isParsed == False:
            line = line.decode('ascii')
            
            # create empty string if not exist
            if (
                'SupInfo' not in out.loc[IX].index
            ) or (
                (
                    not isinstance(out.loc[IX,'SupInfo'], str)
                ) and (
                    pd.isna(out.loc[IX,'SupInfo'])
                )
            ):
                out.loc[IX,'SupInfo'] = ''
            out.loc[IX,"SupInfo"] = '\n'.join([out.loc[IX,'SupInfo'] , str(line)])
            if ('prev_ix' in locals()) and (IX == prev_ix):
                print(''.join([' '] * len(IX)), end='')
            else:
                print(str(IX), end='')
            print(f'[{line:s}]')
            prev_ix = str(IX)
            


# %% [markdown]
# <a href="#auct_top" id='auct_save'><font size=+1><center>^^ TOP ^^</center></font></a>
#
# ---

# %% [markdown]
# # Save results to disk

# %% tags=["nbconvert_instruction:remove_all_outputs"]
file_name = f'{DATA_DIR}/auctions/results/drz-data-{auction_month}-{month_counter}.pkl'
if NO_PRICE:
    file_name = file_name.replace('auctions/results', 'auctions/without-price')
    file_name = file_name.replace('.pkl', '-without-price.pkl')
if OPBOD:
    file_name = file_name.replace('.pkl', '-opbod.pkl')
if do_save(file_name):
    print(f'Save to {file_name}.')
    out.to_pickle(file_name)
else:
    print(f'Skip. {file_name} exists or saving is disabled in settings.')


# %% [markdown]
# # Next: add rdw data
#
# Because rdw data changes constantly it is advisable to run the notebook that adds rdw data to the above results soon.
