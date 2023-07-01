# import txt as dicts

import pathlib
from pprint import pprint

def import_units(filename):
    p = pathlib.Path(filename)
    units = dict()
    faction = None
    attachments = None
    with open(p,'r',encoding='utf8') as f:
        for line in f.readlines():
            line = line.strip()

            if line.isupper():
                if faction is not None:
                    attachments = line
                    target = units[faction][attachments] = dict()
                else:
                    faction = line
                    target = units[faction] = dict()

            else:
                parts = line.split('=')
                if len(parts) == 1:
                    model = parts[0]
                elif len(parts) == 2:
                    count_or_optional, pts = parts
                    optional = pts.split('+')
                    if len(optional) == 1:
                        if model not in target:
                            target[model] = dict()
                        target[model][count_or_optional] = int(pts.removesuffix(' pts'))
                    elif len(optional) == 2:
                        target[model]['+ '+count_or_optional] = int(optional[1].removesuffix(' pts'))
                else:
                    print(line, '\nToo many parts')
    # pprint(units,sort_dicts=False)
    return units

def get_pointvalues():
    import fitz

    with fitz.open('PointValues.pdf') as doc:
        text = ''.join([page.get_text() for page in doc])
        units = dict()
        faction = None
        attachments = None
        is_faction = True
        start = False
        for line in text.split('\n'):
            line = line.strip()
            if line == '1':
                start = True
                continue
            if start:
                if line.isdigit():
                    continue

                if line.isupper():
                    if line == 'DETACHMENT ENHANCEMENTS':
                        attachments = line
                        target = units[faction][attachments] = dict()
                    else:
                        faction = line
                        target = units[faction] = dict()

                else:
                    parts = line.split('.')
                    if len(parts) == 1:
                        model = parts[0]
                    else:
                        parts = [parts[0].strip(), parts[-1]]
                    if len(parts) == 2:
                        count_or_optional, pts = parts
                        optional = pts.split('+')
                        if len(optional) == 1:
                            if model not in target:
                                target[model] = dict()
                            target[model][count_or_optional] = int(pts.removesuffix(' pts'))
                        elif len(optional) == 2:
                            target[model]['+ '+count_or_optional] = int(optional[1].removesuffix(' pts'))

    pprint(units,sort_dicts=False)
    return units

# units = get_pointvalues()
import json

# with open('models.json','w',encoding='utf8') as f:
#     json.dump(units,f, indent=4,sort_keys=False)
import time
import fitz
pdf = 'WH40K_10th_Index_Adepta_Sororitas.pdf'
with fitz.open(pdf) as f:
    start = time.perf_counter()
    mat = fitz.Matrix(.2)
    f.get_page_pixmap(1,dpi=400,matrix=mat)
    print(time.perf_counter() - start)