from __future__ import annotations
import tkinter as tk
from tkinter import ttk, colorchooser, simpledialog, messagebox
from game.board import Section, SectionType
from typing import List


class SectionCatalog(tk.Toplevel):
    """Shows every section; lets you rename, recolour, retype, delete."""

    def __init__(self, master, sections: List[Section], refresh_cb):
        super().__init__(master)
        self.title("Sections")
        self.geometry("300x400")
        self.sections = sections
        self.refresh_cb = refresh_cb

        self.lb = tk.Listbox(self)
        self.lb.pack(fill="both", expand=True, padx=8, pady=6)
        self._fill()

        btn_f = ttk.Frame(self); btn_f.pack(fill="x", pady=4)
        ttk.Button(btn_f, text="Edit",   command=self._edit).pack(side="left", expand=True, fill="x")
        ttk.Button(btn_f, text="Delete", command=self._delete).pack(side="left", expand=True, fill="x")

    def _fill(self):
        self.lb.delete(0, "end")
        for s in self.sections:
            self.lb.insert("end", f"{s.name}  ({s.kind})")

    def _get_sel(self):
        idxs = self.lb.curselection()
        return self.sections[idxs[0]] if idxs else None

    def _edit(self):
        s = self._get_sel()
        if not s: return
        new_name = simpledialog.askstring("Name", "Section name:", initialvalue=s.name, parent=self)
        if new_name: s.name = new_name
        new_kind = simpledialog.askstring("Type", "card/piece/token/deck/any:",
                                          initialvalue=s.kind.value, parent=self)
        if new_kind:
            s.kind = SectionType(new_kind.capitalize())
        new_out = colorchooser.askcolor(title="Outline", initialcolor=s.outline)[1]
        if new_out: s.outline = new_out
        new_fill = colorchooser.askcolor(title="Fill (cancel = keep empty)",
                                         initialcolor=s.fill or "#ffffff")[1]
        if new_fill: s.fill = new_fill
        self._fill(); self.refresh_cb()

    def _delete(self):
        s = self._get_sel()
        if not s: return
        if messagebox.askyesno("Delete", f"Delete section '{s.name}'?", parent=self):
            self.sections.remove(s)
            self._fill(); self.refresh_cb()
