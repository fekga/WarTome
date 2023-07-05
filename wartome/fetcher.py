import sys
from inspect import getmembers, isfunction
from urllib.request import urlopen, Request, urlretrieve, build_opener, install_opener
from urllib.parse import urlparse
from bs4 import BeautifulSoup as soup
from bs4.dammit import EncodingDetector
import pathlib
import datetime
import json
from copy import deepcopy
from collections import namedtuple, deque

# constants
here = pathlib.Path(__file__).parent
url = "https://www.warhammer-community.com/warhammer-40000-downloads/"
pdf_data = (here /'..'/'data.json').resolve()
pdf_folder = (here/'..'/'pdfs').resolve()
pdf_folder.mkdir(parents=True,exist_ok=True)
munitorum = 'Munitorum_Field_Manual'

# to be able to print non-utf8 characters
sys.stdout.reconfigure(encoding='utf-8')

# helper functions
def rchop(s, sub):
    return s[:-len(sub)] if sub and s.endswith(sub) else s

def lchop(s, sub):
    return s[len(sub):] if s.startswith(sub) else s

def exhaust(generator):
    deque(generator,maxlen=0)

# scraping functions
def checkURL(requested_url):
    if not urlparse(requested_url).scheme:
        requested_url = "https://" + requested_url
    return requested_url

def requestAndParse(requested_url):
    # define headers to be provided for request authentication
    headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' 
            'AppleWebKit/537.11 (KHTML, like Gecko) '
            'Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'
    }

    opener = build_opener()
    opener.addheaders = [(k, v) for k, v in headers.items()]
    install_opener(opener)

    requested_url = checkURL(requested_url)
    try:
        resp = Request(url = requested_url, headers = headers)
        opened_url = urlopen(resp)
        page_html = opened_url.read()
        opened_url.close()
        http_encoding = resp.encoding if 'charset' in resp.headers.get('content-type', '').lower() else None
        html_encoding = EncodingDetector.find_declared_encoding(page_html, is_html=True)
        encoding = html_encoding or http_encoding
        page_soup = soup(page_html, "html.parser", from_encoding='utf-8')
        return page_soup

    except Exception as e:
        print(e)

def download_pdfs(*,desired=None,fetch=False,skip_outliers=False):
    if desired is None:
        desired = []
    elif not isinstance(desired,list):
        desired = [desired]

    print(f'info: download_pdfs, {desired = }, {fetch = }, {skip_outliers = }')
    print(f'info: Checking existing {pdf_data}')
    pdf_data.touch(exist_ok=True)
    with open(pdf_data,'r',encoding='utf8') as pdf_datafile:
        try:
            pdf_datamap = json.load(pdf_datafile)
        except json.decoder.JSONDecodeError as e:
            print(e)
            pdf_datamap = dict()

    prev_datamap = deepcopy(pdf_datamap)
    found = set()

    page = requestAndParse(url)
    Result = namedtuple('Result', 'name date path needs_download')

    count_changes = 0

    for resource_group in page.find_all('div', class_='resources-groups'):
        for resource_item in resource_group.find_all('li', class_='resources-list__item'):
            # parsing name
            name = resource_item.h3.text.strip()
            name = rchop(name,'Datasheets')
            translation_map = {
            'Combat Patrols' : 'Combat Patrol',
            'Combat patrol' : 'Combat Patrol',
            }
            for k,v in translation_map.items():
                name = name.replace(k,v)
            name = name.strip().replace(': ','-').replace(" ","_")

            # parsing date
            date = resource_item.find('p', class_='resources-list__date').text.strip()
            date = date.split()[1]
            day,month,year = map(int,date.split('/'))
            update_date = datetime.date(year,month,day)

            # parsing url and filename
            pdf_url = resource_item.find('a',class_='resources-button', href=True)['href']
            pdf_filename = pdf_url.split('/')[-1]

            pdf_path = pdf_folder / f'{name}.pdf'

            pdf_datamap[name] = pdf_datamap.get(name,dict())
            curr_update_date = pdf_datamap[name].get('update_date',None)
            curr_path = pdf_datamap[name].get('path',None)

            found.add(name)

            if desired and name not in desired:
                continue
            elif desired:
                print(f'info: Desired found: {name}')

            def failcheck(checks):
                for x,check,msg in checks:
                    if check(x):
                        print(msg)
                        return True
                return False

            checks = [
            (curr_path,lambda x: x is None, f"warn: Path not present: {pdf_path}"),
            (curr_path,lambda x: not pathlib.Path(x).exists(), f"warn: Path missing: {pdf_path}"),

            (curr_update_date,lambda x: x is None, f"warn: Update date not present: {pdf_path}"),
            (curr_update_date,lambda x: update_date != datetime.datetime.fromisoformat(x).date(), f"warn: Update mismatch: {pdf_path}"),
            ]

            needs_download = failcheck(checks)

            

            if not fetch and needs_download:
                count_changes += 1
                pdf_datamap[name]['update_date'] = update_date.isoformat()
                pdf_datamap[name]['path'] = pdf_path.as_posix()
                print(f'info: Downloading "{name}" with date [{update_date}] to "{pdf_path}"')
                urlretrieve(pdf_url, pdf_path)
                yield Result(name, update_date, pdf_path, needs_download)

            if fetch and not needs_download:
                yield Result(name, update_date, pdf_path, needs_download)

    if not skip_outliers:
        outliers = (set(pdf_datamap.keys()) ^ set(prev_datamap.keys())) - found
        for name in outliers:
            pdf_datamap.pop(name,None)
            count_changes += 1
            print(f'info: Outlier entry found and removed: {name}')
        datafiles = {v['path']:k for k,v in pdf_datamap.items() if v}
        for datafile in pdf_folder.glob('*.pdf'):
            datastr = datafile.as_posix()
            if datastr not in datafiles:
                datafile.unlink(missing_ok=True)
                print(f'info: Outlier file found and removed: {datastr}')
    else:
        print('info: Outliers skipped')

    if count_changes > 0:
        print(f'info: Writing result to {pdf_data}')
        with open(pdf_data,'w',encoding='utf8') as pdf_datafile:
            json.dump(pdf_datamap, pdf_datafile, indent=4,sort_keys=False)

def get_munitorum(*,fetch=False):
    results = list(download_pdfs(fetch=fetch,desired=munitorum,skip_outliers=True))
    if results:
        return results[0].path

def clean():
    exhaust(download_pdfs(fetch=True,skip_outliers=False))

def update():
    exhaust(download_pdfs(fetch=False,skip_outliers=False))

if __name__ == '__main__':
    print(get_munitorum())
    #clean()
    #update()
    print('='*40)
    # path = get_munitorum()
    # print(path)
    # for result in download_pdfs(fetch=True,skip_outliers=True):
    #     # if needs_download:
    #     #     print(name,needs_download)
    #     pass
    print('='*40)

