# import txt as dicts

import fitz
import json
import pathlib
from pprint import pprint

remove_suffix = lambda text, suffix: text[:-len(suffix)] if text.endswith(suffix) and len(suffix) != 0 else text

def get_pointvalues(path, *,show=False):
    print(path)
    if not path.exists():
        return
    with fitz.open(path.resolve()) as doc:
        text = ''.join([page.get_text() for page in doc])
        factions = dict()
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
                        target = factions[faction][attachments] = dict()
                    # don't care about this line
                    elif line == 'FORGE WORLD POINTS VALUES':
                        continue
                    else:
                        faction = line
                        target = factions[faction] = dict()
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
                            target[model][count_or_optional] = int(remove_suffix(pts,' pts'))
                        elif len(optional) == 2:
                            target[model]['+ '+count_or_optional] = int(remove_suffix(optional[1],' pts'))
    if show:
        pprint(factions,sort_dicts=False)
    return factions


if __name__ == '__main__':
    factions = get_pointvalues('pdfs/Munitorum_Field_Manual.pdf',show=True)

    with open('models.json','w',encoding='utf8') as f:
        json.dump(dict(FACTIONS=factions),f,indent=4,sort_keys=False)