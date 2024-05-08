import re
from time import sleep

def get_tree(url):
    
    import requests
    import codecs
    from lxml import html

    # get page
    do_try = True; tried = 0
    while do_try:
        try:
            page = requests.get(url)
            do_try = False # succes
        except:
            # catch glitch
            tried +=1
            print(f'try {url} again after pause: {tried}')
            sleep(1)
            if tried > 10:
                raise

    if page.status_code != 200:
        raise ConnectionError(f'status {page.status_code}. Page <{page.url}> does not exist.')
    # find encoding in header
    decode_type = page.headers["Content-type"]
    decode_type = re.findall('charset=(.*)', decode_type)[0]

    htmlstring = codecs.decode(page.content, decode_type)
    # Convert string to tree object
    return html.fromstring(htmlstring)

def download_image(url, fn, skip_when_exist=True):
    '''
    Download .jpg to disk
    '''
    import urllib.request
    import os
    
    if os.path.isfile(fn) & skip_when_exist:
        return f'{fn} exist. skip'
        
    # get image
    do_try = True; tried = 0
    while do_try:
        try:
            local_filename, headers = urllib.request.urlretrieve(url, fn)
            do_try = False # succes
        except:
            # catch glitch
            tried +=1
            sleep(1)
            print(f'try again {tried}')
            if tried > 10:
                raise
    
    sz_remote = headers.get('Content-Length')
    sz_local = os.path.getsize(local_filename)
    if (sz_remote == 0) or (sz_local == 0):
        os.remove(local_filename)
        return f'{local_filename} has zero bytes and {url} has {sz_remote}. Do not save'

    return f'{url} ->  {fn}'
        

