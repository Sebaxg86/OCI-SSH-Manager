"""Animación de las filas completas durante el reordenamiento."""
import tkinter as tk
from tkinter import font as tkfont

class RowDrag:
    def __init__(self, app, event):
        self.app = app
        self.tree = app.tree
        self.rows = app.drag_order
        self.source = app.drag_row
        box = self.tree.bbox(self.source)
        self.height = box[3]
        def visible_rows(parent=''):
            rows = []
            for row in self.tree.get_children(parent):
                rows.append(row)
                if self.tree.item(row, 'open'): rows.extend(visible_rows(row))
            return rows
        self.display_rows = visible_rows()
        first = next(self.tree.bbox(row) for row in self.display_rows if self.tree.bbox(row))
        self.body_top = first[1]
        self.offset = box[1] - self.rows.index(self.source) * self.height
        self.grab_offset = event.y - box[1]
        self.source_goal = float(box[1])
        self.global_offset = box[1] - self.display_rows.index(self.source)*self.height
        self.positions = {row: float(self.global_offset + i*self.height) for i,row in enumerate(self.display_rows)}
        self.timer = self.finish_timer = None
        self.settling = False
        style = app.style
        tree_style = self.tree.cget('style') or 'Treeview'
        bg = style.lookup(tree_style, 'fieldbackground') or '#ffffff'
        fg = style.lookup(tree_style, 'foreground') or '#202124'
        self.font = tkfont.Font(font=style.lookup(tree_style, 'font') or 'TkDefaultFont')
        self.surface = tk.Canvas(self.tree, highlightthickness=0, background=bg, cursor='closedhand')
        self.surface.place(x=1, y=self.body_top, relwidth=1, height=self.tree.winfo_height()-self.body_top-1)
        self.items = {}
        self.backgrounds = {}
        self.background = bg
        columns = ['#0'] + list(self.tree['columns'])
        widths = [self.tree.column(column, 'width') for column in columns]
        width = self.tree.winfo_width()
        for row in self.display_rows:
            group = 'row'+row
            y = self.positions[row] - self.body_top
            source = row == self.source
            self.backgrounds[row] = self.surface.create_rectangle(0,y,width,y+self.height, fill='#dceaff' if source else bg, outline='',tags=group)
            label = self.tree.item(row,'text')

            values = [label] + list(self.tree.item(row,'values'))
            x = self.tree.bbox(self.source, '#0')[0] - (20 if self.tree.parent(self.source) else 0)
            for column_index, (value, cell_width) in enumerate(zip(values,widths)):
                indent = 20 if column_index == 0 and self.tree.parent(row) else 0
                icon_space = 34 if column_index == 0 else 0
                if column_index == 0:
                    icon = app.icons['folder' if row in app.folder_targets else 'grip']
                    self.surface.create_image(x+20+indent,y+self.height/2,image=icon,tags=group)
                    if row in app.folder_targets:
                        cx=x+7+indent; cy=y+self.height/2
                        points=(cx-3,cy-2,cx,cy+1,cx+3,cy-2) if self.tree.item(row,'open') else (cx-2,cy-3,cx+1,cy,cx-2,cy+3)
                        self.surface.create_line(*points,fill=fg,width=1.2,tags=group)
                text = str(value)
                while text and self.font.measure(text) > cell_width-16-indent-icon_space:
                    text = text[:-2]+'…' if len(text)>2 else ''
                self.surface.create_text(x+8+indent+icon_space,y+self.height/2,text=text,anchor='w',font=self.font,fill='#185abc' if source else fg,tags=group)
                x += cell_width
            if source:
                self.surface.create_line(0,y+self.height-1,width,y+self.height-1,fill='#007aff',tags=group)
            self.items[row] = group
        self.surface.tag_raise(self.items[self.source])
        self.surface.bind('<B1-Motion>', self.motion)
        self.surface.bind('<ButtonRelease-1>', self.release)
        self.surface.bind('<Escape>', app.drag_cancel)
        self.surface.bind('<MouseWheel>', lambda event: 'break')
        self.surface.focus_set()
        self.move(event)
        self.animate()

    def translate(self,event):
        # Coordenadas de la tabla, incluso cuando el cursor está sobre la fila.
        from types import SimpleNamespace
        return SimpleNamespace(x=event.x_root-self.tree.winfo_rootx(), y=event.y_root-self.tree.winfo_rooty())

    def motion(self,event):
        self.app.drag_move(self.translate(event)); return 'break'

    def release(self,event):
        self.app.drag_end(self.translate(event)); return 'break'

    def move(self,event):
        if self.settling: return
        if event.y < self.body_top+10: self.tree.yview_scroll(-1,'units')
        elif event.y > self.tree.winfo_height()-20: self.tree.yview_scroll(1,'units')
        for i,row in enumerate(self.display_rows):
            box = self.tree.bbox(row)
            if box:
                self.global_offset = box[1]-i*self.height
                self.offset = self.global_offset+self.display_rows.index(self.rows[0])*self.height
                break
        self.source_goal = max(self.body_top, min(event.y-self.grab_offset,self.tree.winfo_height()-self.height))
        index = round((self.source_goal-self.offset)/self.height)
        self.app.drop_index = max(0,min(index,len(self.rows)-1))

    def animate(self):
        remaining = [row for row in self.rows if row != self.source]
        remaining.insert(self.app.drop_index,self.source)
        sibling_goals = {row:self.offset+index*self.height for index,row in enumerate(remaining)}
        for index,row in enumerate(self.display_rows):
            goal = self.source_goal if row == self.source else sibling_goals.get(row,self.global_offset+index*self.height)
            highlight = row == self.source or 'drop' in self.tree.item(row,'tags')
            self.surface.itemconfigure(self.backgrounds[row],fill='#dceaff' if highlight else self.background)
            old = self.positions[row]
            new = old+(goal-old)*0.32
            self.positions[row] = new
            self.surface.move(self.items[row],0,new-old)
        self.timer = self.app.root.after(16,self.animate)

    def settle(self,callback):
        self.settling = True
        self.source_goal = self.offset+self.app.drop_index*self.height
        self.finish_timer = self.app.root.after(180,callback)

    def destroy(self):
        for timer in (self.timer,self.finish_timer):
            if timer is not None: self.app.root.after_cancel(timer)
        self.surface.destroy()
