import configparser

def read_config(settings_fn = r'../code/assets/drz-auction-settings.ini'):

    # Read settings from file
    cfg = configparser.ConfigParser()
    fid = open(settings_fn, 'r')
    cfg.read_file(fid)

    # Date of auction
    DATE = cfg['latest']['date'] # yyyy-mm

    # Read other  properties
    VERBOSE = cfg['latest'].getint('verbose') # debug level
    OPBOD = cfg['latest'].getboolean('is_irs') # "opbod" (multiple bids) of IRS (belastingdienst) results
    closed_data_fields = cfg['latest'].get('query_close_data') # Also query closed data?
    CLOSEDDATA = (closed_data_fields is not None) and (closed_data_fields.lower() not in ['0', 'false'])
    SKIPSAVE = cfg['latest'].getboolean('skip_saving') # Do not save to files

    # Url to website with results
    url_section = cfg.get('latest', 'url_version') # based on date
    baseurl = cfg.get(url_section, 'url')
    if OPBOD:
        url_part2 = eval(f'f{cfg.get(url_section, "url_opbod")}')
    else:
        url_part2 = eval(f'f{cfg.get(url_section, "url_insch")}')
    URL = baseurl + url_part2
    EXTEND_URL = cfg.getboolean(url_section, "url_add_veilingen")

    # Ini file
    if VERBOSE > 1:

        fid.seek(0)
        print('-'*(len(settings_fn)+4))
        print('|', settings_fn, '|')
        print('-'*(len(settings_fn)+4))
        for l in fid.readlines():
            print(f'{l}', end='')
        print('-'*(len(settings_fn)+4))
        print('|', settings_fn, '|')
        print('-'*(len(settings_fn)+4))
    fid.close()
    
    # output as dict
    out = dict(
        settings_fn=settings_fn,
        DATE=DATE,
        VERBOSE=VERBOSE,
        OPBOD=OPBOD,
        URL=URL,
        EXTEND_URL=EXTEND_URL,
        CLOSEDDATA=CLOSEDDATA,
        closed_data_fields=closed_data_fields,
        SKIPSAVE=SKIPSAVE,
    )

    return out