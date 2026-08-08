"""Single-file To-Do web application (Python backend + HTML/CSS/JS frontend).

Run:  python todo_web_app.py
Then open: http://127.0.0.1:8000
No third-party packages are required. Tasks persist in todo_web_tasks.db.
"""

import json
import sqlite3
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DATABASE = Path(__file__).with_name("todo_web_tasks.db")


def db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def setup_database():
    with db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                due_date TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'Medium',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TaskFlow | To-Do List</title>
<style>
:root{--ink:#18233f;--blue:#3563e9;--pale:#f4f7ff;--line:#e1e7f2;--muted:#69758d;--red:#d24242}*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:var(--pale);color:var(--ink)}header{background:#172554;color:#fff;padding:24px max(24px,calc((100% - 1120px)/2));display:flex;justify-content:space-between;align-items:center}h1{margin:0;font-size:25px;letter-spacing:-.5px}header p{margin:4px 0 0;color:#cbd8ff;font-size:14px}.wrap{max-width:1120px;margin:28px auto;padding:0 20px;display:grid;grid-template-columns:330px 1fr;gap:24px}.card{background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:0 5px 18px #24345b0b;padding:22px}.card h2{font-size:17px;margin:0 0 19px}label{display:block;font-size:13px;font-weight:700;margin:13px 0 6px;color:#46536a}input,textarea,select{width:100%;border:1px solid #ccd5e5;border-radius:8px;padding:10px;font:inherit;color:var(--ink);background:#fff}textarea{resize:vertical;min-height:102px}input:focus,textarea:focus,select:focus{outline:3px solid #dbe7ff;border-color:var(--blue)}.row{display:flex;gap:10px}.row>*{flex:1}button{border:0;border-radius:8px;padding:10px 13px;font:600 14px Inter,Segoe UI,Arial,sans-serif;cursor:pointer;background:#e9eef8;color:#263650}button:hover{filter:brightness(.97)}button.primary{background:var(--blue);color:white}.form-actions{display:flex;gap:8px;margin-top:18px}.form-actions button{flex:1}.toolbar{display:flex;gap:9px;align-items:center;margin-bottom:15px}.toolbar select{width:130px;padding:8px}.toolbar .summary{margin-left:auto;color:var(--muted);font-size:13px}.task{border:1px solid var(--line);border-left:5px solid #94a3b8;border-radius:10px;padding:15px;margin:10px 0;display:flex;gap:13px;align-items:flex-start}.task.high{border-left-color:#e15151}.task.medium{border-left-color:#e6a628}.task.low{border-left-color:#48a66d}.task.done{opacity:.63;border-left-color:#8090a9}.check{width:21px;height:21px;margin-top:2px;accent-color:var(--blue);cursor:pointer}.task-body{min-width:0;flex:1}.task-title{font-weight:750;font-size:16px;overflow-wrap:anywhere}.done .task-title{text-decoration:line-through}.notes{font-size:13px;color:var(--muted);white-space:pre-wrap;margin-top:5px;line-height:1.4}.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}.tag{font-size:11px;font-weight:700;border-radius:20px;padding:4px 8px;background:#edf1f7;color:#526078}.tag.overdue{background:#fee2e2;color:#b42318}.task-actions{display:flex;gap:5px}.icon{padding:7px 9px;background:transparent;color:#526078}.icon.delete{color:var(--red)}.empty{text-align:center;padding:55px 10px;color:var(--muted)}.empty b{display:block;color:var(--ink);font-size:17px;margin-bottom:7px}@media(max-width:760px){header{padding:20px}.wrap{grid-template-columns:1fr;margin-top:18px;padding:0 14px}.task-actions{flex-direction:column}.toolbar{flex-wrap:wrap}.toolbar .summary{margin-left:0;width:100%}}
</style></head><body>
<header><div><h1>TaskFlow</h1><p>A simple, focused place for your work.</p></div><strong id="headerCount">0 tasks</strong></header>
<main class="wrap"><section class="card"><h2 id="formTitle">Add a task</h2><form id="taskForm"><label for="title">Task title *</label><input id="title" maxlength="200" required placeholder="e.g. Prepare project report" autofocus><label for="notes">Notes</label><textarea id="notes" maxlength="3000" placeholder="Add helpful details (optional)"></textarea><div class="row"><div><label for="due">Due date</label><input id="due" type="date"></div><div><label for="priority">Priority</label><select id="priority"><option>High</option><option selected>Medium</option><option>Low</option></select></div></div><div class="form-actions"><button class="primary" id="saveButton" type="submit">Add task</button><button type="button" id="cancelButton" hidden>Cancel</button></div></form></section>
<section class="card"><div class="toolbar"><strong>Your tasks</strong><select id="filter"><option value="all">All tasks</option><option value="active">Active</option><option value="completed">Completed</option><option value="overdue">Overdue</option></select><span class="summary" id="summary"></span></div><div id="list"></div></section></main>
<script>
let tasks=[],editingId=null;const $=id=>document.getElementById(id);const esc=s=>String(s||'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
async function api(url,options={}){const response=await fetch(url,{headers:{'Content-Type':'application/json'},...options});const data=await response.json();if(!response.ok)throw new Error(data.error||'Something went wrong');return data}
async function load(){tasks=await api('/api/tasks');render()}
function render(){const filter=$('filter').value,today=new Date().toISOString().slice(0,10),visible=tasks.filter(t=>filter==='all'||filter==='active'&&!t.completed||filter==='completed'&&t.completed||filter==='overdue'&&!t.completed&&t.due_date&&t.due_date<today);const complete=tasks.filter(t=>t.completed).length;$('summary').textContent=`${complete} of ${tasks.length} completed`;$('headerCount').textContent=`${tasks.length} task${tasks.length===1?'':'s'}`;const list=$('list');if(!visible.length){list.innerHTML='<div class="empty"><b>No tasks here</b>Add a task or choose a different filter.</div>';return}list.innerHTML=visible.map(t=>{const overdue=!t.completed&&t.due_date&&t.due_date<today;return `<article class="task ${t.priority.toLowerCase()} ${t.completed?'done':''}"><input class="check" type="checkbox" ${t.completed?'checked':''} onchange="toggle(${t.id},this.checked)" aria-label="Toggle task"><div class="task-body"><div class="task-title">${esc(t.title)}</div>${t.notes?`<div class="notes">${esc(t.notes)}</div>`:''}<div class="tags"><span class="tag">${esc(t.priority)} priority</span>${t.due_date?`<span class="tag ${overdue?'overdue':''}">${overdue?'Overdue · ':''}Due ${esc(t.due_date)}</span>`:''}</div></div><div class="task-actions"><button class="icon" onclick="editTask(${t.id})">Edit</button><button class="icon delete" onclick="removeTask(${t.id})">Delete</button></div></article>`}).join('')}
$('taskForm').addEventListener('submit',async e=>{e.preventDefault();const payload={title:$('title').value.trim(),notes:$('notes').value.trim(),due_date:$('due').value,priority:$('priority').value};if(!payload.title)return;try{if(editingId)await api('/api/tasks/'+editingId,{method:'PUT',body:JSON.stringify(payload)});else await api('/api/tasks',{method:'POST',body:JSON.stringify(payload)});reset();load()}catch(e){alert(e.message)}});
function editTask(id){const t=tasks.find(x=>x.id===id);editingId=id;$('formTitle').textContent='Edit task';$('saveButton').textContent='Save changes';$('cancelButton').hidden=false;$('title').value=t.title;$('notes').value=t.notes;$('due').value=t.due_date;$('priority').value=t.priority;$('title').focus();scrollTo({top:0,behavior:'smooth'})}function reset(){editingId=null;$('taskForm').reset();$('priority').value='Medium';$('formTitle').textContent='Add a task';$('saveButton').textContent='Add task';$('cancelButton').hidden=true}$('cancelButton').onclick=reset;
async function toggle(id,completed){try{await api('/api/tasks/'+id,{method:'PUT',body:JSON.stringify({completed})});load()}catch(e){alert(e.message)}}async function removeTask(id){if(confirm('Delete this task permanently?')){try{await api('/api/tasks/'+id,{method:'DELETE'});if(editingId===id)reset();load()}catch(e){alert(e.message)}}}$('filter').onchange=render;load().catch(e=>alert(e.message));
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON request.")

    @staticmethod
    def validate(payload, existing=None):
        title = payload.get("title", existing["title"] if existing else "")
        notes = payload.get("notes", existing["notes"] if existing else "")
        due = payload.get("due_date", existing["due_date"] if existing else "")
        priority = payload.get("priority", existing["priority"] if existing else "Medium")
        if not isinstance(title, str) or not title.strip(): raise ValueError("A task title is required.")
        if len(title.strip()) > 200 or not isinstance(notes, str) or len(notes) > 3000: raise ValueError("Task text is too long.")
        if due:
            try: datetime.strptime(due, "%Y-%m-%d")
            except ValueError: raise ValueError("Due date must be YYYY-MM-DD.")
        if priority not in ("High", "Medium", "Low"): raise ValueError("Invalid priority.")
        return title.strip(), notes.strip(), due, priority

    def do_GET(self):
        if urlparse(self.path).path == "/":
            body = PAGE.encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        elif self.path == "/api/tasks":
            with db_connection() as conn:
                rows = conn.execute("SELECT * FROM tasks ORDER BY completed, CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, CASE WHEN due_date='' THEN '9999-12-31' ELSE due_date END, id DESC").fetchall()
            self.send_json([dict(row) for row in rows])
        else: self.send_json({"error":"Not found"}, 404)

    def do_POST(self):
        if self.path != "/api/tasks": return self.send_json({"error":"Not found"}, 404)
        try:
            title, notes, due, priority = self.validate(self.read_json())
            with db_connection() as conn:
                cursor = conn.execute("INSERT INTO tasks(title,notes,due_date,priority,created_at) VALUES(?,?,?,?,?)", (title, notes, due, priority, date.today().isoformat()))
            self.send_json({"id": cursor.lastrowid}, 201)
        except ValueError as error: self.send_json({"error":str(error)}, 400)

    def do_PUT(self):
        try: task_id = int(self.path.rsplit("/", 1)[1])
        except ValueError: return self.send_json({"error":"Not found"}, 404)
        try:
            payload = self.read_json()
            with db_connection() as conn:
                current = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
                if not current: return self.send_json({"error":"Task not found"}, 404)
                if "completed" in payload:
                    conn.execute("UPDATE tasks SET completed=? WHERE id=?", (1 if payload["completed"] else 0, task_id))
                else:
                    title, notes, due, priority = self.validate(payload, current)
                    conn.execute("UPDATE tasks SET title=?,notes=?,due_date=?,priority=? WHERE id=?", (title,notes,due,priority,task_id))
            self.send_json({"ok":True})
        except (ValueError, TypeError) as error: self.send_json({"error":str(error)}, 400)

    def do_DELETE(self):
        try: task_id = int(self.path.rsplit("/", 1)[1])
        except ValueError: return self.send_json({"error":"Not found"}, 404)
        with db_connection() as conn:
            if not conn.execute("DELETE FROM tasks WHERE id=?", (task_id,)).rowcount: return self.send_json({"error":"Task not found"}, 404)
        self.send_json({"ok":True})


if __name__ == "__main__":
    setup_database()
    port = 8000
    print(f"To-Do List running at http://127.0.0.1:{port}  (press Ctrl+C to stop)")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
