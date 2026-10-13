"""Interfaz gráfica sencilla para el registro SSH local."""
import tkinter as tk
from tkinter import ttk, filedialog, font as tkfont
import threading
import queue
from pathlib import Path
import storage
from row_drag import RowDrag
from icons import load_icons
from dialogs import center_window, Messages
from connection import prepare_key
from terminal import connect_tab, open_tab

DEFAULTS = {'Ubuntu': 'ubuntu', 'Oracle Linux': 'opc', 'Rocky': 'rocky', 'Otro': ''}

class App:
    def __init__(self, root):
        self.root = root
        root.withdraw()
        self.messages = Messages(root)
        icon_path = Path(__file__).with_name('assets') / 'app-icon.png'
        if icon_path.exists():
            self.app_icon = tk.PhotoImage(master=root, file=str(icon_path)).subsample(4)
            root.iconphoto(True, self.app_icon)
        self.icons = load_icons(root)
        self.tree_icons = {}
        for name in ('folder', 'grip'):
            padded = tk.PhotoImage(master=root, width=22, height=16)
            padded.tk.call(str(padded), 'copy', str(self.icons[name]))
            self.tree_icons[name] = padded
        for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont'):
            tkfont.nametofont(name).configure(size=11)
        self.font_family = tkfont.nametofont('TkDefaultFont').actual('family')
        self.style = ttk.Style(root)
        self.style.configure('Manager.Treeview', font=(self.font_family, 11), rowheight=26)
        self.style.configure('Manager.Treeview.Heading', font=(self.font_family, 10))
        self.style.configure('Caption.TLabel', font=(self.font_family, 10), foreground='#8e8e93')
        self.style.configure('TButton', font=(self.font_family, 11), padding=(4,2))
        self.style.configure('TCombobox', font=(self.font_family, 11))
        root.title('OCI SSH Manager')
        root.geometry('1080x500')
        root.minsize(650, 380)
        self.events = queue.Queue()
        self.filter = tk.StringVar(value='Activas')
        self.folders = []
        self.drop_folder = None
        self.profile = tk.StringVar(value='Pro')
        frame = ttk.Frame(root, padding=16)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)
        ttk.Label(frame, text='Mis máquinas', font=(self.font_family, 16, 'bold')).grid(row=0, column=0, sticky='w')
        bar = ttk.Frame(frame); bar.grid(row=1, column=0, sticky='ew', pady=(12,10))
        ttk.Label(bar, text='Mostrar:', image=self.icons['filter'], compound='left').pack(side='left', padx=(0,8))
        self.filter_menu = ttk.Combobox(bar, textvariable=self.filter, state='readonly', width=20, exportselection=False)
        self.filter_menu.pack(side='left')
        self.filter_menu.bind('<<ComboboxSelected>>', self.filter_changed)
        self.filter_menu.bind('<FocusIn>', lambda event: self.root.after_idle(self.filter_menu.selection_clear))
        ttk.Label(bar, text='Terminal:', image=self.icons['terminal'], compound='left').pack(side='left', padx=(24, 8))
        ttk.Entry(bar, textvariable=self.profile, width=12).pack(side='left')
        self.test_button = self.button(bar, 'Probar', self.test_tab, 'terminal')
        self.test_button.pack(side='left', padx=8)
        toolbar = ttk.Frame(frame); toolbar.grid(row=2, column=0, sticky='ew', pady=(0,8))
        self.button(toolbar, 'Agregar', self.form, 'add').pack(side='left')
        self.button(toolbar, 'Nueva carpeta', self.new_folder, 'folder_add').pack(side='left', padx=4)
        self.button(toolbar, 'Editar', self.edit, 'edit').pack(side='left')
        self.button(toolbar, 'Archivar / Restaurar', self.archive, 'archive').pack(side='left', padx=4)
        self.button(toolbar, 'Actualizar', self.refresh, 'refresh').pack(side='right')
        content = ttk.Frame(frame); content.grid(row=3, column=0, sticky='nsew')
        self.tree = ttk.Treeview(content, columns=('ip', 'os', 'user', 'description', 'state'), selectmode='browse', style='Manager.Treeview')
        self.tree.heading('#0', text='Máquinas'); self.tree.column('#0', width=300, minwidth=100, stretch=False)
        for col, label in [('ip', 'IP'), ('os', 'Sistema'), ('user', 'Usuario'), ('description', 'Descripción'), ('state', 'Estado')]:
            self.tree.heading(col, text=label); self.tree.column(col, width=150, minwidth=50, stretch=False)
        content.rowconfigure(0, weight=1); content.columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(content, orient='vertical', command=self.tree.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(content, orient='horizontal', command=self.tree.xview)
        horizontal.grid(row=1, column=0, sticky='ew')
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.column('description', width=250, minwidth=60)
        self.tree.column('ip', width=150)
        self.tree.column('os', width=105)
        self.tree.column('user', width=85)
        self.tree.column('state', width=85)
        self.drag_row = None
        self.row_animation = None
        self.tree.tag_configure('folder', font=(self.font_family, 11))
        self.tree.tag_configure('drop', background='#dceaff', foreground='#007aff')
        self.tree.tag_configure('dragging', background='#dceaff', foreground='#185abc')
        self.tree.bind('<Escape>', self.drag_cancel)
        self.tree.bind('<Motion>', self.drag_hover)
        self.tree.bind('<ButtonPress-1>', self.drag_start, add='+')
        self.tree.bind('<B1-Motion>', self.drag_move, add='+')
        self.tree.bind('<ButtonRelease-1>', self.drag_end, add='+')
        footer = ttk.Frame(frame); footer.grid(row=4, column=0, sticky='ew', pady=(10,0))
        footer.columnconfigure(0, weight=1)
        self.connect_button = self.button(footer, 'Conectar', self.connect, 'connect')
        self.connect_button.grid(row=0, column=1, sticky='e', padx=(12,0))
        center_window(root)
        root.deiconify()
        self.refresh()
        root.after(100, self.poll)

    def filter_changed(self, event=None):
        self.refresh()
        self.root.after_idle(self.filter_menu.selection_clear)

    def button(self, parent, text, command, icon):
        return ttk.Button(parent, text=text, command=command, image=self.icons[icon], compound='left')

    def refresh(self):
        self.drag_cancel()
        try:
            machines = storage.load()
            folders = storage.load_folders()
        except (ValueError, OSError) as error:
            self.messages.showerror('Registro', str(error)); return
        self.machines = machines
        self.folders = folders
        choices = ['Todas', 'Activas', 'Archivadas'] + ['Carpeta: '+name for name in folders]
        self.filter_menu['values'] = choices
        if self.filter.get() not in choices: self.filter.set('Activas')
        previous_open = {self.folder_targets[row]: self.tree.item(row, 'open') for row in getattr(self, 'folder_targets', {}) if self.tree.exists(row)}
        for row in self.tree.get_children(): self.tree.delete(row)
        self.folder_targets = {}
        parents = {}
        # Las máquinas sin carpeta viven directamente en la raíz.
        for i,m in enumerate(machines):
            if self.matches_filter(m) and not m.get('folder'):
                self.insert_machine('', i, m)
        for i,name in enumerate(folders):
            if self.filter.get().startswith('Carpeta: ') and self.filter.get()[9:] != name: continue
            if not self.filter.get().startswith('Carpeta: ') and not any(self.matches_filter(m) and m.get('folder') == name for m in machines): continue
            iid = f'folder{i}'
            parents[name] = iid
            self.folder_targets[iid] = name
            self.tree.insert('', 'end', iid=iid, text=name, image=self.tree_icons['folder'], open=previous_open.get(name, True), tags=('folder',))
        for i,m in enumerate(machines):
            if self.matches_filter(m) and m.get('folder'):
                self.insert_machine(parents[m['folder']], i, m)

    def insert_machine(self, parent, index, machine):
        self.tree.insert(parent, 'end', iid=str(index), text=machine['name'], image=self.tree_icons['grip'], values=(machine['ip'], machine['os'], machine['user'], machine.get('description', ''), 'Archivada' if machine['archived'] else 'Activa'))

    def matches_filter(self, machine):
        value = self.filter.get()
        if value == 'Todas': return True
        if value == 'Activas': return not machine['archived']
        if value == 'Archivadas': return machine['archived']
        return machine.get('folder', '') == value[9:]

    def new_folder(self):
        dialog = tk.Toplevel(self.root); dialog.withdraw()
        dialog.title('Nueva carpeta'); dialog.transient(self.root)
        frame = ttk.Frame(dialog, padding=20); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Nombre de la carpeta').pack(anchor='w')
        name = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=name, width=36); entry.pack(pady=12)
        def save():
            try:
                folders = storage.load_folders()
                folder = name.get().strip()
                storage.save_folders(folders + [folder])
            except (ValueError, OSError) as error:
                self.messages.showerror('No se creó la carpeta', str(error), parent=dialog); return
            dialog.destroy(); self.filter.set('Carpeta: '+folder); self.refresh()
        buttons = ttk.Frame(frame); buttons.pack(fill='x')
        self.button(buttons, 'Cancelar', dialog.destroy, 'cancel').pack(side='left')
        self.button(buttons, 'Crear', save, 'folder_add').pack(side='right')
        dialog.bind('<Return>', lambda event: save())
        center_window(dialog, self.root); dialog.deiconify(); dialog.grab_set(); entry.focus_set()

    def highlight_folder(self, event):
        self.drop_folder = None
        for iid in getattr(self, 'folder_targets', {}):
            if self.tree.exists(iid): self.tree.item(iid, tags=('folder',))
        if event is None: return
        if 0 <= event.x < self.tree.winfo_width() and 0 <= event.y < self.tree.winfo_height():
            iid = self.tree.identify_row(event.y)
            if iid in self.folder_targets:
                self.drop_folder = self.folder_targets[iid]
                self.tree.item(iid, tags=('folder', 'drop'))
            elif not iid and self.filter.get() in ('Todas', 'Activas', 'Archivadas'):
                self.drop_folder = ''

    def move_to_folder(self, machine, folder):
        self.drag_cancel()
        try:
            current = storage.load()
            index = next((i for i,m in enumerate(current) if m == machine), None)
            if index is None: raise ValueError('El registro cambió; actualiza la lista.')
            if folder and folder not in storage.load_folders(): raise ValueError('La carpeta ya no existe.')
            current[index]['folder'] = folder
            storage.save(current)
            self.refresh()
        except (ValueError, OSError) as error:
            self.messages.showerror('No se movió la máquina', str(error)); self.refresh()

    def drag_hover(self, event):
        if self.tree.identify_region(event.x, event.y) in ('heading', 'separator'): return
        row = self.tree.identify_row(event.y)
        indent = 20 if row and self.tree.parent(row) else 0
        box = self.tree.bbox(row, '#0') if row else ()
        origin = box[0] if box else 0
        handle = row.isdigit() and self.tree.identify_column(event.x) == '#0' and origin+18 <= event.x <= origin+44
        self.tree.configure(cursor='openhand' if handle else '')

    def drag_start(self, event):
        if self.tree.identify_column(event.x) != '#0': return
        row = self.tree.identify_row(event.y)
        if not row.isdigit(): return
        indent = 20 if self.tree.parent(row) else 0
        origin = self.tree.bbox(row, '#0')[0]
        if not origin+18 <= event.x <= origin+44: return
        self.drag_cancel()
        self.drag_row = row
        self.drag_parent = self.tree.parent(row)
        self.drag_order = tuple(item for item in self.tree.get_children(self.drag_parent) if item.isdigit())
        self.drop_index = self.drag_order.index(row)
        self.tree.selection_set(row)
        self.tree.focus_set()
        self.tree.item(row, tags=('dragging',))
        self.tree.configure(cursor='closedhand')
        self.row_animation = RowDrag(self, event)
        return 'break'

    def drag_move(self, event):
        if not self.drag_row: return
        self.highlight_folder(event)
        if self.row_animation and self.drop_folder is None:
            self.row_animation.move(event)
        return 'break'

    def drag_cancel(self, event=None):
        if self.row_animation is not None:
            self.row_animation.destroy()
            self.row_animation = None
        if self.drag_row and self.tree.exists(self.drag_row): self.tree.item(self.drag_row, tags=())
        self.drag_row = None
        self.drop_folder = None
        for iid in getattr(self, 'folder_targets', {}):
            if self.tree.exists(iid): self.tree.item(iid, tags=('folder',))
        self.tree.configure(cursor='')
        return 'break'

    def drag_end(self, event):
        if not self.drag_row or not self.row_animation or self.row_animation.settling: return
        self.highlight_folder(event)
        if self.drop_folder is not None:
            self.move_to_folder(self.machines[int(self.drag_row)], self.drop_folder)
            return 'break'
        if event and not (0 <= event.x <= self.tree.winfo_width() and 0 <= event.y <= self.tree.winfo_height()):
            self.drag_cancel(); return 'break'
        self.row_animation.settle(lambda: self.commit_drag(event))
        return 'break'

    def commit_drag(self, event):
        if not self.drag_row: return
        row = self.drag_row
        if event and not (0 <= event.x <= self.tree.winfo_width() and 0 <= event.y <= self.tree.winfo_height()):
            self.drag_cancel(); return 'break'
        remaining = [item for item in self.drag_order if item != row]
        remaining.insert(self.drop_index, row)
        order = tuple(remaining)
        self.drag_cancel()
        if order == self.drag_order: return 'break'
        name = self.machines[int(row)]['name']
        try:
            current = storage.load()
            if current != self.machines:
                raise ValueError('El registro cambió. Actualiza la lista e intenta de nuevo.')
            visible = iter(self.machines[int(i)] for i in order)
            reordered = [next(visible) if self.matches_filter(m) and m.get('folder', '') == self.machines[int(row)].get('folder', '') else m for m in current]
            storage.save(reordered)
        except (ValueError, OSError) as error:
            self.messages.showerror('No se guardó el orden', str(error))
        self.refresh()
        for i, m in enumerate(self.machines):
            if m['name'] == name and self.tree.exists(str(i)):
                self.tree.selection_set(str(i)); break

    def selected(self):
        selected = self.tree.selection()
        if not selected:
            self.messages.showinfo('Selecciona una máquina', 'Selecciona una fila primero.')
            return None
        if not selected[0].isdigit():
            self.messages.showinfo('Selecciona una máquina', 'Selecciona una máquina dentro de la carpeta.'); return None
        return self.machines[int(selected[0])]

    def edit(self):
        machine = self.selected()
        if machine: self.form(machine)

    def form(self, machine=None):
        # Cancelar Editar sin selección no abre un formulario vacío.
        dialog = tk.Toplevel(self.root); dialog.title('Editar máquina' if machine else 'Agregar máquina')
        dialog.withdraw()
        dialog.transient(self.root)
        frame = ttk.Frame(dialog, padding=20); frame.pack(fill='both', expand=True)
        fields = {}
        for row, (key, label) in enumerate([('name','Nombre'),('ip','IP pública'),('os','Sistema'),('user','Usuario SSH'),('key','Llave privada'),('description','Descripción'),('folder','Carpeta')]):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', pady=6)
            value = machine.get(key, '') if machine else ('Ubuntu' if key == 'os' else 'ubuntu' if key == 'user' else '')
            fields[key] = tk.StringVar(value=value)
            if key == 'os':
                widget = ttk.Combobox(frame, textvariable=fields[key], values=list(DEFAULTS), state='readonly')
                widget.bind('<<ComboboxSelected>>', lambda event: fields['user'].set(DEFAULTS[fields['os'].get()]))
            elif key == 'folder':
                options = ['Raíz'] + ['Carpeta: '+name for name in self.folders]
                if not machine and self.filter.get().startswith('Carpeta: '):
                    value = self.filter.get()[9:]
                fields[key].set('Carpeta: '+value if value else 'Raíz')
                widget = ttk.Combobox(frame, textvariable=fields[key], values=options, state='readonly')
            else: widget = ttk.Entry(frame, textvariable=fields[key], width=42)
            widget.grid(row=row, column=1, sticky='ew', padx=10)
        def browse():
            path = filedialog.askopenfilename(parent=dialog, title='Selecciona la llave privada')
            if path: fields['key'].set(path)
        self.button(frame, 'Elegir…', browse, 'folder').grid(row=4, column=2)
        ttk.Label(frame, text='Guardar aplica permisos 600 a la llave original.').grid(row=7,column=0,columnspan=3,pady=10)
        def save():
            try:
                data = {key: value.get().strip() for key,value in fields.items()}
                data['folder'] = data['folder'][9:] if data['folder'].startswith('Carpeta: ') else ''
                if data['folder'] and data['folder'] not in storage.load_folders():
                    raise ValueError('La carpeta ya no existe. Actualiza el formulario.')
                if not data['key']: raise ValueError('Selecciona una llave privada.')
                data['key'] = str(Path(data['key']).expanduser().absolute())
                data['archived'] = machine['archived'] if machine else False
                storage.validate(data)
                current = storage.load()
                if machine:
                    index = next((i for i,m in enumerate(current) if m == machine), None)
                    if index is None: raise ValueError('El registro cambió. Cierra el formulario y actualiza.')
                else: index = None
                if any(m['name'].casefold() == data['name'].casefold() for i,m in enumerate(current) if i != index):
                    raise ValueError('Ese nombre ya existe.')
                data['key'] = prepare_key(data['key'])
                if index is None: current.append(data)
                else: current[index] = data
                storage.save(current)
            except (ValueError,OSError) as error:
                self.messages.showerror('No se guardó', str(error), parent=dialog); return
            dialog.destroy(); self.refresh()
        self.button(frame, 'Guardar', save, 'save').grid(row=8,column=1,sticky='e')
        self.button(frame, 'Cancelar', dialog.destroy, 'cancel').grid(row=8,column=0)
        center_window(dialog, self.root)
        dialog.deiconify()
        dialog.grab_set()

    def archive(self):
        machine = self.selected()
        if not machine: return
        try:
            current = storage.load()
            index = next((i for i,m in enumerate(current) if m == machine), None)
            if index is None: raise ValueError('El registro cambió; actualiza la lista.')
            current[index]['archived'] = not machine['archived']
            storage.save(current); self.refresh()
        except (ValueError,OSError) as error: self.messages.showerror('Registro',str(error))

    def test_tab(self):
        profile = self.profile.get().strip()
        if not profile:
            self.messages.showerror('Perfil', 'Indica un perfil de Terminal.'); return
        self.start_terminal(lambda: open_tab('printf "%s\\n" "Prueba OCI SSH: pestaña creada. No se inició ninguna conexión."', profile))

    def start_terminal(self, action):
        self.connect_button.state(['disabled']); self.test_button.state(['disabled'])
        def worker():
            try: action(); self.events.put((True,'Pestaña abierta. La sesión continúa en Terminal.'))
            except Exception as error: self.events.put((False,str(error)))
        threading.Thread(target=worker,daemon=True).start()

    def connect(self):
        machine = self.selected()
        if not machine: return
        if machine['archived']:
            self.messages.showinfo('Máquina archivada','Restaura la máquina antes de conectar.'); return
        profile = self.profile.get().strip()
        if not profile:
            self.messages.showerror('Perfil','Indica el nombre del perfil de Terminal.'); return
        self.start_terminal(lambda: connect_tab(machine,profile))

    def poll(self):
        try:
            success, message = self.events.get_nowait()
            self.connect_button.state(['!disabled']); self.test_button.state(['!disabled'])
            if not success: self.messages.showerror('Terminal',message)
        except queue.Empty: pass
        self.root.after(100,self.poll)

if __name__ == '__main__':
    root = tk.Tk(); App(root); root.mainloop()
