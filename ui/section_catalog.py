# ui/section_catalog.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, colorchooser, simpledialog, messagebox
from game.board import Section, SectionType
from typing import List, Union


class SectionCatalog(tk.Toplevel):
    """
    Shows every section (grid or free).  
    Lets you rename, recolour, retype, or delete any section.
    """

    def __init__(self, master, sections: List[Union[Section, dict]], refresh_cb):
        super().__init__(master)
        self.title("Sections")
        self.geometry("300x400")

        # The sections list may contain:
        #  • Section objects (grid boards), OR
        #  • dict entries (free boards) with keys "name","kind","points","outline","fill"
        self.sections = sections
        self.refresh_cb = refresh_cb

        self.lb = tk.Listbox(self)
        self.lb.pack(fill="both", expand=True, padx=8, pady=6)
        self._fill()

        btn_f = ttk.Frame(self)
        btn_f.pack(fill="x", pady=4)
        ttk.Button(btn_f, text="Edit",   command=self._edit).pack(side="left", expand=True, fill="x")
        ttk.Button(btn_f, text="Delete", command=self._delete).pack(side="left", expand=True, fill="x")

    def _fill(self):
        """Refresh the listbox with current section names and types."""
        self.lb.delete(0, "end")
        for s in self.sections:
            # Determine name and kind based on type
            if isinstance(s, dict):
                name = s.get("name", "Area")
                kind = s.get("kind", "Any")
            else:
                name = getattr(s, "name", "Area")
                kind = getattr(s, "kind").value if hasattr(s, "kind") else "Any"
            self.lb.insert("end", f"{name}  ({kind})")

    def _get_sel(self):
        """Return the selected section (Section object or dict)."""
        idxs = self.lb.curselection()
        return self.sections[idxs[0]] if idxs else None

    def _edit(self):
        """Open dialogs to edit the selected section’s properties."""
        s = self._get_sel()
        if not s:
            return

        # ===== NAME =====
        if isinstance(s, dict):
            curr_name = s.get("name", "")
        else:
            curr_name = getattr(s, "name", "")

        new_name = simpledialog.askstring(
            "Name",
            "Section name:",
            initialvalue=curr_name,
            parent=self
        )
        if not new_name:
            # user cancelled or entered empty; leave name unchanged
            pass
        else:
            if isinstance(s, dict):
                s["name"] = new_name
            else:
                s.name = new_name

        # ===== TYPE =====
        if isinstance(s, dict):
            curr_kind = s.get("kind", "Any")
        else:
            curr_kind = getattr(s.kind, "value", "Any")

        new_kind = simpledialog.askstring(
            "Type",
            "card / piece / token / deck / any:",
            initialvalue=curr_kind,
            parent=self
        )
        if new_kind:
            new_kind = new_kind.capitalize()
            if isinstance(s, dict):
                s["kind"] = new_kind
            else:
                s.kind = SectionType(new_kind)

        # ===== OUTLINE COLOR =====
        if isinstance(s, dict):
            curr_out = s.get("outline", "#808080")
        else:
            curr_out = getattr(s, "outline", "#808080")

        new_out = colorchooser.askcolor(
            title="Outline",
            initialcolor=curr_out
        )[1]
        if new_out:
            if isinstance(s, dict):
                s["outline"] = new_out
            else:
                s.outline = new_out

        # ===== FILL COLOR =====
        if isinstance(s, dict):
            curr_fill = s.get("fill", "")
        else:
            curr_fill = getattr(s, "fill", "")

        new_fill = colorchooser.askcolor(
            title="Fill (cancel = keep empty)",
            initialcolor=curr_fill or "#ffffff"
        )[1]
        if new_fill is not None:
            if isinstance(s, dict):
                s["fill"] = new_fill
            else:
                s.fill = new_fill

        # Finish up
        self._fill()
        self.refresh_cb()

    def _delete(self):
        """Remove the selected section from the list."""
        s = self._get_sel()
        if not s:
            return

        # Get the displayed name for confirmation
        if isinstance(s, dict):
            name = s.get("name", "Area")
        else:
            name = getattr(s, "name", "Area")

        if messagebox.askyesno(
            "Delete",
            f"Delete section '{name}'?",
            parent=self
        ):
            self.sections.remove(s)
            self._fill()
            self.refresh_cb()
