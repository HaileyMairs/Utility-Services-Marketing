#11/12/25 12:31pm
#Auto creates GUI 
import os
import importlib.util
import inspect
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
# ---------------- Colors ----------------
BG_BLACK = "#000000"
CREAM = "#FFF8E1"
DARK_GREEN = "#0b5d3b"
PANEL_BG = "#0f0f0f"

@dataclass
class DatabaseConfig:
    server: str = "localhost,1433"
    database: str = "MCRWS-Telog"
    username: str = "sa"
    password: str = ""
    driver: str = "ODBC Driver 18 for SQL Server"
    encrypt: str = "no"
    trust_cert: str = "yes"
    timeout: int = 5


class DatabaseClient:
    """Shared database connector used by all modules."""
    def __init__(self):
        self.config = DatabaseConfig()
        self.conn = None

    def configure(self, config: DatabaseConfig):
        self.config = config
        self.connect()

    def connect(self):
        if not self.config:
            raise ValueError("Database config not set")
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        cfg = self.config
        conn_str = (
            f"DRIVER={{{cfg.driver}}};"
            f"SERVER={cfg.server};"
            f"DATABASE={cfg.database};"
            f"UID={cfg.username};PWD={cfg.password};"
            f"Encrypt={cfg.encrypt};TrustServerCertificate={cfg.trust_cert};"
        )
        self.conn = pyodbc.connect(conn_str, autocommit=True, timeout=cfg.timeout)
        return self.conn

    def query(self, sql, params=None):
        if not self.conn:
            self.connect()
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchall()


class DatabaseDialog(tk.Toplevel):
    """Modal dialog to capture DB settings."""
    def __init__(self, master, config: DatabaseConfig):
        super().__init__(master)
        self.title("Database Configuration")
        self.resizable(False, False)
        self.config = config
        self.result = None

        self.server_var = tk.StringVar(value=config.server)
        self.db_var = tk.StringVar(value=config.database)
        self.user_var = tk.StringVar(value=config.username)
        self.pwd_var = tk.StringVar(value=config.password)
        self.driver_var = tk.StringVar(value=config.driver)
        self.encrypt_var = tk.BooleanVar(value=config.encrypt.lower() == "yes")
        self.tsc_var = tk.BooleanVar(value=config.trust_cert.lower() == "yes")

        self._build()
        self.grab_set()
        self.transient(master)
        self.wait_visibility()
        self.focus()

    def _build(self):
        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0)

        row = 0
        ttk.Label(frm, text="Server (host,port)").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.server_var, width=28).grid(row=row, column=1, sticky="we")
        row += 1

        ttk.Label(frm, text="Database").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.db_var).grid(row=row, column=1, sticky="we")
        row += 1

        ttk.Label(frm, text="Username").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.user_var).grid(row=row, column=1, sticky="we")
        row += 1

        ttk.Label(frm, text="Password").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.pwd_var, show="*").grid(row=row, column=1, sticky="we")
        row += 1

        ttk.Label(frm, text="ODBC Driver").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.driver_var).grid(row=row, column=1, sticky="we")
        row += 1

        ttk.Checkbutton(frm, text="Encrypt", variable=self.encrypt_var).grid(row=row, column=0, sticky="w")
        ttk.Checkbutton(frm, text="Trust Server Certificate", variable=self.tsc_var).grid(row=row, column=1, sticky="w")
        row += 1

        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=2, pady=(8, 0), sticky="e")
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btns, text="Save & Connect", command=self._on_save).pack(side="right")

    def _on_save(self):
        cfg = DatabaseConfig(
            server=self.server_var.get().strip(),
            database=self.db_var.get().strip(),
            username=self.user_var.get().strip(),
            password=self.pwd_var.get(),
            driver=self.driver_var.get().strip() or "ODBC Driver 18 for SQL Server",
            encrypt="yes" if self.encrypt_var.get() else "no",
            trust_cert="yes" if self.tsc_var.get() else "no",
        )
        self.result = cfg
        self.destroy()


class DynamicUtilityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dynamic Utility App")
        self._maximize_window()
        self.configure(bg=BG_BLACK)
        self.db_client = DatabaseClient()
        self.module_cache = {}

        self._setup_styles()
        self._create_menubar()
        self._create_sidebar()
        self._create_main_panel()
        self._prompt_for_db_and_build()

    # ---------------- Styles ----------------
    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview",
                    background=BG_BLACK,
                    foreground=CREAM,
                    fieldbackground=BG_BLACK,
                    rowheight=28,
                    font=("Segoe UI", 10))
        s.configure("Treeview.Heading",
                    background=DARK_GREEN,
                    foreground=CREAM,
                    font=("Segoe UI", 10, "bold"))
        s.map("Treeview",
              background=[('selected', '#1a7b50')],
              foreground=[('selected', 'white')])

    # ---------------- Sidebar ----------------
    def _create_sidebar(self):
        self.sidebar = tk.Frame(self, bg=PANEL_BG, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="Menu", font=("Segoe UI", 14, "bold"),
                 bg=PANEL_BG, fg=CREAM).pack(pady=(16, 8))
        tk.Button(
            self.sidebar,
            text="Configure Database",
            bg=DARK_GREEN,
            fg=CREAM,
            relief="flat",
            command=self._prompt_for_db_and_build,
        ).pack(fill="x", padx=12, pady=(0, 12))

    # ---------------- Main Panel ----------------
    def _create_main_panel(self):
        self.main_frame = tk.Frame(self, bg=BG_BLACK)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self.title_label = tk.Label(
            self.main_frame, text="", font=("Segoe UI", 18, "bold"),
            bg=BG_BLACK, fg=CREAM, anchor="w"
        )
        self.title_label.pack(fill="x", pady=(0, 5))

        table_frame = tk.Frame(self.main_frame, bg=BG_BLACK)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=(), show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _maximize_window(self):
        """Try platform-friendly maximize; fall back to explicit geometry."""
        for method in (
            lambda: self.state("zoomed"),
            lambda: self.attributes("-zoomed", True),
        ):
            try:
                method()
                return
            except tk.TclError:
                continue
        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()
        self.geometry(f"{width}x{height}")

    def _create_menubar(self):
        menubar = tk.Menu(self)
        db_menu = tk.Menu(menubar, tearoff=0)
        db_menu.add_command(label="Configure…", command=self._prompt_for_db_and_build)
        menubar.add_cascade(label="Database", menu=db_menu)
        self.config(menu=menubar)

    def _prompt_for_db_and_build(self):
        dialog = DatabaseDialog(self, self.db_client.config)
        self.wait_window(dialog)
        if dialog.result is None:
            if not self.db_client.conn:
                messagebox.showerror("Database required", "Please configure the database to continue.")
                return
        else:
            try:
                self.db_client.configure(dialog.result)
            except Exception as exc:
                messagebox.showerror("Connection failed", str(exc))
                return

        # Clear old sidebar entries except header and config button
        for child in list(self.sidebar.winfo_children())[2:]:
            child.destroy()
        self.module_cache.clear()
        self.build_dynamic_sidebar()

    # ---------------- Scan Functions Folder ----------------
    def scan_py_files(self, folder):
        data = {}
        if not os.path.exists(folder):
            print(f"[DEBUG] Folder does not exist: {folder}")
            return data
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    title = None
                    btns = []
                    with open(full_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("#title:"):
                                title = line.split(":", 1)[1].strip().strip("'\"")
                            elif line.startswith("#btn:"):
                                btn_name = line.split(":", 1)[1].strip().strip("'\"")
                                btns.append((btn_name, full_path))
                    if title and btns:
                        if title in data:
                            data[title].extend(btns)
                        else:
                            data[title] = btns
        return data

    # ---------------- Load Module ----------------
    def load_module_class(self, file_path):
        spec = importlib.util.spec_from_file_location(os.path.basename(file_path), file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Find the first class in the module
        cls = None
        for name in dir(mod):
            obj = getattr(mod, name)
            if inspect.isclass(obj) and obj.__module__ == mod.__name__:
                cls = obj
                break

        if cls is None:
            raise Exception(f"No class found in {file_path}")

        # Instantiate class
        try:
            instance = cls(self.db_client)
        except TypeError:
            instance = cls()
        except Exception as exc:
            raise Exception(f"Failed to instantiate {cls.__name__}: {exc}") from exc

        # Inject shared db if supported
        if not isinstance(instance, type) and hasattr(instance, "__dict__"):
            if getattr(instance, "db", None) is None:
                instance.db = self.db_client

        return instance

    # ---------------- Call Function ----------------
    def call_module_function(self, module_instance, btn_name):
        func_name = "get_" + btn_name.lower().replace(" ", "_")
        if hasattr(module_instance, func_name):
            try:
                columns, rows = getattr(module_instance, func_name)()
            except Exception as exc:
                self.title_label.config(text=f"{btn_name} (error)")
                self.populate_tree(["Error"], [(str(exc),)])
                return
            self.populate_tree(columns, rows)
            self.title_label.config(text=btn_name)
        else:
            self.title_label.config(text=f"{btn_name} (function not found)")
            self.populate_tree(["Message"], [("⚠️ Function not implemented.",)])

    # ---------------- Populate Treeview ----------------
    def populate_tree(self, cols, rows):
        tree = self.tree
        tree.delete(*tree.get_children())
        tree["columns"] = cols
        tree["show"] = "headings"

        for c in cols:
            tree.heading(c, text=c, anchor="center")
            tree.column(c, width=150, anchor="center")

        if not rows:
            tree["columns"] = ("Message",)
            tree.heading("Message", text="")
            tree.column("Message", anchor="center", width=800)
            tree.insert("", "end", values=("⚠️ No data found.",))
            return

        for i, r in enumerate(rows):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            tree.insert("", "end", values=r, tags=(tag,))

        tree.tag_configure("evenrow", background="#000000", foreground=CREAM)
        tree.tag_configure("oddrow", background="#0f3021", foreground=CREAM)

    # ---------------- Build Dynamic Sidebar ----------------
    def build_dynamic_sidebar(self):
        folder = os.path.join(os.path.dirname(__file__), "Functions")
        data = self.scan_py_files(folder)

        for title, btn_list in data.items():
            # Container for button + dropdown
            container = tk.Frame(self.sidebar, bg=PANEL_BG)
            container.pack(fill="x")

            # Main button
            main_btn = tk.Button(
                container,
                text=f"{title} ▸",
                bg=DARK_GREEN,
                fg=CREAM,
                relief="flat",
                anchor="w"
            )
            main_btn.pack(fill="x", padx=12, pady=6)

            # Frame for dropdown
            frame = tk.Frame(container, bg=PANEL_BG)
            frame.pack(fill="x", padx=12, pady=0)
            frame.pack_forget()  # initially hidden

            # Toggle function
            def toggle(f=frame, b=main_btn, t=title):
                if f.winfo_ismapped():
                    f.pack_forget()
                    b.config(text=f"{t} ▸")
                else:
                    f.pack(fill="x", padx=12)
                    b.config(text=f"{t} ▾")
            main_btn.config(command=toggle)

            # Add buttons to dropdown
            for btn_name, module_file in btn_list:
                if module_file not in self.module_cache:
                    self.module_cache[module_file] = self.load_module_class(module_file)
                mod_instance = self.module_cache[module_file]
                tk.Button(
                    frame,
                    text=btn_name,
                    bg=PANEL_BG,
                    fg=CREAM,
                    relief="flat",
                    anchor="w",
                    padx=12,
                    command=lambda m=mod_instance, b=btn_name: self.call_module_function(m, b)
                ).pack(fill="x", pady=2)

# ---------------- Run App ----------------
if __name__ == "__main__":
    app = DynamicUtilityApp()
    app.mainloop()
