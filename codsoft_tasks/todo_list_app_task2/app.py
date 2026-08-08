"""A single-file desktop To-Do List application.

Run with:  python todo_app.py
Requirements: Python 3 with Tkinter (included with most Python installations).
Tasks are saved automatically in todo_tasks.db beside this program.
"""

import sqlite3
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


DB_PATH = Path(__file__).with_name("todo_tasks.db")


class TodoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("My To-Do List")
        self.geometry("960x610")
        self.minsize(760, 480)
        self.configure(bg="#f5f7fb")
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.selected_id = None

        self._create_database()
        self._build_ui()
        self.refresh_tasks()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_database(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                notes TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'Medium',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e6ebf5")
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", "#15233d")])
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
        style.configure("Accent.TButton", background="#2563eb", foreground="white")
        style.map("Accent.TButton", background=[("active", "#1d4ed8")])

        header = tk.Frame(self, bg="#172554", padx=22, pady=17)
        header.pack(fill="x")
        tk.Label(header, text="MY TO-DO LIST", bg="#172554", fg="white", font=("Segoe UI", 19, "bold")).pack(side="left")
        self.summary_label = tk.Label(header, bg="#172554", fg="#bfdbfe", font=("Segoe UI", 10))
        self.summary_label.pack(side="right")

        content = tk.Frame(self, bg="#f5f7fb", padx=20, pady=18)
        content.pack(fill="both", expand=True)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # Editor
        editor = tk.LabelFrame(content, text=" Task details ", bg="#f5f7fb", fg="#172554", font=("Segoe UI", 11, "bold"), padx=14, pady=12)
        editor.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        editor.columnconfigure(0, weight=1)

        self.title_var = tk.StringVar()
        self.due_var = tk.StringVar()
        self.priority_var = tk.StringVar(value="Medium")
        self.status_var = tk.StringVar(value="Ready")

        self._label(editor, "Task title *", 0)
        self.title_entry = ttk.Entry(editor, textvariable=self.title_var, width=31, font=("Segoe UI", 11))
        self.title_entry.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self._label(editor, "Notes", 2)
        self.notes_text = tk.Text(editor, width=31, height=8, font=("Segoe UI", 10), relief="solid", bd=1, wrap="word")
        self.notes_text.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        self._label(editor, "Due date (YYYY-MM-DD)", 4)
        ttk.Entry(editor, textvariable=self.due_var).grid(row=5, column=0, sticky="ew", pady=(0, 12))
        self._label(editor, "Priority", 6)
        ttk.Combobox(editor, textvariable=self.priority_var, values=("High", "Medium", "Low"), state="readonly").grid(row=7, column=0, sticky="ew", pady=(0, 16))

        actions = tk.Frame(editor, bg="#f5f7fb")
        actions.grid(row=8, column=0, sticky="ew")
        ttk.Button(actions, text="Add task", style="Accent.TButton", command=self.add_task).pack(side="left")
        ttk.Button(actions, text="Update", command=self.update_task).pack(side="left", padx=7)
        ttk.Button(actions, text="Clear", command=self.clear_editor).pack(side="left")
        tk.Label(editor, textvariable=self.status_var, bg="#f5f7fb", fg="#475569", wraplength=245, justify="left", font=("Segoe UI", 9)).grid(row=9, column=0, sticky="w", pady=(14, 0))

        # List area
        right = tk.Frame(content, bg="#f5f7fb")
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        toolbar = tk.Frame(right, bg="#f5f7fb")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 9))
        tk.Label(toolbar, text="Show:", bg="#f5f7fb", fg="#334155", font=("Segoe UI", 10)).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        filter_box = ttk.Combobox(toolbar, textvariable=self.filter_var, values=("All", "Active", "Completed", "Overdue"), width=12, state="readonly")
        filter_box.pack(side="left", padx=(6, 14))
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_tasks())
        ttk.Button(toolbar, text="Mark done / undo", command=self.toggle_complete).pack(side="left")
        ttk.Button(toolbar, text="Delete", command=self.delete_task).pack(side="left", padx=7)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_tasks).pack(side="right")

        tree_frame = tk.Frame(right, bg="white", highlightbackground="#dbe3ef", highlightthickness=1)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        columns = ("state", "title", "priority", "due", "created")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        headings = {"state": "Status", "title": "Task", "priority": "Priority", "due": "Due date", "created": "Created"}
        widths = {"state": 105, "title": 260, "priority": 90, "due": 110, "created": 112}
        for col in columns:
            self.tree.heading(col, text=headings[col], command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=widths[col], anchor="w", stretch=(col == "title"))
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.tag_configure("done", foreground="#64748b")
        self.tree.tag_configure("overdue", foreground="#b91c1c")
        self.tree.bind("<<TreeviewSelect>>", self.load_selected_task)
        self.tree.bind("<Double-1>", lambda _event: self.toggle_complete())
        self.bind("<Return>", lambda _event: self.add_task() if not self.selected_id else self.update_task())

    @staticmethod
    def _label(parent, text, row):
        tk.Label(parent, text=text, bg="#f5f7fb", fg="#334155", font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 4))

    def validated_values(self):
        title = self.title_var.get().strip()
        due = self.due_var.get().strip()
        if not title:
            messagebox.showwarning("Task title needed", "Please enter a task title.")
            self.title_entry.focus_set()
            return None
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Invalid due date", "Use the format YYYY-MM-DD, for example 2026-08-15.")
                return None
        return title, self.notes_text.get("1.0", "end-1c").strip(), due, self.priority_var.get()

    def add_task(self):
        values = self.validated_values()
        if not values:
            return
        self.conn.execute("INSERT INTO tasks (title, notes, due_date, priority, created_at) VALUES (?, ?, ?, ?, ?)", (*values, datetime.now().strftime("%Y-%m-%d")))
        self.conn.commit()
        self.clear_editor("Task added.")
        self.refresh_tasks()

    def update_task(self):
        if not self.selected_id:
            messagebox.showinfo("Select a task", "Select a task from the list before updating it.")
            return
        values = self.validated_values()
        if not values:
            return
        self.conn.execute("UPDATE tasks SET title=?, notes=?, due_date=?, priority=? WHERE id=?", (*values, self.selected_id))
        self.conn.commit()
        self.status_var.set("Task updated.")
        self.refresh_tasks(select_id=self.selected_id)

    def delete_task(self):
        if not self.selected_id:
            messagebox.showinfo("Select a task", "Select a task from the list first.")
            return
        if messagebox.askyesno("Delete task", "Permanently delete the selected task?"):
            self.conn.execute("DELETE FROM tasks WHERE id=?", (self.selected_id,))
            self.conn.commit()
            self.clear_editor("Task deleted.")
            self.refresh_tasks()

    def toggle_complete(self):
        if not self.selected_id:
            messagebox.showinfo("Select a task", "Select a task from the list first.")
            return
        row = self.conn.execute("SELECT completed FROM tasks WHERE id=?", (self.selected_id,)).fetchone()
        new_state = 0 if row["completed"] else 1
        self.conn.execute("UPDATE tasks SET completed=? WHERE id=?", (new_state, self.selected_id))
        self.conn.commit()
        self.status_var.set("Task marked completed." if new_state else "Task marked active.")
        self.refresh_tasks(select_id=self.selected_id)

    def refresh_tasks(self, select_id=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY completed, CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, CASE WHEN due_date='' THEN '9999-12-31' ELSE due_date END, id DESC").fetchall()
        today = date.today().isoformat()
        view = self.filter_var.get()
        visible = 0
        completed_count = self.conn.execute("SELECT COUNT(*) FROM tasks WHERE completed=1").fetchone()[0]
        total = self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        for row in rows:
            overdue = bool(row["due_date"] and row["due_date"] < today and not row["completed"])
            if view == "Active" and row["completed"]: continue
            if view == "Completed" and not row["completed"]: continue
            if view == "Overdue" and not overdue: continue
            state = "✓ Completed" if row["completed"] else ("! Overdue" if overdue else "○ Active")
            tag = "done" if row["completed"] else ("overdue" if overdue else "")
            self.tree.insert("", "end", iid=str(row["id"]), values=(state, row["title"], row["priority"], row["due_date"] or "—", row["created_at"]), tags=(tag,))
            visible += 1
        self.summary_label.config(text=f"{completed_count} of {total} tasks completed  •  {visible} shown")
        if select_id and self.tree.exists(str(select_id)):
            self.tree.selection_set(str(select_id))
            self.tree.focus(str(select_id))

    def load_selected_task(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_id = int(selected[0])
        row = self.conn.execute("SELECT * FROM tasks WHERE id=?", (self.selected_id,)).fetchone()
        self.title_var.set(row["title"])
        self.due_var.set(row["due_date"])
        self.priority_var.set(row["priority"])
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", row["notes"])
        self.status_var.set(f"Editing task #{self.selected_id}. Update, mark done, or delete it.")

    def clear_editor(self, message="Ready"):
        self.selected_id = None
        self.title_var.set("")
        self.due_var.set("")
        self.priority_var.set("Medium")
        self.notes_text.delete("1.0", "end")
        self.tree.selection_remove(self.tree.selection())
        self.status_var.set(message)
        self.title_entry.focus_set()

    def sort_by(self, column):
        # Sorting the currently displayed rows makes it easy to browse any column.
        values = [(self.tree.set(item, column), item) for item in self.tree.get_children("")]
        reverse = getattr(self, "_sort_column", None) == column and not getattr(self, "_sort_reverse", False)
        values.sort(reverse=reverse, key=lambda pair: pair[0].lower())
        for position, (_, item) in enumerate(values):
            self.tree.move(item, "", position)
        self._sort_column, self._sort_reverse = column, reverse

    def on_close(self):
        self.conn.close()
        self.destroy()


if __name__ == "__main__":
    TodoApp().mainloop()
