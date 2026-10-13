"""Posición consistente de la app y sus ventanas emergentes."""
import tkinter as tk
from tkinter import ttk

def center_window(window, parent=None):
    window.update_idletasks()
    width, height = window.winfo_width(), window.winfo_height()
    if width <= 1: width = window.winfo_reqwidth()
    if height <= 1: height = window.winfo_reqheight()
    if parent is None:
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
    else:
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry(f'+{x}+{y}')

class Messages:
    def __init__(self, root):
        self.root = root

    def showinfo(self, title, message, parent=None):
        parent = parent or self.root
        dialog = tk.Toplevel(parent)
        dialog.withdraw()
        dialog.title(title)
        dialog.transient(parent)
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=message, wraplength=440, justify='left').pack(fill='x', pady=(0,18))
        button = ttk.Button(frame, text='Aceptar', command=dialog.destroy)
        button.pack(anchor='e')
        dialog.bind('<Return>', lambda event: dialog.destroy())
        dialog.bind('<Escape>', lambda event: dialog.destroy())
        previous_grab = parent.grab_current()
        center_window(dialog, parent)
        dialog.deiconify()
        dialog.grab_set()
        button.focus_set()
        parent.wait_window(dialog)
        if previous_grab and previous_grab.winfo_exists():
            previous_grab.grab_set()

    showerror = showinfo
