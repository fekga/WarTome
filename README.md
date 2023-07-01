# BattleScribe - 10th Edition

## Adding pdf to the json
The `models.json` contains the preprocessed point values of each unit. A pdf's path can be added to the `models.json` under `PDF` and under `[FACTION NAME]` key as a value.

Example:
```
"PDF" : {
  "BLOOD ANGELS": "Path\To\BloodAngels.pdf"
  }
```
I recommend copying the file next to the script.

## Controls

### Unit tree
| Command | Description |
| --- | --- |
| Left-Click | Open/Close subtree, select unit with command points (Ctrl and Shift also works to select multiple units) |
| Double-Click | Move selected units to the Selected Tree |
| Return key | Move selected units to the Selected Tree |
| Right-Click | Open a new window with the corresponding unit's card when a pdf is provided for it's faction (see above) |

### Selection Tree
| Command | Description |
| --- | --- |
| Left-Click | Select unit (Ctrl and Shift also works to select multiple units) |
| Double-Click | Remove selected units from the Selected Tree |
| Delete key | Move selected units to the Selected Tree |
| Right-Click | Open a new window with the corresponding unit's card when a pdf is provided for it's faction (see above) |

### Unit Card
| Command | Description |
| --- | --- |
| Left-Click | Go to the next page of the card (if the unit has multiple pages) |
| Right-Click | Close card |
