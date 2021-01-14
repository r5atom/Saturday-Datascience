def read_tag_value(fn = './regex-patterns/drz-re-patt-tag.txt'):

    '''
    Reads text file.
    In text file the field name and regex pattern are separated by a comma.
        "[field name]", "[pattern]"
    In [pattern] the value denoted by .. in [?P<val>..] is added to [field name] in following function.
    '''
    
    import pandas as pd
    
    df=pd.read_csv(
        fn,
        comment='#',
        header=None,
        quotechar='"',
        delimiter=",",
        skipinitialspace=True,
        names=['Field', 'Pattern']
    )
    
    return df

def read_has_tag(fn = './regex-patterns/drz-re-patt-hastag.txt'):

    '''
    Reads text file.
    In text file the field name and regex pattern are separated by a comma.
        "[field name]", "[pattern]"
    If [pattern] exist [field name] is set to True in following functions
    '''
    
    import pandas as pd
    
    df=pd.read_csv(
        fn,
        comment='#',
        header=None,
        quotechar='"',
        delimiter=",",
        skipinitialspace=True,
        names=['Field', 'Pattern']
    )
    
    return df

def read_replace_fragments(fn = './regex-patterns/drz-re-patt-replace.txt'):
    
    '''
    Reads text file.
    In text file the search regex pattern and replacement string are separated by a comma.
        "[pattern]", "[replacement]"
    '''
    
    import pandas as pd
    
    df=pd.read_csv(
        fn,
        comment='#',
        header=None,
        quotechar='"',
        delimiter=",",
        skipinitialspace=True,
        names=['Pattern', 'Replace']
    ).fillna('') 

    return df

def read_all():
    
    '''
    do all with defaults
    '''
    
    tags = read_tag_value()
    flagtags = read_has_tag()
    repfragments = read_replace_fragments()

    return tags, flagtags, repfragments