import tkinter as tk
import tkinter.font
import tkinter.messagebox
from tkinter import ttk
import pyglet
import pathlib
from PIL import ImageTk,Image
from load_font import *
import fitz
import json

from ctypes import windll

import wartome as wt

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


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.selection_removed = False
        self.image_cache = dict()
        self.pdf_cache = dict()
        self.card_scale = 1
        self.card_dpi = 200
        self.TITLE = 'WarTome - 10th  edition'


        self.title(self.TITLE)
        self.state('zoomed')
        self.geometry('1000x800')
        self.minsize(1000,800)
        self.iconbitmap(resource_path("wh40k.ico"))

        

        self.init_styles()
        self.init_widgets()
        self.init_bindings()
        self.after(0, self.post_init)

    def init_styles(self):

        font_name = 'a Atmospheric'
        font_size = 10
        label_size = 18
        row_height = 25
        defaultFont = tk.font.nametofont("TkDefaultFont")
        defaultFont.configure(family='Noto Mono',size=font_size, weight='bold')

        selection_color = '#b92'
        deselection_color = '#222'
        background = '#222'
        foreground = '#eee'

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TLabel", 
            font=(font_name, label_size), 
            background=background, 
            foreground=foreground)
        
        style.configure("Treeview.Heading", 
            font=(font_name, font_size), 
            background=background, 
            foreground=foreground, 
            focuscolor=selection_color)

        style.configure("Treeview",
                background=background,
                foreground=foreground,
                rowheight=row_height,
                fieldbackground=background)
        
        style.map('Treeview', 
            background=[
            ('selected', selection_color), 
            ('!selected', deselection_color)], 
            foreground=[
            ('selected', background),
            ('!selected', foreground)])

        style.map('Treeview.Heading', 
            background=[
            ('selected', selection_color), 
            ('!selected', deselection_color)], 
            foreground=[
            ('selected', background),
            ('!selected', foreground)])

        style.layout("Treeview.Item",
            [('Treeitem.padding', {'sticky': 'nswe', 'children': 
                [('Treeitem.indicator', {'side': 'left', 'sticky': ''}),
                ('Treeitem.image', {'side': 'left', 'sticky': ''}),
                     ('Treeitem.text', {'side': 'left', 'sticky': ''}),
                ],
            })])

        style.layout('arrowless.Vertical.TScrollbar', 
             [('Vertical.Scrollbar.trough',
               {'children': 
               [('Vertical.Scrollbar.thumb', 
                        {'unit' : '1',
                        'sticky': 'nswe'})
                ],
                'sticky': 'ns'})])

        style.map('arrowless.Vertical.TScrollbar',
            background=[('active',foreground), ('!active',background)],
            troughcolor=[('active',foreground), ('!active', background)],
            gripcount=[('active',0),('!active',0)]
            )

    def init_widgets(self):
        self.columnconfigure(0,weight=100)
        self.columnconfigure(1,weight=0)
        self.columnconfigure(2,weight=100)
        self.rowconfigure(0,weight=25)
        self.rowconfigure(1,weight=1)

        self.tree = tree = ttk.Treeview(self, selectmode='extended', columns=('POINTS'))

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview, style='arrowless.Vertical.TScrollbar')
        vsb.grid(column=1,row=0,rowspan=2,sticky='news')
        tree.configure(yscrollcommand=vsb.set)
        
        tree.heading('#0', text='MODELS', anchor=tk.CENTER)
        tree.column('#0', anchor=tk.W, stretch=True, minwidth=600)
        tree.heading('POINTS', text='POINTS', anchor=tk.CENTER)
        tree.column('POINTS', anchor=tk.E, stretch=True)

        tree.grid(column=0,row=0, rowspan=3, sticky=tk.NSEW)

        frame = ttk.Frame(self)
        frame.grid_rowconfigure(0,weight=1)
        frame.grid_columnconfigure(0,weight=1)
        frame.grid_columnconfigure(1,weight=0)
        frame.grid(column=2,row=0, sticky='news', columnspan=2)
        self.selection_tree = ttk.Treeview(frame, selectmode='extended', columns=('Count', 'POINTS'))
        self.selection_tree.grid(column=0, row=0, sticky=tk.NSEW)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.selection_tree.yview, style='arrowless.Vertical.TScrollbar')
        vsb.grid(column=1,row=0,sticky='news')
        self.selection_tree.configure(yscrollcommand=vsb.set)
        
        self.selection_tree.heading('#0', text='Type', anchor=tk.CENTER)
        self.selection_tree.column('#0', anchor=tk.CENTER, stretch=True, minwidth=500)
        self.selection_tree.heading('Count', text='Subtype', anchor=tk.CENTER)
        self.selection_tree.column('Count', anchor=tk.CENTER, stretch=True, minwidth=300)
        self.selection_tree.heading('POINTS', text='POINTS', anchor=tk.CENTER)
        self.selection_tree.column('POINTS', anchor=tk.CENTER, stretch=False, minwidth=100)
        
        frame = ttk.Frame(self)
        frame.grid_columnconfigure(0,weight=1)
        frame.grid_columnconfigure(1,weight=1)
        frame.grid_rowconfigure(0,weight=1)
        frame.grid(column=2,row=1, columnspan=2, sticky='news')

        subframe = ttk.Frame(frame)
        subframe.grid_columnconfigure(0,weight=1)
        subframe.grid_rowconfigure(0,weight=1)
        subframe.grid(column=0,row=0, columnspan=1, sticky='ew')
        
        self.total_label = ttk.Label(subframe, text='TOTAL', anchor=tk.CENTER)
        self.total_label.grid(column=0,row=0,sticky='news')

        subframe = ttk.Frame(frame)
        subframe.grid_columnconfigure(0,weight=1)
        subframe.grid_rowconfigure(0,weight=1)
        subframe.grid(column=1,row=0, columnspan=1, sticky='ew')

        self.total_value = ttk.Label(subframe, text='0  points', anchor=tk.CENTER)
        self.total_value.grid(column=0,row=0,sticky='news')

    def init_bindings(self):
        self.tree.bind('<<TreeviewSelect>>', self.item_selected)
        self.selection_tree.bind('<<TreeviewSelect>>', self.item_selected)

        self.tree.bind('<Return>', self.add_items_selected)
        self.tree.bind('<Double-Button-1>', self.add_items_selected)

        self.selection_tree.bind('<Delete>', self.delete_items_selected)
        self.selection_tree.bind('<Double-Button-1>', self.delete_items_selected)

        self.tree.bind('<Button-3>', self.item_right_clicked)
        self.selection_tree.bind('<Button-3>', self.item_right_clicked)

    def post_init(self):
        self.models = None
        self.pdfs = None
        self.field_manual = None
        self.check_loading = False
        self.load_pdf_data()
            
    def post_load_init(self):
        self.models = wt.parser.get_pointvalues(self.field_manual)
        with open(wt.fetcher.pdf_data,'r',encoding='utf8') as data:
            self.pdfs = json.load(data)

        from pprint import pprint
        pprint(self.models)
        self.load_tree(self.tree,self.models)

    def on_checking_loading(self):
        if self.check_loading:
            if self.field_manual is not None:
                self.post_load_init()
                self.check_loading = False
                return
            self.after(0,self.on_checking_loading)

    def load_pdf_data(self):
        self.field_manual = wt.fetcher.get_field_manual(fetch=True)
        if self.field_manual is None:
            ret = tk.messagebox.askokcancel(title="Missing field_manual",message="Field Manual is missing, attempt downloading?")
            if ret:
                self.check_loading = True
                self.after(50,self.on_checking_loading)
                self.field_manual = wt.fetcher.get_field_manual()
        else:
            self.post_load_init()

    def get_page_numbers(self, faction, key):
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
        def sub_load(tree, key, parent, index, faction=None):
            is_dict = isinstance(parent, dict)

            # TODO: modify self.models instead of this tags bullshit

            if key.isupper():
                # detchment enhancements
                if key == 'DETACHMENT ENHANCEMENTS':
                    index = tree.insert(index, tk.END, text=key, open=True)
            elif is_dict:
                # enhancement or unit
                is_open = tree.item(index)['text'] == 'DETACHMENT ENHANCEMENTS'
                index = tree.insert(index, tk.END, text=key, open=is_open)
            if is_dict:
                for k,v in parent.items():
                    sub_load(tree,k,v,index=index,faction=faction)
            else:
                # command points
                index = tree.insert(index, tk.END, text=key, values=(f'{parent} points',), open=False)

        if models:
            for faction, parent in models.items():
                index = tree.insert('', tk.END, text=faction, open=False)
                sub_load(tree,faction,parent,index=index, faction=faction)
        else:
            print("warning: Couldn't load models")


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
            if faction not in self.models:
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
        print('SELECTION')
        if event.widget == self.tree and self.selection_tree.selection() and not self.selection_removed:
            self.selection_removed = True
            self.selection_tree.selection_remove(*self.selection_tree.selection())
        elif event.widget == self.selection_tree and self.tree.selection() and not self.selection_removed:
            self.selection_removed = True
            self.tree.selection_remove(*self.tree.selection())
        else:
            self.selection_removed = False

    def add_items_selected(self, event):
        print('INSERTION')
        def assemble(i):
            item = self.tree.item(i)
            values = item['values']
            cps = values[0]
            parent = self.tree.item(self.tree.parent(i))

            return [f"{parent['text']}",f"{item['text']}", f"{values[0]}"]

        selected_items = self.tree.selection()
        if not selected_items:
            selected_items = (event.widget.identify('item',event.x,event.y),)
        self.tree.selection_set('')


        selection = []
        for i in selected_items:
            if not self.tree.get_children(i):
                selection.append(assemble(i))

        for s in selection:
            name, count, cps = s
            self.selection_tree.insert('', tk.END, text=name, open=True, values=(count, cps))

        self.tree.selection_set(selected_items)

        self.update_total_cps()

    def delete_items_selected(self, event):
        print('DELETION')
        selected_items = event.widget.selection()
        if not selected_items:
            event.widget.selection_set(event.widget.identify('item',event.x,event.y))
        for item in selected_items:
            event.widget.selection_remove(item)
            event.widget.delete(item)

        self.update_total_cps()
        self.selection_removed = True

    def update_total_cps(self):
        total_cps = 0
        for item in self.selection_tree.get_children():
            count, cps = self.selection_tree.item(item)['values']
            total_cps += int(cps.split(' ')[0])
        self.total_value['text'] = f'{total_cps}  points'
        self.update()


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

def pre_init():
    pyglet.font.add_file(resource_path('aAtmospheric.ttf'))

if __name__ == '__main__':
    def main():
        app = App()
        app.mainloop()
    main()