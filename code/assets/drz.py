import pandas as pd
import re

import scrape

def lot_code(auction_code, lot_nr):
    return f'K{auction_code[2:4]}{auction_code[5:9]}{lot_nr:.0f}'

def lot_url(auction_code, lot_nr, opbod):
    if isinstance(lot_nr, int):
        K_code = lot_code(auction_code, lot_nr)
    elif isinstance(lot_nr, str) and lot_nr.startswith('K'):
        # input was 'K....' not a number
        K_code = lot_nr
        
    if opbod:
        return f'https://verkoop.domeinenrz.nl/verkoop_bij_opbod_{auction_code}?status=both&meerfotos={K_code}'
    else:
        #https://verkoop.domeinenrz.nl/verkoop_bij_inschrijving_2023-0009?veilingen=2023-0009&meerfotos=K2300091800
        return f'https://verkoop.domeinenrz.nl/verkoop_bij_inschrijving_{auction_code}?veilingen={auction_code}&meerfotos={K_code}'
    
def has_content(tree):
    path = '//div[@class="wrapper"]/div[@class="article"]/div[@class="catalogus"]'
    el = tree.xpath(path)
    if len(el) == 0:
        return False
    if len(el[0].getchildren()) > 0:
        return True
    else:
        return False
    
def first_lot_nr(auction_code, opbod, start=999, max_nr=2000):
    not_ok = True
    lot_nr = start
    while not_ok:
        tree = scrape.get_tree(lot_url(auction_code, lot_nr, opbod))
        if has_content(tree):
            not_ok = False
            return lot_nr
        lot_nr += 1
        if lot_nr > max_nr:
            raise OverflowError(f'Lot_nr reached {max_nr}\n{lot_url(auction_code, lot_nr, opbod)}')
        
    return lot_nr

def index_nr(auction_code, lot_nr, opbod):
    if opbod:
        return auction_code[:7]+'-'+str(lot_nr)
    else:
        return auction_code[:5]+ auction_code[-2:] +'-'+ str(lot_nr)
    
def next_url(auction_code, tree, opbod):
    paths = [
        '//div[@class="wrapper"]/div[@class="article"]/div[@class="catalogus"]/div[@class="catalogusdetailitem split-item-first"]/div[2]/div[3]/a',
        '//div[@class="wrapper"]/div[@class="article"]/div[@class="catalogus"]/div[@class="catalogusdetailitem split-item-first"]/div[3]/div[3]/a'
    ]
    for path in paths:
        els = tree.xpath(path)
        if len(els) == 1:
            el = els[0]
            break
    K_code = re.findall('meerfotos=(.*)', el.get("href"))[0]
    url = lot_url(auction_code, K_code, opbod)
    lot_nr_s = K_code[-4:]
    return index_nr(auction_code, lot_nr_s, opbod), url

def all_pages(auction_code, opbod, verbose=False):
    source = pd.Series(name='Source', dtype=str, index=pd.Index([], name='lot_name'))

    # first
    if opbod:
        start = 999
    else:
        start = 1799
    if verbose:
        print(f'Finding first lot. starting from nr. {start}')
    lot_nr = first_lot_nr(auction_code, opbod, start=start)
    url = lot_url(auction_code, lot_nr, opbod)
    idx = index_nr(auction_code, lot_nr, opbod)
    source.loc[idx] = url
    if verbose:
        print(idx, end='\n')
    tree = scrape.get_tree(url) # tree of first
    
    # following
    ok = True
    while ok:
        idx, url = next_url(auction_code, tree, opbod)
        if idx in source.index:
            if verbose:
                print(f'\nreached first {idx}')
            ok = False
            break
        tree = scrape.get_tree(url)
        source.loc[idx] = url
        if verbose:
            print(idx, end='\n')

    return source

def get_price(tree):
    # Price is formatted as "strong"
    path = '//div[@class="wrapper"]/div[@class="article"]/div[@class="catalogus"]/div[@class="catalogusdetailitem split-item-first"]/strong'
    tag_closed = 'Deze kavel is gesloten.'
    tag_not_met = 'Niet gegund'
    tag_running = 'Huidig bod:'

    el = tree.xpath(path)
    if len(el) > 0:
        if el[0].text == tag_closed:
            # auction is closed. There should be a price
            el.pop(0) # see if there is a next bold
            if len(el) > 0:
                return el[0].text
            else:
                # if no more, try first text element
                path = '//div[@class="wrapper"]/div[@class="article"]/div[@class="catalogus"]/div[@class="catalogusdetailitem split-item-first"]/text()'
                el = tree.xpath(path)
                if el[0] == tag_not_met:
                    return f'no price: {tag_not_met}'
                # if all fails it was closed after all
                return f'closed: {tag_closed}'
        elif el[0].text == tag_running:
            # auction is running. There is temporary price
            return f'running: {tag_running} {el[0].tail}'
            
        # return price
        return el[0].text

        
    else:
        # Price is formatted as "b"
        el = tree.xpath(re.sub('strong', 'b', path))
        if len(el) > 0:
            if el[0].text == tag_not_met:
                # reserve not met
                return f'no price: {tag_not_met}'
        return 'empty'


def get_image_urls(tree):
        
    '''
    Return urls (src) of images. These are inside divs of class 'photo'
    '''
    
    items = tree.xpath('//div[@class="photo"]/a/img')
    # try high res first
    locs = [item.get('data-hresimg') for item in items]
    # fallback
    locs = [item.get('src') if l is None else l for l, item in zip(locs, items)]

    return locs
