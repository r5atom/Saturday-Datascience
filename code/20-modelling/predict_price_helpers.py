
def pow10(y):
    return 10**y
    
# Split fuel helper functions

def split_lpg_type(s):
    '''Split lpg type from list of fuels separated by / '''

    import re
    
    # No type
    if s.endswith('lpg'):
        return s, ''
    if 'lpg' not in s:
        return s, ''
    # Type is after the last '/'
    M = re.search('^(.*)/(.*)$',s)
    if M:
        return M[1], M[2]
    else:
        return s, ''

def merge_lpg_and_lpgtype(fuel_type):
    '''Add LPG type to LPG (remove /). 
    Note that order of fuels is preserved. I.e. it is able to return both "benzine/lpg-g3" and "lpg-g3/benzine". '''

    import pandas as pd

    def _lpg_type(s):
        return 'lpg-' + split_lpg_type(s)[1] if (type(s) == str) and ('lpg' in s) else ''
    def _fuel_type_short(s):
        return split_lpg_type(s)[0] if (type(s) == str) else ''

    lpg_type = fuel_type.apply(_lpg_type)
    #lpg_type = fuel_type.apply(lambda s: 'lpg-' + split_lpg_type(s)[1] if (type(s) == str) and ('lpg' in s) else '')
    fuel_type_short = fuel_type.apply(_fuel_type_short)
    #fuel_type_short = fuel_type.apply(lambda s: split_lpg_type(s)[0] if (type(s) == str) else '')
    fuel_type_new = pd.Series([f.replace('lpg', l) if type(f) == str else f for f,l in zip(fuel_type_short,lpg_type)])
    return fuel_type_new

def get_unique_fuels(fuel_type):
    
    '''Splitting fuels at "/" and return unique values'''

    import numpy as np

    def _fuel_type_list(s):
        return s.split('/') if type(s) == str else np.NaN
    
    # make list (as string)
    fuel_type_list = fuel_type.apply(_fuel_type_list).astype(str)
    #fuel_type_list = fuel_type.apply(lambda s:s.split('/') if type(s) == str else np.NaN).astype(str)
    
    # Get unique fuels
    possible_fuels = list() # empty list
    for l in fuel_type_list.unique():
        for ll in eval(l): # use eval to convert str to list
            possible_fuels += [ll]     
    # uniquify
    return np.unique(possible_fuels)

    
from sklearn.base import BaseEstimator, TransformerMixin

# Custom transformer to make one-hot fuel encoder based on string
# This is different from get_dummies, because it can take a list of values in a field
class DummyfyFuel(BaseEstimator, TransformerMixin):
    def __init__(self, fuel_names=None):
        
        assert (fuel_names == None) or (isinstance(fuel_names, (list,))), '[fuel_names] should be list (or None)'
        
        self.fuel_names = fuel_names
        
    def fit(self, X, y=None):
        
        if not self.fuel_names:
            # get fuel names based on input.
            # Note that if train/test are split, test might lack a fuel type.
            self.fuel_names = get_unique_fuels(merge_lpg_and_lpgtype(X))

        return self
    
    def transform(self, X):

        def _fuel_type_list(s):
            return s.split('/') if type(s) == str else np.NaN
        def _fuel_dummies(l):
            return int(f in eval(l))
    
        import pandas as pd
        
        # get stringyfied list
        fuel_type_list = merge_lpg_and_lpgtype(X).apply(_fuel_type_list).astype(str)
        #fuel_type_list = merge_lpg_and_lpgtype(X).apply(lambda s:s.split('/') if type(s) == str else np.NaN).astype(str)
        # set index as input
        fuel_type_list.index = X.index

        # transform: dummies
        fuel_dummies = pd.DataFrame(index=fuel_type_list.index)
        for f in self.fuel_names:
            fuel_dummies['fuel_' + f] = fuel_type_list.apply(_fuel_dummies)
            #fuel_dummies['fuel_' + f] = fuel_type_list.apply(lambda l:int(f in eval(l)))

        return fuel_dummies
        
