import re
import numpy as np
import pandas as pd

def expand_results_columns(df):
    '''
    The results field contains a dict that can be expanded to flatten the output
    '''
    
    assert 'Results' in df.columns
    assert 'Count' in df.columns
    assert any(df.Count.values == 0) == False
    
    return pd.concat([df.drop(columns='Results'), pd.DataFrame.from_dict(df.Results.to_list())], axis=1)

def flatten_multi_index(multi_indx):
    '''
    flatten index
    '''

    indx = multi_indx.to_frame()
    indx = indx.apply(lambda x: '_'.join(x.str.lower()), axis=1)

    illegal_chars = r' |\(|\)|\\|\/|\-|\$'
    indx = indx.apply(lambda x: re.sub(fr'({illegal_chars})','', x))

    return pd.Index(indx)    


def adjust_key_numbering(key_names):
    keys_with_number = key_names[key_names.apply(lambda x: re.search(r'[0-9]+$', x) is not None)]
    keys_with_number = keys_with_number.apply(lambda x: re.findall(r'(.+)[0-9]+$', x)[0]).unique()

    # adjust name from "Note3" to "Note_3" and start counter at 1 (eg. "Note_1")
    for key_name in keys_with_number:
        sel = key_names.apply(lambda x: re.search(rf'^{key_name}[0-9]*$', x) is not None)
        key_names[sel] = key_names[sel].apply(lambda x: re.sub(rf'({key_name})([0-9]*)$', r'\1_\2',x))
        key_names[sel] = key_names[sel].apply(lambda x: x+'1' if x.endswith('_') else x)
    return key_names

class Nhtsa:
    
    from http.client import InvalidURL
    from urllib.request import HTTPError

    def __init__(self, vin, url = r'https://vpic.nhtsa.dot.gov/decoder/Decoder/ExportToExcel?', verbose=0):
        self.vin_ = vin
        self.url_ = url
        self.verboselevel_ = verbose
        self.succes_ = None
        self.set_abrv_list(abrv='default')
        self.set_units_list(units='default')

    def __str__(self):
        out = 'Nhtsa class contains'
        for fld in dir(self):
            if fld.startswith('_'):
                continue
            if fld.endswith('_'):
                val = getattr(self, fld)
                if 'shape' in dir(val):
                    out += '\n' + f'{fld}: {val.shape}'
                else:
                    out += '\n' + f'{fld}: {val}'
        if self.succes_ == True:
            out += f'\ndata (size): {self.data.shape}'
        return out

    def _checks(self, kind):
        '''
        Helper function to check status.
        '''
        if kind == 'data':
            # Should have data
            if self.succes_ is None:
                if self.verboselevel_ > 0:
                    print('No data. Run <get_data()> first.')
                return False
            else:
                return True
        elif kind == 'index_unique':
            # Should be non-unique
            if self.data.index.is_unique:
                if self.verboselevel_ >= 4:
                    print('Index is unique.')            
                return True
            else:
                if self.verboselevel_ >= 2:
                    print('Index is not unique.')            
                return False
        elif kind == 'index_split':
            # Is group name split
            if self.data.index.nlevels == 4:
                if self.verboselevel_ >= 4:
                    print('Index has been split.')            
                return True
            else:
                return False
        else:
            raise NotImplementedError

    def get_data(self):
        '''
        Get data from website and store as pandas dataframe.
        '''
        
        # Make url based on base url and vin
        call = f'{self.url_}VIN={self.vin_}'
        self.call_ = call
        # Get data
        try:
            # url returns CSV
            resp = pd.read_csv(call, sep=',', na_values=['Not Applicable'])
            self.succes_ = True

        except InvalidURL:
            self.succes_ = False
            self.errormsg_ = f'URL <{self.call_}> is invalid. It might have characters that are not allowed.'
            if self.verboselevel_ > 0:
                print(self.errormsg_)
            resp = pd.DataFrame(data = {'Group Name': np.NaN, 'Element': 'Vin', 'Value': vin}, index = [-1])
        
        except HTTPError:
            self.succes_ = False
            self.errormsg_ = f'URL <{self.call_}> is invalid. Server might be offline.'
            if self.verboselevel_ > 0:
                print(self.errormsg_)
            resp = pd.DataFrame(data = {'Group Name': np.NaN, 'Element': 'Vin', 'Value': vin}, index = [-1])
            
        # Clean up response
        resp.drop_duplicates(inplace=True)
        resp.set_index(['Group Name', 'Element'], inplace=True)
        resp = pd.concat([resp, pd.DataFrame({'Value': self.vin_}, index=[(np.NaN, 'Vin')])]) # add input
        # add origin
        resp.loc[:, 'nhtsa key'] = resp.index.to_frame().fillna('').apply(' / '.join, axis=1)
        
        # Store data
        self.data = resp
            
   
    def make_index_unique(self):
        '''
        Make index unique by adding counter as done with other fields
        '''
        
        assert self._checks('data')
        assert self._checks('index_split') == False, 'Run <make_index_unique()> before <split_group_index()>.'
        if self._checks('index_unique') == True:
            # already unique
            return None
        
        indx = self.data.index.to_frame()
        sel_first = indx.index.duplicated(keep = 'first')
        counters = [0] * indx.index[sel_first].nunique() # list of counters with length nr of non-unique
        for i,name in enumerate(indx.index[sel_first]):
                
            # Select current index name and update counter
            index_toggle = indx.index[sel_first].unique() == name
            counters = [c+1 if sel else c for c,sel in zip(counters, index_toggle)]
            assert sum(index_toggle) == 1, 'only one should be current'
            counter = [c for c,sel in zip(counters, index_toggle) if sel][0]
            
            new_name = (name[0], name[1] + str(counter+1)) # "counter+1" suffix starts at 2. Similar to other fields
            iloc = np.where(sel_first)[0][i]
            
            if self.verboselevel_ >= 4:
                print(i, iloc, ' - '.join(name), counters, counter, indx.iloc[iloc].name, new_name)
                
            indx.iloc[iloc] = new_name
        
        self.data.index = pd.MultiIndex.from_frame(indx)
        
        assert self._checks('index_unique'), 'index is still not unique'
        
    def adjust_index_counter(self):
        '''
        Add counter in multiline key
        '''
    
        assert self._checks('data')
        assert self._checks('index_unique')
        assert self._checks('index_split')
        
        indx = self.data.index.to_frame()
        
        # Adjust keys from "Element" field that have number (e.g. "Note3")
        key_names = adjust_key_numbering(indx.Element)
        
        if self.verboselevel_ >= 4:
            display(key_names[key_names.apply(lambda x: re.search(r'_[0-9]+$', x) is not None)].to_frame())
            
        # apply
        indx.Element = key_names
        self.data.index = pd.MultiIndex.from_frame(indx)
        assert self._checks('index_unique')
    
    def split_group_index(self):
        '''
        Split group name result
        '''
        assert self._checks('data')
        indx = self.data.index.to_frame()
        
        # If group name is empty it is a system returned value
        group_split = indx.loc[:,'Group Name'].fillna('System').str.split(r'\s+/\s+', expand=True, regex=True).fillna('')
        
        # name levels 0, 1, etc
        col_names = ['Group Name ' + str(i) for i in group_split.columns] 
        group_split.columns = col_names
        
        # apply
        indx  = pd.concat([group_split, indx.Element], axis=1)
        self.data.index = pd.MultiIndex.from_frame(indx)
        
    def set_abrv_list(self, abrv='default'):
        if abrv == 'default':
            abrv = {
                'Anti-lock Braking System (ABS)': 'ABS',
                'Electronic Stability Control (ESC)': 'ESC',
                'Tire Pressure Monitoring System (TPMS) Type': 'TPMS',
                'Event Data Recorder (EDR)': 'EDR',
                'Automatic Crash Notification (ACN) / Advanced Automatic Crash Notification (AACN)': 'CAN_AACN',
                'Crash Imminent Braking (CIB)': 'CIB',
                'Forward Collision Warning (FCW)': 'FCW',
                'Dynamic Brake Support (DBS)': 'DBS',
                'Pedestrian Automatic Emergency Braking (PAEB)': 'PAEB',
                'Blind Spot Warning (BSW)': 'BSW',
                'Lane Departure Warning (LDW)': 'LDW',
                'Lane Keeping Assistance (LKA)': 'LKA',
                'Blind Spot Intervention (BSI)': 'BSI',
                'Daytime Running Light (DRL)': 'DRL',
                'Adaptive Driving Beam (ADB)': 'ADB',
                'Adaptive Cruise Control (ACC)': 'ACC',
                'Active Safety System Note': 'activesafetysysnote',
                'Automatic Pedestrian Alerting Sound (For Hybrid and EV only)': 'automaticpedestrianalertingsound'
            }
        self.abrv_ = abrv
        
    def set_units_list(self, units='default'):
        if units == 'default':
            units = [
                'Displacement (CC)',
                'Displacement (CI)',
                'Displacement (L)',
                'Engine Power (kW)',
                'Engine Brake (hp) From',
                'Engine Brake (hp) To',
                'Top Speed (MPH)',
                'Track Width (inches)',
                'Bus Length (feet)',
                'Bed Length (inches)',
                'Curb Weight (pounds)',
                'Wheel Base (inches) From',
                'Wheel Base (inches) To',
                'Trailer Length (feet)',
                'Wheel Size Front (inches)',
                'Wheel Size Rear (inches)',
                'Base Price ($)',
                'Battery Current (Amps) From',
                'Battery Voltage (Volts) From',
                'Battery Energy (kWh) From',
                'Battery Current (Amps) To',
                'Battery Voltage (Volts) To',
                'Battery Energy (kWh) To',
                'Charger Power (kW)'
            ]
        self.units_ = units
        
    def abreviate_element_index(self):
        '''
        abreviate and substitute units
        '''
        assert self._checks('data')
        indx = self.data.index.to_frame()

        # abreviate
        indx.Element = indx.Element.replace(self.abrv_)
        indx.Element = indx.Element.apply(lambda x: re.sub(r'\((.+)\)', r'\1', x) if x in self.units_ else x).to_list()
        if self.verboselevel_ >= 4:
            print('These elements have characters that are not allowed')
            for l in indx.Element.apply(lambda x: x if re.search('\(.+\)', x) is not None else np.NaN).dropna().to_list():
                print(f'\t{l}')
        self.data.index = pd.MultiIndex.from_frame(indx)
        
    def flatten_index(self):
        '''
        flatten index
        '''
        
        assert self._checks('data')
        indx = flatten_multi_index(self.data.index)
        if self.verboselevel_ >= 4:
            display(indx)
        self.data.index = pd.Index(indx)
        
    def full_parse(self):
        '''
        Parse results in correct sequence.
        '''
        
        self.get_data()
        self.abreviate_element_index()
        self.make_index_unique()
        self.split_group_index()
        self.adjust_index_counter()
        self.flatten_index()

        if self.verboselevel_ > 0:
            print(self)

class Nhtsa_batch:
    
    def __init__(self, vins, url = r'https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch', batch_size=50, verbose=0):
        self.vins_ = vins
        self.url_ = url
        self.batch_size_ = batch_size
        self.verboselevel_ = verbose
        self.succes_ = None
        self._data_dict()
        self._prep_data()
        
    def __str__(self):
        out = 'Nhtsa_batch class contains'
        for fld in dir(self):
            if fld.startswith('_'):
                continue
            if fld.endswith('_'):
                val = getattr(self, fld)
                if 'shape' in dir(val):
                    out += '\n' + f'{fld}: {val.shape}'
                else:
                    out += '\n' + f'{fld}: {val}'
        if self.succes_ == True:
            out += f'\ndata (size): {self.data.shape}'
        return out

    def _data_dict(self, fn = './assets/nhtsa-data-dict.csv'):
        self.data_dict_ = pd.read_csv(fn, sep=';', index_col=0)
        
    def _checks(self, kind):
        '''
        Helper function to check status.
        '''
        if kind == 'data':
            # Should have data
            if self.succes_ is None:
                if self.verboselevel_ > 0:
                    print('No data. Run <get_data()> first.')
                return False
            else:
                return True
        if kind == 'input_vector':
            # Input should be a vector
            if isinstance(self.vins_, pd.Series):
                if self.verboselevel_ > 0:
                    print('Input is a vector.')
                return True
            else:
                if self.verboselevel_ >= 2:
                    print('Input is not a vector.')
                return False
        elif kind == 'index_unique':
            # Should be non-unique
            if self.data.index.is_unique:
                if self.verboselevel_ >= 4:
                    print('Index is unique.')            
                return True
            else:
                if self.verboselevel_ >= 2:
                    print('Index is not unique.')            
                return False
        elif kind == 'columns_unique':
            # Should be non-unique
            if self.data.columns.is_unique:
                if self.verboselevel_ >= 4:
                    print('Index is unique.')            
                return True
            else:
                if self.verboselevel_ >= 2:
                    print('Index is not unique.')            
                return False
        elif kind == 'index_split':
            # Is group name split
            if self.data.index.nlevels == 4:
                if self.verboselevel_ >= 4:
                    print(f'Index has been split in {self.data.index.nlevels} levels.')
                return True
            else:
                if self.verboselevel_ >= 2:
                    print(f'Index {self.data.index.nlevels} levels.')
                return False
        elif kind == 'columns_split':
            # Is group name split
            if self.data.columns.nlevels == 4:
                if self.verboselevel_ >= 4:
                    print(f'Index has been split in {self.data.columns.nlevels} levels.')
                return True
            else:
                if self.verboselevel_ >= 2:
                    print(f'Index {self.data.columns.nlevels} levels.')
                return False
        else:
            raise NotImplementedError
            
    def _prep_data(self):
        '''
        Make sure the input is <vin>,<mfyear>
        '''
        if self._checks('input_vector'):
            # already a vector
            return
        df_ = self.vins_
        df_.iloc[:,0] = df_.iloc[:,0].apply(lambda x: re.sub(';','?', x) if ';' in x else x)
        df_.iloc[:,1] = df_.iloc[:,1].astype(str)
        df_ = df_.replace({'': np.NaN}).dropna(subset=df_.columns[0])
        self.vins_ = df_.fillna('').apply(','.join, axis=1)
        

            
    def get_data(self):
        '''
        Get data from website in batches and store as pandas dataframe.
        '''
        import requests
        
        batches = self.vins_.groupby(np.arange(self.vins_.shape[0]) // self.batch_size_)
        self.nbatches_ = len(batches)
        resp = pd.DataFrame()
        post_fields = {'format': 'json', 'data': ''}
        for i_batch, batch in batches:
            if self.verboselevel_ > 0:
                print(f'batch [{i_batch+1}/{self.nbatches_}]')
            if self.verboselevel_ > 8:
                print(batch.shape)
                display(batch)

            # set post fields
            data = ';'.join(batch)
            post_fields.update(data=data)

            # get response
            rsp = requests.post(self.url_, data=post_fields).text
            if self.verboselevel_ > 8:
                print(rsp)
            add = pd.read_json(rsp)
            add.loc[:, 'Batch'] = i_batch+1
            if self.verboselevel_ > 8:
                display(add)
            if add.Message.str.lower().str.contains('error').any() == True:
                display(add.Results.values)
            assert any(add.Count.values == 0) == False

            # add to dataframe
            add = expand_results_columns(add)
            add.replace({'Not Applicable': np.NaN, '': np.NaN}, inplace=True)
            add.index = batch.index.copy()
            resp = pd.concat([resp, add])
            
        self.succes_ = True
        # Store data
        self.data = resp
        
    def multiindex_data(self):
        '''
        Abbreviate and translate columns to multiindex
        '''
        assert self._checks('data')
        assert self._checks('columns_split') == False, 'Already multiindex.'
        
        fields = self.data_dict_
        abbr_cols = self.data.columns.intersection(fields.nhtsa_abbreviation)
        sys_cols = np.setdiff1d(self.data.columns, fields.nhtsa_abbreviation)
        new_index = pd.concat([
            fields.set_index('nhtsa_abbreviation').loc[abbr_cols, [f'GroupName_{i}' for i in range(3)]], 
            abbr_cols.to_series(name='Element')
        ], axis=1)
        new_index = pd.concat([new_index,
                               pd.concat([
                                    pd.DataFrame(data=[['System', np.NaN, np.NaN]] * sys_cols.shape[0], index=sys_cols, columns=[f'GroupName_{i}' for i in range(3)]),
                                    pd.Series(data=sys_cols, index=sys_cols, name='Element')
                                ], axis=1)], axis=0)
        new_index = new_index.fillna('')
        self.data = pd.concat([self.data.T, new_index], axis=1).set_index([f'GroupName_{i}' for i in range(3)] + ['Element']).T

    def adjust_index_counter(self):
        '''
        Add counter in multiline key
        '''
    
        assert self._checks('data')
        assert self._checks('columns_unique')
        assert self._checks('columns_split')
        
        indx = self.data.columns.to_frame()
        
        # Adjust keys from "Element" field that have number (e.g. "Note3")
        key_names = adjust_key_numbering(indx.Element)
        
        if self.verboselevel_ >= 4:
            display(key_names[key_names.apply(lambda x: re.search(r'_[0-9]+$', x) is not None)].to_frame())
            
        # apply
        indx.Element = key_names
        self.data.columns = pd.MultiIndex.from_frame(indx)
        assert self._checks('index_unique')

    def flatten_index(self):
        '''
        flatten index
        '''   
        assert self._checks('data')
        assert self._checks('columns_split')
        
        indx = flatten_multi_index(self.data.columns)
        if self.verboselevel_ >= 4:
            display(indx)
        self.data.columns = pd.Index(indx)

    def full_parse(self):
        '''
        Parse results in correct sequence.
        '''
        
        self.get_data()
        if self.verboselevel_ > 8: print(self)
        self.multiindex_data()
        if self.verboselevel_ > 8: print(self)
        self.adjust_index_counter()
        if self.verboselevel_ > 8: print(self)
        self.flatten_index()
        if self.verboselevel_ > 8: print(self)

        if self.verboselevel_ > 0:
            print(self)