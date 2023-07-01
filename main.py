import tkinter as tk
import tkinter.font
from tkinter import ttk
import pyglet
import pathlib
from PIL import ImageTk,Image
from load_font import *
import fitz
import json

from ctypes import windll
# make text crisp on the gui
windll.shcore.SetProcessDpiAwareness(1)

import sys
import os
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

pyglet.font.add_file(resource_path('aAtmospheric.ttf'))


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.selection_removed = False
        self.image_cache = dict()
        self.pdf_cache = dict()
        self.card_scale = 1
        self.card_dpi = 200
        self.TITLE = 'BattleScribe - 10th  edition'

        # self.geometry('1300x600')
        # self.overrideredirect(1)
        self.title(self.TITLE)
        self.state('zoomed')
        self.minsize(1000,800)
        self.iconbitmap(resource_path("wh40k.ico"))

        font_name = 'a Atmospheric'
        self.defaultFont = tk.font.nametofont("TkDefaultFont")
  
        self.defaultFont.configure(family='Noto Mono',size=10, weight='bold')
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=(font_name, 18), background='#222', foreground='#eee')
        selection_color = '#b92'
        style.configure("Treeview.Heading", 
            font=(font_name, 10), 
            background='#222', 
            foreground='#eee', 
            focuscolor=selection_color)
        style.configure("Treeview",
                background="#222",
                foreground="#eee",
                rowheight=25,
                fieldbackground="#222")
        
        style.map('Treeview', background=[('selected', selection_color)], foreground=[('selected', '#222')])
        style.map('Treeview.Heading', background=[('selected', selection_color)], foreground=[('selected', '#222')])
        style.layout("Treeview.Item",
            [('Treeitem.padding', {'sticky': 'nswe', 'children': 
                [('Treeitem.indicator', {'side': 'left', 'sticky': ''}),
                ('Treeitem.image', {'side': 'left', 'sticky': ''}),
                     ('Treeitem.text', {'side': 'left', 'sticky': ''}),
                ],
            })]
            )
        style.layout('arrowless.Vertical.TScrollbar', 
             [('Vertical.Scrollbar.trough',
               {'children': 
               [
                    ('Vertical.Scrollbar.thumb', {
                        'unit' : '1',
                        'sticky': 'nswe'}
                     )
                ],
                'sticky': 'ns'})])
        style.map('arrowless.Vertical.TScrollbar',
            background=[('active','#eee'), ('!active','#222')],
            troughcolor=[('active','#eee'), ('!active', '#222')],
            gripcount=[('active',0),('!active',0)]
            )

        self.columnconfigure(0,weight=100)
        self.columnconfigure(1,weight=0)
        self.columnconfigure(2,weight=100)
        self.rowconfigure(0,weight=25)
        self.rowconfigure(1,weight=1)

        self.tree = tree = ttk.Treeview(self, selectmode='extended', columns=('CPS'))

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview, style='arrowless.Vertical.TScrollbar')
        vsb.grid(column=1,row=0,rowspan=2,sticky='news')
        tree.configure(yscrollcommand=vsb.set)
        
        tree.heading('#0', text='MODELS', anchor=tk.CENTER)
        tree.column('#0', anchor=tk.W, stretch=True, minwidth=400)
        tree.heading('CPS', text='CPS', anchor=tk.CENTER)
        tree.column('CPS', anchor=tk.E, stretch=True)

        # set colors based on tags
        # tree.tag_configure('unit', background='#141')
        # tree.tag_configure('command points', background='#eee', foreground='#222')

        with open('models.json','r',encoding='utf8') as f:
            self.models = json.load(f)

        self.load_tree(tree,self.models)

        tree.grid(column=0,row=0, rowspan=3, sticky=tk.NSEW)

        frame = ttk.Frame(self)
        frame.grid_rowconfigure(0,weight=1)
        frame.grid_columnconfigure(0,weight=1)
        frame.grid_columnconfigure(1,weight=0)
        frame.grid(column=2,row=0, sticky='news', columnspan=2)
        self.selection_tree = ttk.Treeview(frame, selectmode='extended', columns=('Count', 'CPS'))
        self.selection_tree.grid(column=0, row=0, sticky=tk.NSEW)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.selection_tree.yview, style='arrowless.Vertical.TScrollbar')
        vsb.grid(column=1,row=0,sticky='news')
        self.selection_tree.configure(yscrollcommand=vsb.set)
        
        self.selection_tree.heading('#0', text='Type', anchor=tk.CENTER)
        self.selection_tree.column('#0', anchor=tk.CENTER, stretch=True, minwidth=400)
        self.selection_tree.heading('Count', text='Subtype', anchor=tk.CENTER)
        self.selection_tree.column('Count', anchor=tk.CENTER, stretch=True)
        self.selection_tree.heading('CPS', text='CPS', anchor=tk.CENTER)
        self.selection_tree.column('CPS', anchor=tk.CENTER, stretch=True)
        
        self.total_frame = ttk.Frame(self)
        self.total_frame.grid_columnconfigure(0,weight=1)
        self.total_frame.grid_columnconfigure(1,weight=1)
        self.total_frame.grid_rowconfigure(0,weight=1)
        self.total_frame.grid(column=2,row=1, columnspan=2, sticky='news')
        
        self.total_label = ttk.Label(self.total_frame, text='TOTAL', anchor=tk.CENTER)
        self.total_label.grid(column=0,row=0,sticky='news')
        self.total_value = ttk.Label(self.total_frame, text='0  pts', anchor=tk.CENTER)
        self.total_value.grid(column=1,row=0,sticky='news')

        self.tree.bind('<<TreeviewSelect>>', self.item_selected)
        self.selection_tree.bind('<<TreeviewSelect>>', self.item_selected)

        self.tree.bind('<Return>', self.add_items_selected)
        self.tree.bind('<Double-Button-1>', self.add_items_selected)

        self.selection_tree.bind('<Delete>', self.delete_items_selected)
        self.selection_tree.bind('<Double-Button-1>', self.delete_items_selected)

        self.tree.bind('<Button-3>', self.item_right_clicked)
        self.selection_tree.bind('<Button-3>', self.item_right_clicked)


    def get_hierarchy(self, tree, item):
        tags = ['hierarchy']
        hierarchy = []
        current = item
        while current:
            current = tree.parent(current)
            hierarchy += [tree.item(current)['text']]

        hierarchy = [h for h in hierarchy[::-1] if h]

        tags += hierarchy
        return tags

    def get_page_numbers(self, faction,key):
        pnos = []
        key = key.lower()
        if faction is not None and faction in self.pdfs:
            pdf = self.pdfs[faction]

            for e,page in enumerate(pdf.pages()):
                text = page.get_text(sort=True).strip()
                if not text:
                    continue
                lines = text.split('\n')
                first, second, *rest = lines
                first = first.strip().lower()
                second = second.strip().lower()
                if first == key or second == key:
                    pnos.append(e+1)
        return pnos

    def load_tree(self, tree, models):
        def sub_load(tree, key, value, index, faction=None):
            is_dict = isinstance(value, dict)

            if key.isupper():
                if key == 'DETACHMENT ENHANCEMENTS':
                    tags = ['detachment enhancements'] + self.get_hierarchy(tree,index) + [tree.item(index)['text']]
                    index = tree.insert(index, tk.END, text=key, open=True, tags=tags)
                    
            elif is_dict:
                is_open = False
                if tree.item(index)['text'] == 'DETACHMENT ENHANCEMENTS':
                    tags = ['enhancement']
                    is_open=True
                else:
                    tags = ['unit']
                
                tags +=  self.get_hierarchy(tree,index) + [tree.item(index)['text']]
                index = tree.insert(index, tk.END, text=key, open=is_open, tags=tags)

            if is_dict:
                for k,v in value.items():
                    sub_load(tree,k,v,index=index,faction=faction)
            else:
                tags = ['command points'] + self.get_hierarchy(tree,index) + [tree.item(index)['text']]
                index = tree.insert(index, tk.END, text=key, values=(f'{value} pts',), open=False,tags=tags)

        def try_open(filename):
            try:
                return fitz.open(filename)
            except:
                return None

        self.pdfs = {k:try_open(v) for k,v in models["PDF"].items()}

        for key, value in models["FACTIONS"].items():
            index = tree.insert('', tk.END, text=key, open=False, tags=['faction'])
            sub_load(tree,key,value,index=index, faction=key)


    def create_image(self, target, faction, pno):
        if (faction, pno, self.card_scale, self.card_dpi) in self.image_cache:
            img,w,h = self.image_cache[(faction, pno, self.card_scale, self.card_dpi)]
        else:
            doc = self.pdfs[faction]
            mat = fitz.Matrix(self.card_scale)
            pix = doc.get_page_pixmap(pno - 1, dpi=self.card_dpi, matrix=mat)

            image = Image.frombytes('RGB',
                                   [pix.width, pix.height],
                                   pix.samples)
            #w,h = int(image.width*self.card_scale),int(image.height*self.card_scale)
            w,h = int(image.width),int(image.height)
            image = image.resize((w,h))
            
            img = ImageTk.PhotoImage(image)
            self.image_cache[(faction, pno, self.card_scale, self.card_dpi)] = img,w,h

        target.label.grid_forget()
        target.canvas = canvas = tk.Canvas(target, width = w, height = h)
        canvas.create_image((0,0), anchor='nw', image=img)
        canvas.grid(column=0,row=0, sticky='news')

        target.geometry(f"{w}x{h}")
        target.update()
        
        
    def item_right_clicked(self, event):
        tree = event.widget
        item = tree.identify('item',event.x,event.y)

        if not tree.exists(item):
            return

        tags = tree.item(item)['tags']
        
        if 'hierarchy' not in tags:
            faction = tree.item(item)['text']
        else:
            hierarchy = tags[tags.index('hierarchy')+1:]
            faction = hierarchy[0]
            if faction not in self.models["FACTIONS"]:
                return

        pdf = self.pdfs.get(faction,None)
        if pdf is None:
            return

        if 'command points' in tags:
            tags = tree.item(tree.parent(item))['tags']
            item = tree.parent(item)

        if 'enhancement' in tags:
            pnos = self.get_page_numbers(faction,'ENHANCEMENTS')
        elif 'unit' in tags:
            pnos = self.get_page_numbers(faction,tree.item(item)['text'])
        elif 'faction' in tags:
            pnos = self.get_page_numbers(faction,'STRATAGEMS')
        elif event.widget == self.selection_tree:
            pnos = self.get_page_numbers(faction, hierarchy[-1])
            if not pnos:
                pnos = self.get_page_numbers(faction, 'ENHANCEMENTS')
        else:
            pnos = self.get_page_numbers(faction,'ENHANCEMENTS')
        if not pnos:
            return

        self.disableChildren(self)
        top = tk.Toplevel(self)
        top.grid_columnconfigure(0,weight=1)
        top.grid_rowconfigure(0,weight=1)
        top.geometry(f"300x200+0+0")
        top.label = label = ttk.Label(top, text='Loading...', anchor=tk.CENTER)
        label.grid(column=0,row=0, sticky='ns')
        top.configure(background="#222")
        top.resizable(False, False)
        # top.overrideredirect(1)
        top.withdraw()
        top.deiconify()
        top.update()
        
        def destroy(top):
            top.destroy()

        def flip_card(top, pdf, pnos):
            if hasattr(top,'canvas'):
                top.canvas.grid_forget()
            if top.index not in top.visited:
                top.label = label = ttk.Label(top, text='Loading...', anchor=tk.CENTER)
                label.grid(column=0,row=0, sticky='ns')
                top.geometry(f"300x200")
                top.update()
            ret = self.create_image(top, pdf, pnos[top.index])
            if ret is False:
                destroy(top)
                self.enableChildren(self)
                return
            top.update()
            top.visited.add(top.index)
            top.index = (top.index+1)%len(pnos)

        top.visited = set()
        top.index = 0
        flip_card(top,faction,pnos)
        if len(pnos) > 1 and top:
            top.bind('<Button-1>', lambda event,top=top,faction=faction,pno=pnos: flip_card(top,faction,pnos))
        top.bind('<Button-3>', lambda event,top=top: destroy(top))
        
        self.enableChildren(self)

    def item_selected(self, event):
        if event.widget == self.tree and self.selection_tree.selection() and not self.selection_removed:
            self.selection_removed = True
            self.selection_tree.selection_remove(*self.selection_tree.selection())
        elif event.widget == self.selection_tree and self.tree.selection() and not self.selection_removed:
            self.selection_removed = True
            self.tree.selection_remove(*self.tree.selection())
        else:
            self.selection_removed = False

    def add_items_selected(self, event):
        def assemble(i):
            item = self.tree.item(i)
            tags = item['tags']
            values = item['values']
            cps = values[0]
            parent = self.tree.item(self.tree.parent(i))

            return [f"{parent['text']}",f"{item['text']}", f"{values[0]}"], tags

        selection = [assemble(i) for i in self.tree.selection() if 'command points' in self.tree.item(i)['tags']]

        for s, t in selection:
            name, count, cps = s
            self.selection_tree.insert('', tk.END, text=name, open=True, values=(count, cps),tags=t)

        self.update_total_cps()

    def delete_items_selected(self, event):
        for item in event.widget.selection():
            event.widget.delete(item)
        event.widget.focus_set()
        self.update_total_cps()

    def update_total_cps(self):
        total_cps = 0
        for item in self.selection_tree.get_children():
            count, cps = self.selection_tree.item(item)['values']
            total_cps += int(cps.split(' ')[0])
        self.total_value['text'] = f'{total_cps}  pts'


    def disableChildren(self,parent):
        for child in parent.winfo_children():
            wtype = child.winfo_class()
            if wtype not in ('Frame','Labelframe','TFrame','TLabelframe', 'Treeview', 'TScrollbar', 'Toplevel'):
                child.configure(state='disable')
            elif wtype in ('Treeview',):
                child['selectmode'] = 'none'
            else:
                self.disableChildren(child)

    def enableChildren(self,parent):
        for child in parent.winfo_children():
            wtype = child.winfo_class()
            if wtype not in ('Frame','Labelframe','TFrame','TLabelframe', 'Treeview', 'TScrollbar', 'Toplevel'):
                child.configure(state='normal')
            elif wtype in ('Treeview',):
                child['selectmode'] = 'extended'
            else:
                self.enableChildren(child)




app = App()
app.mainloop()