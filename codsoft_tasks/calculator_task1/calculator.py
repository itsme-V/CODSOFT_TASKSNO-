import tkinter as tk
import math

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro Calculator")
        self.root.geometry("750x650")
        self.root.resizable(False, False)
        
        self.is_dark_mode = True
        self.memory_val = 0.0
        self.angle_mode = 'deg'  
        
       
        self.colors_dark = {
            'bg': '#17181A',
            'display_bg': '#17181A',
            'display_fg': '#FFFFFF',
            'num_bg': '#222427', 'num_fg': '#FFFFFF', 'num_hover': '#32353A',
            'op_bg': '#FF9F0A', 'op_fg': '#FFFFFF', 'op_hover': '#FFB23D',
            'sci_bg': '#333538', 'sci_fg': '#FFFFFF', 'sci_hover': '#43464A',
            'sys_bg': '#A5A5A5', 'sys_fg': '#000000', 'sys_hover': '#C0C0C0',
            'history_bg': '#222427', 'history_fg': '#FFFFFF'
        }
        
        
        self.colors_light = {
            'bg': '#F3F3F3',
            'display_bg': '#F3F3F3',
            'display_fg': '#000000',
            'num_bg': '#FFFFFF', 'num_fg': '#000000', 'num_hover': '#EAEAEA',
            'op_bg': '#FF9F0A', 'op_fg': '#FFFFFF', 'op_hover': '#FFB23D',
            'sci_bg': '#EAEAEA', 'sci_fg': '#000000', 'sci_hover': '#D4D4D4',
            'sys_bg': '#D4D4D4', 'sys_fg': '#000000', 'sys_hover': '#C4C4C4',
            'history_bg': '#FFFFFF', 'history_fg': '#000000'
        }
        
        self.colors = self.colors_dark
        self.root.configure(bg=self.colors['bg'])
        
        
        self.left_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.left_frame.pack(side="left", fill="both", expand=True)
        
        self.right_frame = tk.Frame(self.root, bg=self.colors['bg'], width=250)
        self.right_frame.pack(side="right", fill="y")
        self.right_frame.pack_propagate(False)
        
        
        self.top_bar = tk.Frame(self.left_frame, bg=self.colors['bg'])
        self.top_bar.pack(fill="x", padx=10, pady=10)
        
        self.theme_btn = tk.Button(self.top_bar, text="☀ Light Mode", font=("Helvetica", 10, "bold"), 
                                   command=self.toggle_theme, bg=self.colors['sys_bg'], fg=self.colors['sys_fg'],
                                   borderwidth=0, relief="flat", cursor="hand2", padx=10, pady=5)
        self.theme_btn.pack(side="left")
        
        self.angle_btn = tk.Button(self.top_bar, text="Mode: DEG", font=("Helvetica", 10, "bold"), 
                                   command=self.toggle_angle, bg=self.colors['sys_bg'], fg=self.colors['sys_fg'],
                                   borderwidth=0, relief="flat", cursor="hand2", padx=10, pady=5)
        self.angle_btn.pack(side="right")
        
        
        self.display_frame = tk.Frame(self.left_frame, bg=self.colors['bg'])
        self.display_frame.pack(fill="both", pady=(5, 10))
        
        self.display = tk.Entry(
            self.display_frame,
            font=("Helvetica", 38),
            bg=self.colors['display_bg'],
            fg=self.colors['display_fg'],
            borderwidth=0,
            justify="right",
            insertbackground=self.colors['display_fg']
        )
        self.display.pack(fill="both", padx=20, pady=10)
        self.display.focus_set()
        
        
        self.history_label = tk.Label(self.right_frame, text="History", font=("Helvetica", 14, "bold"), 
                                      bg=self.colors['bg'], fg=self.colors['display_fg'])
        self.history_label.pack(pady=(15, 5))
        
        self.history_text = tk.Text(self.right_frame, font=("Helvetica", 12), bg=self.colors['history_bg'],
                                    fg=self.colors['history_fg'], borderwidth=0, state=tk.DISABLED, wrap=tk.WORD)
        self.history_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        
        self.buttons_frame = tk.Frame(self.left_frame, bg=self.colors['bg'])
        self.buttons_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.button_widgets = []
        self.create_buttons()
        
        
        self.root.bind('<Return>', self.calculate)
        self.root.bind('<Escape>', lambda e: self.clear())
        self.display.bind('<Key>', self.key_handler)
        
    def create_buttons(self):
        
        buttons = [
            ('MC', 'sys', self.mem_clear), ('MR', 'sys', self.mem_recall), ('M+', 'sys', self.mem_add), ('M-', 'sys', self.mem_sub),
            ('C', 'sys', self.clear), ('(', 'sys', lambda: self.btn_click('(')), (')', 'sys', lambda: self.btn_click(')')), ('DEL', 'sys', self.delete_last),
            ('sin', 'sci', lambda: self.btn_click('sin')), ('cos', 'sci', lambda: self.btn_click('cos')), ('tan', 'sci', lambda: self.btn_click('tan')), ('sqrt', 'sci', lambda: self.btn_click('sqrt')),
            ('log', 'sci', lambda: self.btn_click('log')), ('π', 'sci', lambda: self.btn_click('π')), ('e', 'sci', lambda: self.btn_click('e')), ('^', 'sci', lambda: self.btn_click('^')),
            ('7', 'num', lambda: self.btn_click('7')), ('8', 'num', lambda: self.btn_click('8')), ('9', 'num', lambda: self.btn_click('9')), ('÷', 'op', lambda: self.btn_click('÷')),
            ('4', 'num', lambda: self.btn_click('4')), ('5', 'num', lambda: self.btn_click('5')), ('6', 'num', lambda: self.btn_click('6')), ('×', 'op', lambda: self.btn_click('×')),
            ('1', 'num', lambda: self.btn_click('1')), ('2', 'num', lambda: self.btn_click('2')), ('3', 'num', lambda: self.btn_click('3')), ('-', 'op', lambda: self.btn_click('-')),
            ('.', 'num', lambda: self.btn_click('.')), ('0', 'num', lambda: self.btn_click('0')), ('=', 'op', self.calculate), ('+', 'op', lambda: self.btn_click('+')),
        ]
        
        row_val = 0
        col_val = 0
        
        for text, btype, command in buttons:
            bg_color = self.colors[f'{btype}_bg']
            fg_color = self.colors[f'{btype}_fg']
            
            btn = tk.Button(
                self.buttons_frame, text=text, bg=bg_color, fg=fg_color,
                font=("Helvetica", 15, "bold"), borderwidth=0, relief="flat",
                command=command, cursor="hand2"
            )
            btn.grid(row=row_val, column=col_val, sticky="nsew", padx=3, pady=3)
            
            self.create_hover_effect(btn, btype)
            self.button_widgets.append((btn, btype))
            
            col_val += 1
            if col_val > 3:
                col_val = 0
                row_val += 1

        for i in range(4):
            self.buttons_frame.grid_columnconfigure(i, weight=1)
        for i in range(8):
            self.buttons_frame.grid_rowconfigure(i, weight=1)
            
    def create_hover_effect(self, btn, btype):
        btn.bind("<Enter>", lambda e, bt=btype: e.widget.config(bg=self.colors[f'{bt}_hover']))
        btn.bind("<Leave>", lambda e, bt=btype: e.widget.config(bg=self.colors[f'{bt}_bg']))

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.colors = self.colors_dark if self.is_dark_mode else self.colors_light
        
        self.root.configure(bg=self.colors['bg'])
        self.left_frame.configure(bg=self.colors['bg'])
        self.right_frame.configure(bg=self.colors['bg'])
        self.top_bar.configure(bg=self.colors['bg'])
        self.display_frame.configure(bg=self.colors['bg'])
        self.buttons_frame.configure(bg=self.colors['bg'])
        
        self.theme_btn.configure(
            text="☀ Light Mode" if self.is_dark_mode else "🌙 Dark Mode",
            bg=self.colors['sys_bg'], fg=self.colors['sys_fg']
        )
        self.angle_btn.configure(
            bg=self.colors['sys_bg'], fg=self.colors['sys_fg']
        )
        
        self.display.configure(
            bg=self.colors['display_bg'], fg=self.colors['display_fg'],
            insertbackground=self.colors['display_fg']
        )
        
        self.history_label.configure(bg=self.colors['bg'], fg=self.colors['display_fg'])
        self.history_text.configure(bg=self.colors['history_bg'], fg=self.colors['history_fg'])
        
        for btn, btype in self.button_widgets:
            btn.configure(
                bg=self.colors[f'{btype}_bg'],
                fg=self.colors[f'{btype}_fg'],
                activebackground=self.colors[f'{btype}_hover'],
                activeforeground=self.colors[f'{btype}_fg']
            )

    def toggle_angle(self):
        if self.angle_mode == 'deg':
            self.angle_mode = 'rad'
            self.angle_btn.config(text="Mode: RAD")
        else:
            self.angle_mode = 'deg'
            self.angle_btn.config(text="Mode: DEG")

    
    def mem_clear(self): 
        self.memory_val = 0.0
        
    def mem_recall(self): 
        self.btn_click(str(self.memory_val))
        
    def mem_add(self):
        try:
            val = float(self.safe_eval(self.display.get()))
            self.memory_val += val
        except: pass
        
    def mem_sub(self):
        try:
            val = float(self.safe_eval(self.display.get()))
            self.memory_val -= val
        except: pass

    
    def safe_eval(self, expr):
        expr = expr.replace('^', '**').replace('÷', '/').replace('×', '*').replace('π', 'pi')
        
        
        def safe_sin(x): return math.sin(math.radians(x)) if self.angle_mode == 'deg' else math.sin(x)
        def safe_cos(x): return math.cos(math.radians(x)) if self.angle_mode == 'deg' else math.cos(x)
        def safe_tan(x): return math.tan(math.radians(x)) if self.angle_mode == 'deg' else math.tan(x)
        
        allowed = {
            'sin': safe_sin,
            'cos': safe_cos,
            'tan': safe_tan,
            'log': math.log10, 'ln': math.log, 'sqrt': math.sqrt,
            'pi': math.pi, 'e': math.e, 'abs': abs,
        }
        return eval(expr, {"__builtins__": {}}, allowed)

    def calculate(self, event=None):
        expr = self.display.get()
        if not expr: return
        try:
            result = self.safe_eval(expr)
            
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            
            result_str = str(round(result, 8)) if isinstance(result, float) else str(result)
                
            self.display.delete(0, tk.END)
            self.display.insert(0, result_str)
            
        
            mode_tag = f" ({self.angle_mode.upper()})" if any(trig in expr for trig in ['sin', 'cos', 'tan']) else ""
            
            self.history_text.config(state=tk.NORMAL)
            self.history_text.insert(tk.END, f"{expr}{mode_tag}\n= {result_str}\n\n")
            self.history_text.see(tk.END)
            self.history_text.config(state=tk.DISABLED)
            
        except Exception:
            self.display.delete(0, tk.END)
            self.display.insert(0, "Error")

    def clear(self):
        self.display.delete(0, tk.END)

    def delete_last(self):
        current = self.display.get()
        if current == "Error": 
            self.clear()
        else: 
            self.display.delete(len(current)-1, tk.END)

    def btn_click(self, value):
        current = self.display.get()
        if current == "Error":
            self.clear()
        if value in ['sin', 'cos', 'tan', 'log', 'ln', 'sqrt']:
            self.display.insert(tk.END, value + "(")
        else:
            self.display.insert(tk.END, value)

    def key_handler(self, event):
        
        if event.char == '*':
            self.display.insert(tk.INSERT, '×')
            return "break"
        elif event.char == '/':
            self.display.insert(tk.INSERT, '÷')
            return "break"

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()


