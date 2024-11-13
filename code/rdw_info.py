import pandas as pd
import numpy as np
import re
from IPython.display import display

def get_apis_with_search(query):

    import re

    # Get dataset by querying open data site
    resp = web_request(
        'https://data.overheid.nl/data/api/3/action/package_search', 
        {'q': query, 
        'rows':1001 #upper limit is 1000
        }
    )
    tgk = resp.json()

    # Check result
    if not tgk['success']:
        print(resp.url)
        print(tgk)
        raise RuntimeError('API function raised an exception.')
    n_tgk = tgk['result']['count']
    if len(tgk['result']['results']) != n_tgk:
        print(resp.url)
        raise OverflowError(f"Number of results is expected to be {n_tgk}, but is in fact {len(tgk['result']['results'])}")
    if n_tgk == 0:
        print(resp.url)
        raise OverflowError(f"Number of results is expected to more than 0")
    
    # Retrieve url from results
    api_urls = [r['url'] if 'url' in r else r['identifier'] for r in tgk['result']['results']]
    # Retrieve name and trim first part of title
    api_full_names = [r['title'] for r in tgk['result']['results']]
    # Get api_names (like "m9d7-ebf2")
    patterns = [
        '^https://opendata.rdw.nl/d/(.*)$',
    ];
    # try different regexp patterns, stop when all are successfull
    for pattern in patterns:  
        api_names = [re.findall(pattern, url) for url in api_urls]        
        if all([len(itm) > 0 for itm in api_names]):
            api_names = [n[0] for n in api_names]
            break
    
    return api_names, api_full_names, api_urls

def get_sub_apis(df):
    
    import re
    
    # get names of columns
    if isinstance(df.columns[0], tuple):
        # if column is tuple get first value
        column_names = df.columns.map(lambda x: x[0])
    else:
        column_names = df.columns

    # Name and url of all api_ columns
    isapi = column_names.str.startswith('api_')
    if any(isapi) == False:
        # There are no api columns
        return
    api_full_names = column_names[isapi].values
    api_urls = df.loc[:, isapi].ffill(axis=0).iloc[-1,:].values

    # Drop duplicates
    api_full_names, api_urls = np.unique(np.array([api_full_names, api_urls], dtype=str), axis=1)
    
    # Extract api_name
    patterns = [
        '.*resource/(.*)\.json$',
        '.*\/(.+?)\/?$'
    ]    
    # try different regexp patterns, stop when all are successfull
    for pattern in patterns:  
        api_names = [re.findall(pattern,url) for url in api_urls]        
        if all([len(itm) > 0 for itm in api_names]):
            api_names = np.array([n[0] for n in api_names])
            break
            
    return list(api_names), list(api_full_names), list(api_urls)

def web_request(url, params):
    
    import requests
    
    resp = requests.request('GET', url, params=params)
    
    if resp.status_code != 200:
        print(f'\n{url}\n{params}\nStatus: {resp.status_code}')
    
    return resp

def soda_request(api_url, token, params):
    
    import requests
    
    # if single reg this works too:  
    # params={'kenteken': reg}
    
    resp = requests.request('GET', api_url, headers={'X-App-Token': token}, params=params)
    
    if resp.status_code != 200:
        print(f'\n{resp.url}\nStatus: {resp.status_code}')
    
    return resp

def long_to_short_conf(long_codes):

    '''
    Convert short conformity code to long code
    Example 
        long: typegoedkeuringsnummer       = e4*2007/46*0996*04
        short: eu_type_goedkeuringssleutel = e4*07/46*0996*04
    Example: e11*2007/2046*0004*02
    src: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:31992L0053&from=en
    APPROVAL CERTIFICATE NUMBERING SYSTEM 
    1. In the case of an approval for a system, component or separate technical unit: the number consists of five sections separated by the '*' character:
        Section 1: the lowercase letter 'e' followed by the distinguishing letter(s) or number of the Member States issuing the approval:
            1 Germany,
            2 France,
            3 Italy,
            4 the Netherlands,
            5 Zweden
            6 Belgium,
            7 Hongarije
            8 Tjechie
            9 Spain,
            10 --
            11 the United Kingdom,
            12 Oostenrijk
            13 Luxembourg,
            14 --
            15 --
            16 --
            17 Finland
            18 Denmark,
            19 Roemenie
            20 Polen
            21 Portugal,
            22 --
            23 Griekenland
            24 Ierland
            25 --
            26 Slovenie
            27 Slowakije
            28 --
            29 Estland
            30 --
            31 --
            32 Letland
            33 --
            34 Bulgarije
            35 --
            36 Litouwen
            37 --
            ..
            49 Cyprus
            50 Malta
            EL Greece,
            IRL Ireland.
        (Section 2: the number of the base Directive.)
        Section 3: the number of the latest amending Directive applicable to the approval. Should a Directive contain different implementation dates referring to different technical standards, an alphabetical character is to be added. This charracter will refer to the specific technical requirement on the basis of which type-approval was granted.
        Section 4: a four-digit sequential number (with leading zeros as applicable) to denote the base approval number. The sequence starts from 0001 for each base Directive.
        Section 5: a two-digit sequential number (with a leading zero if applicable) to denote the extension. The sequence starts from 01 for each base approval number.
    2. In the case of an approval for a vehicle Section 2 is omitted.
    3. Example of the third approval (with, as yet, no extension) issued by France to the braking Directive:
        e2*
        71/320*
        88/194*
        0003*
        00
        or in the case of a Directive with two implementation stages A and B.
        e2*
        88/77*
        91/542A*
        0003*
        00 
    4. Example of the second extension to the fourth vehicle approval issued by the United Kingdom:
        e11*
        91/???*
        0004*
        02.

    Resume for vehicles
    1: Country - "e" followed by country code issuing the type.
        e11* is the United Kingdom.
    2: Regulation no. - omitted
    3: Amending body - Number of the last amending directive or regulation. 
        *2007/2046* is an approval under Commission Regulation No. 2007/2046.
    5: Sequence - Four-digit sequential number designating the base approval number. The sequence starts from 0001 for each basic directive or regulation. 
        *0004* the 4th type-approval.
    5: Extension - Two-digit sequential number to designate the extension of type approval. The sequence starts from 00 for each base approval number. 
        *02 the 2nd extension of approval.

    Before this was done by using a lookup table available by querying 55kv-xf7m, but this table no longer exist as of March 2024.
    Here we simply split the code and remove the trailing milenium.
    '''   

    # select codes with correct format 
    func = lambda x:  3==(len(re.findall('\*', x)) if isinstance(x,str) else -1)
    sel = [func(c) for c in long_codes]

    # split codes
    func = lambda x: x.split('*')
    sections = [func(c) if s else 4*[''] for c,s in zip(long_codes,sel) ]

    # Prepare output
    out = pd.DataFrame(index = long_codes, columns=[f'eu_approval_no_section{i}' for i in [1, 3, 4, 5]], data=sections)

    # *2001/116* -> *01/116* 
    # *2007/46* -> *07/46*
    # *2018/858* -> *18/858*
    out.replace({'eu_approval_no_section3': r'^20([0-9][0-9]/)'}, r'\1', regex=True, inplace=True)
    # *168/2013* -> *168/13*
    out.replace({'eu_approval_no_section3': r'/20([0-9][0-9])$'}, r'/\1', regex=True, inplace=True)
    # *KS07/46* -> *07E46*
    out.replace({'eu_approval_no_section3': r'^KS([0-9][0-9])/'}, r'\1E', regex=True, inplace=True)

    # add concatenated to dataframe
    out['eu_type_goedkeuringssleutel'] = out.apply(lambda x: x.str.cat(sep='*'), axis=1)
    
    return out

def long_to_short_conf_v0(long_codes):
    
    '''
    Convert short conformity code to long code by querying 55kv-xf7m
    '''   
    # Prepare output
    out = pd.DataFrame(index = long_codes)

    # Query short and long fields
    flds = [
        'eu_type_goedkeuringssleutel',
        'typegoedkeuringsnummer',
    ]

    # Create query
    codes = '%27' + '%27,%27'.join(long_codes) + '%27'
    flds = ','.join(flds)
    q = f"select={flds}%20where%20typegoedkeuringsnummer%20in%20({codes})"
    url = r"https://opendata.rdw.nl/resource/55kv-xf7m.csv?$" + q

    try:
        # Perform query
        table = pd.read_csv(url, sep=',', header=0, index_col=None, dtype=str)
        # Some have duplicate, sort alphabetically
        table = table.sort_values(by='eu_type_goedkeuringssleutel', ascending=False).groupby('typegoedkeuringsnummer').first()
        # Add to output
        out = out.merge(table, how='left', right_on='typegoedkeuringsnummer', left_index=True)
        # When no result return input
        out = out.reset_index().ffill(axis=1).set_index('typegoedkeuringsnummer')
    except:
        print(url)
        raise
    
    return out.drop(columns='index')

def get_metadata(api_name, token=''):
    
    # get info from "view" api
    api_url = f'https://opendata.rdw.nl/api/views/{api_name}.json'
    resp = soda_request(api_url, token, '')
    metadata = resp.json()

    # create basic dataframe
    # part 1: column information
    column_info = metadata.pop('columns')
    # part 2: column content information
    contents = [i.pop('cachedContents') if 'cachedContents' in i.keys() else {} for i in column_info]
    # combine
    md = pd.concat([pd.DataFrame(column_info), pd.DataFrame(contents)], axis=1, keys=['field_info', 'field_content'])
    
    # set remaining fields as attributes of dataframe 
    md._attrs = metadata


    # typecast
    cast_as = {
        ('field_info', 'position'): int,
        ('field_info', 'width'): 'Int64',
        ('field_content', 'non_null'): 'Int64',
        ('field_content', 'not_null'): int,
        ('field_content', 'null'): 'Int64',
        ('field_content', 'count'): 'Int64',
        ('field_content', 'cardinality'): 'Int64',
        ('field_content', 'average'): float,
        ('field_content', 'sum'): float,
    }
    for fld,dtype in cast_as.items():
        if fld not in md.columns:
            # print(f'skip {fld}, because it is not in metadata of {api_name}')
            continue
        type_casted = md.loc[:,fld].astype(dtype)
        del md[fld] # to avoid "dtype incompatible" warnings
        md.loc[:,fld] = type_casted
        

    # set index as field name (column name)
    md.set_index(('field_info','fieldName'), inplace=True)
    md.index.name='fieldName'

    # low cardinality could point to categorical data (factors)
    # create a new empty "object" column
    md.loc[:, ('field_content', 'factors')] = pd.Series(index=md.index, dtype='object', data=np.NaN) 
    
    if ('field_content', 'cardinality') not in md:
        # there is no cardinality info stop here
        return md

    n_category_max = max(md.loc[:, ('field_content', 'top')].apply(lambda x: len(x) if isinstance(x, list) else x)) # default max is twenty top observations
    is_cat = (md.loc[:, ('field_content', 'cardinality')] < n_category_max) & (md.loc[:, ('field_content', 'cardinality')] > 1) # 19 or less indicates category
    is_str = md.loc[:, ('field_info', 'dataTypeName')] == 'text'
    is_num = md.loc[:, ('field_info', 'dataTypeName')] == 'number'
    
    # string categories
    factors = md.loc[is_cat&is_str, ('field_content', 'top')].apply(lambda x: [i['item'] for i in x])
    factors.name = ('field_content', 'factors')
    md.update(factors)
    
    # integer categories
    uniq_values = md.loc[is_cat&is_num, ('field_content', 'top')].apply(lambda x: [(i['item']) for i in x])
    is_int = is_num.copy()
    is_int &= uniq_values.apply(lambda x: all([v.isnumeric() for v in x]))
    factors = uniq_values[is_int].apply(lambda x: [int(v) for v in x])
    factors.name = ('field_content', 'factors')
    md.update(factors)
    
    # counters (range)
    is_cnt = is_int.copy()
    is_cnt &= md.loc[is_int, ('field_content', 'factors')].apply(lambda x: max(x) == (min(x) + len(x)-1))
    factors = md.loc[is_cnt, ('field_content', 'factors')].apply(lambda x: range(min(x), max(x)+1))
    factors.name = ('field_content', 'factors')
    md.update(factors)

    # output
    assert (md.loc[:, [('field_info', 'renderTypeName'), ('field_info', 'dataTypeName')]].nunique(axis=1)==1).all()
    out = md.copy()

    return out

class RdwInfo:
    
    '''
    Get information from RDW by querying on fields such as registrations
    
    Input:
    idx:      registration    <list>, <string> Example idx='aa-bb-11'
    api_name: api name (code) <string>         Example api_name='m9d7-ebf2'
    key:      token for app   <string>         Default key=None
    '''
    
    
    def __init__(self, idx, api_name, key=None):

        # Handle input
        
        self.idx_ = idx
        self.api_name_ = api_name
        self._key = key
        self.set_api_url(api_name)

        # Initialize fields
        
        self.metadata_ = dict()
        self.set_metadata(api_name)
        
        # Results are tall. Pivot on these columns to have 1 obs per row
        self.metadata_['pivot_columns'] = {
            '3huj-srit': 'as_nummer',
            '8ys7-d773': 'brandstof_volgnummer',
            'gr7t-qfnb': ['volgnummeraandrijving', 'volgnummerenergiebron'],
            'vezc-m2t6': 'carrosserie_volgnummer',
            'jhie-znh9': ['carrosserie_volgnummer', 'carrosserie_voertuig_nummer_code_volgnummer'],
            'kmfi-hrps': ['carrosserie_volgnummer', 'carrosserie_klasse_volgnummer'],
            'sgfe-77wx': ['meld_datum_door_keuringsinstantie_dt', 'soort_erkenning_keuringsinstantie'],
            'a34c-vvps': ['meld_datum_door_keuringsinstantie_dt', 'gebrek_identificatie'],
            'sghb-dzxx': ['montagedatum', 'demontagedatum'],
            'ahsi-8uyu': 'asnummer',
            'xhyb-w7xt': 'volgnummeras', # As Uitvoering
            'q7fi-ijjh': ['carrosserie_volgnummer', 'carrosserie_klasse_volgnummer'],
            'w2qp-idms': 'carrosserie_volgnummer',
            'ky2r-jqad': ['volgnummercarrosserietype'],
            'nypm-t8hx': ['carrosserie_volgnummer', 'carrosserie_uitvoering_numeriek_volgnummer'],
            'mdqe-txpd': 'volgnummer',
            'x5v3-sewk': 'volgnummerhandelsbenamingfabr', # Handelsbenaming Fabrikant
            'fj7t-hhik': 'merkcode', 
            'kyri-nuah': 'volgnummermerk',
            'g2s6-ehxa': 'volgnummer',
            '4by9-ammk': 'volgnummeraandrijving',
            '5w6t-p66a': ['volgnummer','brandstof_volgnummer'], 
            'mt8t-4ep4': 'plaats_aanduiding_volgnummer',
            'h9pa-e9ta': 'subcategorie_uitvoering_volgnr',
            'm692-vvff': 'volgnummerspecialedoeleinden',
            '2822-t8sx': 'uitvgavenummer_verbruikboek',
            'r7cw-67gs': 'volgnummer',
            '7rjk-eycs': 'volgnummerversnelling',
            '3xwf-ince': 'rupsband_set_volgnr',
            'xn6e-huse': 'volgnummerrupsbandset',
            '2ba7-embk': 'subcategorie_voertuig_volgnummer',
            '7ug8-2dtt': 'bijzonderheid_volgnummer',
            't49b-isb7': 'referentiecode_rdw',
            'd3ex-xghj': 'volgnummerkoppeling', 
            '9s6a-b42z': 'volgnummerintrekkingtgk',


            }
        # Unique id per row
        # "*" means no index. These are reference tables.
        self.metadata_['primary_keys'] = {
            'm9d7-ebf2': 'kenteken',
            '3huj-srit': 'kenteken',
            '8ys7-d773': 'kenteken',
            'vezc-m2t6': 'kenteken',
            'jhie-znh9': 'kenteken',
            'kmfi-hrps': 'kenteken',
            'sgfe-77wx': 'kenteken',
            'a34c-vvps': 'kenteken',
            'sghb-dzxx': 'kenteken', 
            'vkij-7mwc': 'kenteken',
            '3xwf-ince': 'kenteken',
            '2ba7-embk': 'kenteken',
            '7ug8-2dtt': 'kenteken',
            't49b-isb7': 'kenteken', 
            '55kv-xf7m': 'eu_type_goedkeuringssleutel',
            'jqs4-4kvw': '*', #'code_toelichting_tellerstandoordeel',
            'hx2c-gt7k': '*', #'gebrek_identificatie',
            '5k74-3jha': '*', #'volgnummer',
            'v23s-d6km': '*', #'',
            'nmwb-dqkz': '*', #'volgnummer',
            'j9yg-7rg9': '*', #'referentiecode_rdw',
            'mh8w-8cup': '*', #'referentiecode_rdw',
            'mu2x-mu5e': '*', #'referentiecode_rdw',
            '9ihi-jgpf': '*', #'referentiecode_rdw',
            'ahsi-8uyu': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'],
            'wx3j-69ie': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'],
            'q7fi-ijjh': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'],
            'w2qp-idms': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'],
            'nypm-t8hx': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'],
            'mdqe-txpd': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'],
            'fj7t-hhik': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'],
            'g2s6-ehxa': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'],
            '5w6t-p66a': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'], 
            'mt8t-4ep4': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'], 
            'h9pa-e9ta': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'], 
            '2822-t8sx': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'], 
            'r7cw-67gs': ['eu_type_goedkeuringssleutel', 'eeg_variantcode', 'eeg_uitvoeringscode', 'uitvoering_wijzigingsnummer'], 
            'xhyb-w7xt': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 10 as_uitvoering
            'x5v3-sewk': ['typegoedkeuringsnummer', 'codevariantgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 4 Handelsbenaming Fabrikant
            'ky2r-jqad': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 6 carrosserie_uitvoering
            'gr7t-qfnb': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 3 Energiebron Uitvoering
            'd3ex-xghj': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 9 Koppeling Uitvoering
            'byxc-wwua': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 1 Basis Uitvoering
            'm692-vvff': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 7 Speciale Doeleinden
            'kyri-nuah': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 5 Merk Uitvoering
            '7rjk-eycs': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 8 Versnelling Uitvoering
            '4by9-ammk': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 2 Aandrijving Uitvoering
            'xn6e-huse': ['typegoedkeuringsnummer', 'codevarianttgk', 'codeuitvoeringtgk', 'volgnummerrevisieuitvoering'], # 11 Rupsbandset Uitvoering
            '9s6a-b42z': 'typegoedkeuringsnummer', # 12 Intrekking Typegoedkeuring
            }
        if (api_name in self.metadata_['primary_keys']) and (self.metadata_['primary_keys'][api_name] == 'kenteken'):
            self.clean_reg() # Capitals and no fillers

    
    def __str__(self):
        
        # When print() is called on object
        
        out = 'Class contains'
        for fld in dir(self):
            if fld.startswith('_'):
                # ignore _fields
                continue
                
            def val_field(name, val):
                out = ''
                if ('shape' in dir(val)) and not isinstance(val, np.str_):
                    out += '\n\t' + f'{name} {type(val)}:\n\t\tshape={val.shape}'
                elif isinstance(val, list):
                    out += '\n\t' + f'{name} {type(val)}:\n\t\tlen={len(val)}'
                elif isinstance(val, dict):
                    out += '\n\t' + f'{name} {type(val)}:\n\t\tcontains fields {list(val.keys())}'
                elif isinstance(val, str):
                    if len(val) > 60:
                        out += '\n\t' + f'{name} {type(val)}:\n\t\t{val[:30]} .. {val[-30:]}'
                    else:
                        out += '\n\t' + f'{name} {type(val)}:\n\t\t{val}'
                else:
                    out += val_field(name, val.__repr__())
                return out
                
            if fld.endswith('_'):
                # print fields_
                val = getattr(self, fld)
                out += val_field(fld, val)
        
            if fld=='metadata_':
                for subfld in getattr(self, fld).keys():
                    if subfld in ['primary_keys', 'pivot_columns']:
                        api_name = self.api_name_
                        d =  getattr(self, fld)[subfld]
                        if api_name not in d.keys():
                            val = '-empty-'
                        else:
                            val = d[self.api_name_]
                        out += val_field(f'{fld}.{subfld}["{self.api_name_}"]', val)
                    else:
                        val = getattr(self, fld)[subfld]
                        out += val_field(f'{fld}.{subfld}', val)

        return out


    # Helper functions
    
    def clean_reg(self):
        if isinstance(self.idx_, str):
            self.idx_ = [self.idx_]
        # upper case without fillers
        self.idx_ = [r.replace('-','').upper() for r in self.idx_]

    # Setters
    
    def set_key(self, key):
        self._key = key
    def set_api_name(self, api_name):
        self.api_name_ = api_name
        # start over
        self.set_metadata(api_name)
        self.set_api_url(api_name)
        for fld in ['data_', '_resp', 'resp_status_']:
            if hasattr(self, fld):
                delattr(self, fld)

    def set_api_url(self, api_name, output_format='json'):
        # output_format: CSV, JSON, XML, GeoJSON, RDF-XML
        url = f'https://opendata.rdw.nl/resource/{api_name}.{output_format}'
        self.api_url_ = url
    def set_metadata(self, api_name):
        md = get_metadata(api_name)
        name = re.findall('^.*:\s(.*)$', md._attrs['name'])
        name = name[0] if isinstance(name, list) else ''
        self.metadata_['online'] = md
        self.metadata_['name'] = name
               
    # Getters
    
    def get_idx(self):
        return self.idx_
    def get_api_name(self):
        return self.api_name_
    def get_api_url(self, key):
        url = self.api_url_ 
        if key is not None:
            url += '?$$app_token={key}'
        return url
    def get_resp_status(self):
        if hasattr(self, 'resp_status_') == False:
            return None
        return self.resp_status_
    def get_resp(self):
        if self.get_resp_status() != 200:
            return self.query_api()
        return self._resp
    def get_header(self):
        resp  = self.get_resp()
        self.metadata_['header'] = resp.headers
        return resp.headers
    def get_df(self):
        if hasattr(self, 'data_') == False:
            self.query_to_df()
        return self.data_

    def get_dtypes_from_header(self):
        header = self.get_header()
        # response header fields can be eval-ed
        dtypes = dict(zip(
            eval(header['X-SODA2-Fields']), 
            eval(header['X-SODA2-Types']))
           )
        
        return dtypes
        
    def get_dtypes(self):
        # https://dev.socrata.com/docs/datatypes/
        # expand this dict if needed
        soda_to_python = {
            'text': str,
            'number': float,
            'floating_timestamp':'datetime64[ns]'
        }
        dtypes = self.get_dtypes_from_header()
        not_implemented = {k:v for k,v in dtypes.items() if v not in soda_to_python.keys()}
        if len(not_implemented) > 0:
            print(not_implemented)
            raise NotImplementedError(f'{len(not_implemented)} fields have SODA dtypes that cannot be converted to python dtypes.')

        return {k: soda_to_python[v] if v in soda_to_python.keys() else str for k,v in dtypes.items()}
    
    # Main methods
        
    def query_api(self):
        
        # Get info from api
        
        api_name = self.get_api_name()
        
        # Use different type of queries per api
        if api_name not in self.metadata_['primary_keys']:
            raise NotImplementedError(f'Api <{api_name}> has not primary_key listed in metadata. Please add.')

        if self.metadata_['primary_keys'][api_name] == 'kenteken':
            reg_list =  ','.join([f'"{r}"' for r in self.get_idx()])
        
            resp = soda_request(
                self.get_api_url(key=None), # key not in url use header
                self._key,
                {'$where': f'kenteken in ({reg_list})'}
            )
        elif self.metadata_['primary_keys'][api_name] == 'eu_type_goedkeuringssleutel':
            conf_list =  ','.join([f'"{r}"' for r in self.get_idx()])
            
            resp = soda_request(
                self.get_api_url(key=None), # key not in url use header
                self._key,
                {'$where': f'eu_type_goedkeuringssleutel in ({conf_list})'}
            )
        elif self.metadata_['primary_keys'][api_name] == 'typegoedkeuringsnummer':
            conf_list =  ','.join([f'"{r}"' for r in self.get_idx()])
            
            resp = soda_request(
                self.get_api_url(key=None), # key not in url use header
                self._key,
                {'$where': f'typegoedkeuringsnummer in ({conf_list})'}
            )
        elif isinstance(self.metadata_['primary_keys'][api_name], list):
            
            sep = '.' # separator between index fields

            idx = self.get_idx()

            # if primary key is a list of key we need to make a composite key
            assert idx.map(lambda x: sep not in x).all().all() # It could complicate things if sep is already present
            
            # make composite key 
            composite_key = idx.apply(lambda x: sep.join(x), axis=1)
            composite_keys = '"' + '","'.join(composite_key) + '"'

            # make a select statement that separates fields
            select_construct = f'||\'{sep}\'||'.join(self.metadata_['primary_keys'][api_name])
            q = f'*,{select_construct} as composite_key where composite_key in ({composite_keys})'
            
            # query
            resp = soda_request(
                self.get_api_url(key=None), # key not in url use header
                self._key,
                {'$select': q}
            )
        elif self.metadata_['primary_keys'][api_name] == '*':
            # get full table. This is a reference table
            resp = soda_request(
                self.get_api_url(key=None), # key not in url use header
                self._key,
                {'$limit': '50000'}
                )
            
        else:
            raise NotImplementedError(f'Api <{api_name}> has unrecognized primary_key: {self.metadata_["primary_keys"][api_name]}')

        self._resp = resp
        self.resp_status_ = resp.status_code
        
        return resp
    
    def query_to_df(self):
        
        resp = self.get_resp()
        
        # Dataframe from json from response
        df = pd.DataFrame.from_dict(resp.json(), dtype=str)
    
        self.data_ = df

    def assign_df_types(self):  
        df = self.get_df()
        # Header of response has dtypes
        dtypes = self.get_dtypes()
        for fld in df:
            df[fld] = df[fld].astype(dtypes[fld])
            
        self.data_ = df    
    
    def assign_df_index(self):                
        df = self.get_df()
        # Set primary key of df
        api_name = self.get_api_name()
        if df.shape[0] == 0:
            # df is empty
            return
        if self.metadata_['primary_keys'][api_name] == '*':
            # no index
            return

        df.set_index(self.metadata_['primary_keys'][api_name], inplace=True)

        self.data_ = df
        
    def perform_df_pivot(self):
        # input
        api_name = self.get_api_name()
        if api_name not in self.metadata_['pivot_columns']:
            # no pivot needed
            return
        df = self.get_df()
        if df.shape[0] == 0:
            # df is empty. skip
            return
        
        # columns to pivot on
        cols = self.metadata_['pivot_columns'][api_name]
        cols = [cols] if isinstance(cols, str) else cols
        prim_key = self.metadata_['primary_keys'][api_name]
        prim_key = [prim_key] if isinstance(prim_key, str) else prim_key # make list of one if it is a single string       
        
        # pivot
        
        # create df with unique rows
        df_uniq_idx = df.reset_index().set_index(prim_key + cols)
        assert df_uniq_idx.index.is_unique, f'During pivot in {api_name} {cols} were not enough to yield unique observations.'

        # rank values in pivot columns to get a sorted index number (0, 1, 2, ..) 
        for i, col in enumerate(cols):
            ranks = df_uniq_idx.reset_index().groupby(df.index)[col].apply(lambda x: x.rank(method='dense')).astype(int).astype(str)
            # Add to df_uniq_idx
            ranks.sort_index(level=-1, inplace=True)
            ranks.index = df_uniq_idx.index
            ranks.name = f'indexno{i}'
            df_uniq_idx = df_uniq_idx.join(ranks, how='left')

        # Save for output
        df = df_uniq_idx.reset_index().set_index(prim_key).pivot(columns=[f'indexno{i}' for i in range(len(cols))])
        df.columns = df.columns.map(lambda x: '_'.join(x).rstrip('_')) # flatten column names
        
        self.data_ = df
        
    def process_api(self):
        
        # Full flow
        self.query_to_df()
        self.assign_df_types()
        self.assign_df_index()
        self.perform_df_pivot()
        # Add timestamp
        header = self.get_header()
        df = self.get_df()
        df['TimeStamp'] = pd.to_datetime(header['Date'])
        self.data_ = df
        
        assert df.index.is_unique


class OviInfo:
    '''
    Get information from OVI RDW by scraping site
    
    Input:
    idx:      registration    <list>, <string> Example idx='aa-bb-11'
    '''
    

    
    def __init__(self, idx, verbose=1):

        # Handle input
        
        self.idx_ = idx
        self.verbose_level_ = verbose
        self._url = 'https://ovi.rdw.nl/'
        self.clean_reg() # Capitals and no fillers
        self.data_ = pd.DataFrame()
        self.metadata_ = dict()
        self.current_reg_ = self.idx_[0]
        
        
    def __str__(self):
        
        # When print() is called on object
        
        out = 'Class contains'
        for fld in dir(self):
            if fld.startswith('_'):
                # ignore _fields
                continue
                
            def val_field(name, val):
                out = ''
                if ('shape' in dir(val)) and not isinstance(val, str):
                    out += '\n\t' + f'{name} {type(val)}:\n\t\tshape={val.shape}'
                elif isinstance(val, list):
                    out += '\n\t' + f'{name} {type(val)}:\n\t\tlen={len(val)}'
                elif isinstance(val, dict):
                    out += '\n\t' + f'{name} {type(val)}:\n\t\tcontains fields {list(val.keys())}'
                elif isinstance(val, str):
                    if len(val) > 60:
                        out += '\n\t' + f'{name} {type(val)}:\n\t\t{val[:30]} .. {val[-30:]}'
                    else:
                        out += '\n\t' + f'{name} {type(val)}:\n\t\t{val}'
                else:
                    out += val_field(name, val.__repr__())
                return out
                
            if fld.endswith('_'):
                # print fields_
                val = getattr(self, fld)
                out += val_field(fld, val)
        
            if fld=='metadata_':
                for subfld in getattr(self, fld).keys():
                    if subfld in ['primary_keys', 'pivot_columns']:
                        api_name = self.api_name_
                        d =  getattr(self, fld)[subfld]
                        if api_name not in d.keys():
                            val = '-empty-'
                        else:
                            val = d[self.api_name_]
                        out += val_field(f'{fld}.{subfld}["{self.api_name_}"]', val)
                    else:
                        val = getattr(self, fld)[subfld]
                        out += val_field(f'{fld}.{subfld}', val)

        return out
    
    
    # Helper functions
    
    def clean_reg(self):
        if isinstance(self.idx_, str):
            self.idx_ = [self.idx_]
        # upper case without fillers
        self.idx_ = [r.replace('-','').upper() for r in self.idx_]
    
    def check_ovi_status(self):
        
        from time import sleep
        
        TIME_OUT = 60 # seconds        

        tree = self.get_tree()
        reg = self.get_current_reg()
        
        
        ERROR = len(tree.xpath('//*[@action="FoutPagina.aspx?error=ErrorBlocked"]')) == 1
        warn_text = tree.xpath('//*[@class="warning"]//text()')
        WARNING_NA = (len(warn_text) > 0) and (
            (warn_text[0].startswith(f'Er zijn geen gegevens gevonden voor het ingevulde kenteken {reg.upper()}.')) or \
            (warn_text[0].startswith(f'{reg.upper()} is geen geldig kenteken.'))
        )

        # return result
        if ERROR:
            # pause
            msg = tree.xpath('//*[@class="text-red"]')[0].text
            if self.verbose_level_ > 2:
                print(msg)
            if self.verbose_level_ > 1:
                print(f'time out {TIME_OUT}s')
            self.reset_resp()
            sleep(TIME_OUT)
            return self.check_ovi_status() # try again (recursive)
        elif WARNING_NA:
            return '\n'.join(warn_text)
        
        return 'ok'
        
    def update_progress(self, values, disp_id=None, ncol = 10):
        last_row = len(values)%ncol
        pad = ncol - last_row if last_row > 0 else 0
        values += ['']*pad
        df = pd.DataFrame(np.reshape([values],(-1, ncol)))
        df.index=[f'{i*ncol}-{(i+1)*ncol-1}' for i in range(df.shape[0])]
        df.index.name='items'
        if disp_id is None:
            disp_id = display(df, display_id=True)
        else:
            disp_id.update(df)
        return disp_id
        
    # Getters 
    
    def get_resp_status(self):
        if hasattr(self, 'resp_status_') == False:
            return None
        return self.resp_status_
    def get_resp(self):
        if self.get_resp_status() != 200:
            return self.query_web()
        return self._resp
    def get_header(self):
        resp  = self.get_resp()
        self.metadata_['header'] = resp.headers
        return resp.headers
    def get_tree(self):
        if hasattr(self, 'tree_') == False:
            self.query_to_tree()
        return self.tree_
    def get_current_reg(self):
        return self.current_reg_ 

        
    # Setters
    
    def set_field_content(self, reg_data, field):
        
        # Get content from field
        reg = self.get_current_reg()
        tree = self.get_tree()
        txt = tree.xpath(f'//*[@id="{field}"]/text()')
        
        if len(txt) != 1:
            content = ''
        else:
            content = txt[0]
        if content in ('Niet geregistreerd'):
            content = ''
            
        # try:
        #     content = bytes(content, 'utf-8').decode('utf-8')
        # except:
        #     print(field, txt)
            
        
        # Set content
        reg_data[field] = content
        return reg_data
    
    def add_reg_to_data(self):
        
        reg = self.get_current_reg()
        fields = self.current_fields()
        reg_data = pd.Series(dtype='object', name=reg)
        for field in fields:
            reg_data = self.set_field_content(reg_data, field)
        
        # Add to main dataframe
        if self.data_.shape[0] == 0:
            self.data_ = reg_data.to_frame().T
        else:
            self.data_ = pd.concat([self.data_.T, reg_data], axis=1).T
        
        # go to next
        self.to_next_reg()
        return True
        
    def to_next_reg(self):
        
        self.reset_resp()
        for reg in self.idx_:
            if reg in self.data_.index:
                reg = None # if last, exit with None
                continue
            break
        self.current_reg_ = reg
        
    def reset_resp(self):
        delattr(self, 'tree_')
        self.resp_status_ = None
         
    def current_fields(self):
        
        tree = self.get_tree()
        elements = tree.xpath('//*[@class="ui-block-d border ovigrid"]') + tree.xpath('//*/div[@class="ui-block-d ovigrid"]')
        fields = [el.attrib['id'] for el in elements if 'id' in el.keys()]
        return fields
  
    
    def query_web(self):
        
        reg = self.get_current_reg()
        resp = web_request(self._url, params = {'kenteken': reg})
        self._resp = resp
        self.resp_status_ = resp.status_code
        msg = self.check_ovi_status()
        if self.verbose_level_ > 4:
            print(msg)

        return self._resp
    
    def query_to_tree(self):
        
        from lxml import html

        resp = self.get_resp()
        tree = html.fromstring(resp.content)
        self.tree_ = tree
        
    def process_api(self):
        
        # Full flow
        
        if self.verbose_level_ > 0:
            delta = np.timedelta64(int(np.ceil(len(self.idx_)/30) * (60 + 10)), 's')
            print(f"This takes approximately {np.timedelta64(delta, 'm').astype(int)} minutes. Done by {(pd.Timestamp('now') + delta).strftime('%H:%M:%S')}.")
            progress = list(self.idx_.copy())
            disp_id = self.update_progress(progress, disp_id=None)
            c = 0
        while self.get_current_reg() is not None:
            self.add_reg_to_data()
            if 'disp_id' in locals():
                fld = self.data_.iloc[-1,:]
                progress[c] = f'[{sum((fld!="") & fld.notna())}/{sum(fld.notna())}]{fld.name}'
                disp_id = self.update_progress(progress, disp_id)
                c=c+1

            
            

        if 'disp_id' in locals():
            self.update_progress(progress + ['done'], disp_id)

        # Add timestamp
        header = self.get_header()
        self.data_['TimeStamp'] = pd.to_datetime(header['Date'])
        
        assert self.data_.index.is_unique    

if __name__ == "__main__":
    # Example
    import assets.hidden_api_keys as hidden_api_keys
    main_api = 'm9d7-ebf2'
    Car = RdwInfo('62-sf-fg', main_api, hidden_api_keys.socrata_apptoken)
    print(Car)
    Car.process_api()
    print(Car.get_df().to_markdown())
else:
    print(f'enjoy {__name__}')
