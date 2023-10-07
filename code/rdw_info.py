import pandas as pd
import numpy as np
import re
from IPython.display import display

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
        print(f'\n{url}\nStatus: {resp.status_code}')
    
    return resp

def soda_request(api_url, token, params):
    
    import requests
    
    # if single reg this works too:  
    # params={'kenteken': reg}
    
    resp = requests.request('GET', api_url, headers={'X-App-Token': token}, params=params)
    
    if resp.status_code != 200:
        print(f'\n{api_url}\nStatus: {resp.status_code}')
    
    return resp

def long_to_short_conf(long_codes):
    
    '''
    Convert short conformity code to long code
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

    # Perform query
    table = pd.read_csv(url, sep=',', header=0, index_col=None, dtype=str)
    # Some have duplicate, sort alphabetically
    table = table.sort_values(by='eu_type_goedkeuringssleutel', ascending=False).groupby('typegoedkeuringsnummer').first()
    # Add to output
    out = out.merge(table, how='left', right_on='typegoedkeuringsnummer', left_index=True)
    # When no result return input
    out = out.reset_index().ffill(axis=1).set_index('typegoedkeuringsnummer')
    
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
        ('field_info', 'width'): pd.Int64Dtype(),
        ('field_content', 'non_null'): int,
        ('field_content', 'not_null'): int,
        ('field_content', 'null'): int,
        ('field_content', 'count'): int,
        ('field_content', 'cardinality'): int,
        ('field_content', 'average'): float,
        ('field_content', 'sum'): float,
    }
    for fld,dtype in cast_as.items():
        if fld not in md.columns:
            continue
        md.loc[:,fld] = md.loc[:,fld].astype(dtype)

    # set index as field name (column name)
    md.set_index(('field_info','fieldName'), inplace=True)
    md.index.name='fieldName'

    # low cardinality could point to categorical data (factors)
    md.loc[:, ('field_content', 'factors')] = np.NaN
    
    if ('field_content', 'cardinality') not in md:
        # there is no cardinality info stop here
        return md

    n_category_max = max(md.loc[:, ('field_content', 'top')].apply(lambda x: len(x) if isinstance(x, list) else x)) # twenty
    is_cat = (md.loc[:, ('field_content', 'cardinality')] < n_category_max) & (md.loc[:, ('field_content', 'cardinality')] > 1)
    is_str = md.loc[:, ('field_info', 'dataTypeName')] == 'text'
    is_num = md.loc[:, ('field_info', 'dataTypeName')] == 'number'
    
    # string categories
    md.loc[:, ('field_content', 'factors')].update(md.loc[is_cat&is_str, ('field_content', 'top')].apply(lambda x: [i['item'] for i in x]))
    
    # integer categories
    uniq_values = md.loc[is_cat&is_num, ('field_content', 'top')].apply(lambda x: [(i['item']) for i in x])
    is_int = is_num.copy()
    is_int &= uniq_values.apply(lambda x: all([v.isnumeric() for v in x]))
    md.loc[:, ('field_content', 'factors')].update(uniq_values[is_int].apply(lambda x: [int(v) for v in x]))
    
    # counters (range)
    is_cnt = is_int.copy()
    is_cnt &= md.loc[is_int, ('field_content', 'factors')].apply(lambda x: max(x) == (min(x) + len(x)-1))
    md.loc[:, ('field_content', 'factors')].update(md.loc[is_cnt, ('field_content', 'factors')].apply(lambda x: range(min(x), max(x)+1)))
    md.loc[:, ('field_content', 'factors')]

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
            'vezc-m2t6': 'carrosserie_volgnummer',
            'jhie-znh9': ['carrosserie_volgnummer', 'carrosserie_voertuig_nummer_code_volgnummer'],
            'kmfi-hrps': ['carrosserie_volgnummer', 'carrosserie_klasse_volgnummer'],
            'sgfe-77wx': ['meld_datum_door_keuringsinstantie_dt'],
            'a34c-vvps': ['meld_datum_door_keuringsinstantie_dt', 'gebrek_identificatie'],
            'sghb-dzxx': ['montagedatum', 'demontagedatum'],
            'ahsi-8uyu': 'asnummer',
            'q7fi-ijjh': ['carrosserie_volgnummer', 'carrosserie_klasse_volgnummer'],
            'w2qp-idms': 'carrosserie_volgnummer',
            'nypm-t8hx': ['carrosserie_volgnummer', 'carrosserie_uitvoering_numeriek_volgnummer'],
            'mdqe-txpd': 'volgnummer',
            'fj7t-hhik': 'merkcode', 
            'g2s6-ehxa': 'volgnummer',
            '5w6t-p66a': ['volgnummer','brandstof_volgnummer'], 
            'mt8t-4ep4': 'plaats_aanduiding_volgnummer',
            'h9pa-e9ta': 'subcategorie_uitvoering_volgnr',
            '2822-t8sx': 'uitvgavenummer_verbruikboek',
            'r7cw-67gs': 'volgnummer',
            '3xwf-ince': 'rupsband_set_volgnr',
            '2ba7-embk': 'subcategorie_voertuig_volgnummer',
            '7ug8-2dtt': 'bijzonderheid_volgnummer',
            't49b-isb7': 'referentiecode_rdw',


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
            'floating_timestamp':np.datetime64
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
        elif isinstance(self.metadata_['primary_keys'][api_name], list):
            
            sep = '.' # separator between index fields

            idx = self.get_idx()

            # if primary key is a list of key we need to make a composite key
            assert idx.applymap(lambda x: sep not in x).all().all() # It could complicate things it sep is already present
            
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
            raise NotImplementedError(f'Api <{api_name}> has unregognized primary_key: {self.metadata_["primary_keys"][api_name]}')

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
        prim_key = [prim_key] if isinstance(prim_key, str) else prim_key       
        
        # pivot
        # create df with unique rows
        df_uniq_idx = df.reset_index().set_index(prim_key + cols)
        assert df_uniq_idx.index.is_unique

        # rank values in pivot columns to get a sorted index number (0, 1, 2, ..) 
        for i, col in enumerate(cols):
            ranks = df_uniq_idx.reset_index().groupby(df.index)[col].apply(lambda x: x.rank(method='dense')).astype(int).astype(str)
            ranks.index = df_uniq_idx.index
            df_uniq_idx.loc[:, f'indexno{i}'] = ranks

        df = df_uniq_idx.reset_index().set_index(prim_key).pivot(columns=[f'indexno{i}' for i in range(len(cols))])
        
        # flatten column names
        df.columns = df.columns.map(lambda x: '_'.join(x).rstrip('_'))
        
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
