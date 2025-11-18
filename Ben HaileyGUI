'''Current GUI as of 11/5/25 1331
*** ONLY LOOKING AT THE MCRWS-Telog DATABASE ***
Battery Health tab created and needs to add the database inside. It is only a shell
Gui changed to drop down menu

CURRENT SETUP
Alarms
    Active
        displays all current active alarms across all sites. 
    Repeated
        shows alarms that have triggered multiples times in 7 days
    Orphan
        displays alarms that are not associated with a known site
Device Health
    Currently Empty
System Reliability
    Site Reliability    
        ranks sites by reliability. calculates total downtime, number of outages, expected uptime, and normalized reliability score to prioritize maintenance or upgrades
Tables w/ Info
Tables w/o Info
'''

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyodbc
import threading
from datetime import datetime, timedelta
import json
import os
import pathlib
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple
import keyring
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ---------- CONFIG ----------
SQL_SERVER = "SUPERCOOLGAMING"
DATABASE = "MCRWS-Telog"
REFRESH_MS = 60_000

# Telog database name used for fully-qualified queries (change here if needed)
TELOG_DB = DATABASE

BG_BLACK = "#000000"
CREAM = "#FFF8E1"
DARK_GREEN = "#0b5d3b"
PANEL_BG = "#0f0f0f"
TEXT_COLOR = CREAM

# --- Connection Manager Config ---
APP_DIR = pathlib.Path.home() / ".hailey_gui"
APP_DIR.mkdir(exist_ok=True)
CONFIG_PATH = APP_DIR / "db_profiles.json"
KEYRING_SERVICE = "HaileyGUI"
# ----------------------------

# === UNIVERSAL DB CONNECTION MANAGER (SQL Server, Postgres, MySQL, SQLite) ===
@dataclass
class ConnectionProfile:
    name: str
    db_type: str  # "mssql" | "postgres" | "mysql" | "sqlite"
    host: str = ""
    port: Optional[int] = None
    database: str = ""
    username: str = ""
    odbc_driver: str = "ODBC Driver 18 for SQL Server"  # MSSQL only
    use_integrated: bool = False                        # MSSQL only
    encrypt: bool = True                                # MSSQL only
    trust_server_cert: bool = True                      # MSSQL only
    sqlite_path: str = ""                               # SQLite only
    query_timeout: int = 30
    active: bool = False

    def keyring_username(self) -> str:
        return f"{self.name}::{self.username or 'INTEGRATED'}"

class ConnectionManager:
    def __init__(self):
        # Initialize profile storage and load existing profiles
        self._profiles: Dict[str, ConnectionProfile] = {}
        self.engine = None
        self._load()

        # --- Universal Connection Manager bootstrap ---
        # If there is an active profile, attempt to build and test an engine
        active = self.get_active()
        if active:
            try:
                eng = SqlEngineFactory.build_engine(active, self)
                ok, msg = SqlEngineFactory.test_connection(eng)
                if ok:
                    # Store engine for callers; do not try to wrap it with DatabaseManager
                    self.engine = eng
                else:
                    try:
                        pass
                    except Exception:
                        pass
            except Exception as e:
                try:
                    pass
                except Exception:
                    pass
        # --- End Connection Manager bootstrap ---

    def _load(self):
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for name, rec in data.get("profiles", {}).items():
                self._profiles[name] = ConnectionProfile(**rec)
        else:
            CONFIG_PATH.write_text(json.dumps({"profiles": {}}, indent=2))

    def _save(self):
        data = {"profiles": {n: asdict(p) for n, p in self._profiles.items()}}
        for p in data["profiles"].values():
            if p["db_type"] != "mssql":
                for k in ("odbc_driver","use_integrated","encrypt","trust_server_cert"):
                    p.pop(k, None)
            if p["db_type"] != "sqlite":
                p.pop("sqlite_path", None)
        CONFIG_PATH.write_text(json.dumps(data, indent=2))

    def list_profiles(self) -> Dict[str, ConnectionProfile]:
        return dict(self._profiles)

    def get_active(self) -> Optional[ConnectionProfile]:
        for p in self._profiles.values():
            if p.active:
                return p
        return None

    def set_active(self, name: str):
        for n in self._profiles:
            self._profiles[n].active = (n == name)
        self._save()

    def save_password(self, profile: ConnectionProfile, password: str):
        keyring.set_password(KEYRING_SERVICE, profile.keyring_username(), password)

    def load_password(self, profile: ConnectionProfile) -> Optional[str]:
        return keyring.get_password(KEYRING_SERVICE, profile.keyring_username())

    def upsert_profile(self, profile: ConnectionProfile, save_password: Optional[str] = None):
        if profile.active:
            for p in self._profiles.values():
                p.active = False
        self._profiles[profile.name] = profile
        self._save()
        if save_password is not None and not profile.use_integrated and profile.db_type != "sqlite":
            self.save_password(profile, save_password)

    def delete_profile(self, name: str):
        prof = self._profiles.pop(name, None)
        if prof:
            try:
                keyring.delete_password(KEYRING_SERVICE, prof.keyring_username())
            except Exception:
                pass
            self._save()

class SqlEngineFactory:
    @staticmethod
    def make_url_and_kwargs(p: ConnectionProfile, password: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        if p.db_type == "mssql":
            driver = p.odbc_driver.replace(" ", "+")
            auth_part = ""
            if not p.use_integrated:
                auth_part = f"{p.username}:{password or ''}@"
            host = p.host or "localhost"
            port = f":{p.port}" if p.port else ""
            db = p.database or "master"
            encrypt = "yes" if p.encrypt else "no"
            tsc = "yes" if p.trust_server_cert else "no"
            query = f"driver={driver};Encrypt={encrypt};TrustServerCertificate={tsc}"
            if p.use_integrated:
                query += ";Trusted_Connection=Yes"
            url = f"mssql+pyodbc://{auth_part}{host}{port}/{db}?{query}"
            kwargs = {"pool_pre_ping": True}
            return url, kwargs

        elif p.db_type == "postgres":
            host = p.host or "localhost"
            port = p.port or 5432
            db = p.database or "postgres"
            user = p.username or "postgres"
            url = f"postgresql+psycopg2://{user}:{password or ''}@{host}:{port}/{db}"
            return url, {"pool_pre_ping": True}

        elif p.db_type == "mysql":
            host = p.host or "localhost"
            port = p.port or 3306
            db = p.database or "mysql"
            user = p.username or "root"
            url = f"mysql+pymysql://{user}:{password or ''}@{host}:{port}/{db}"
            return url, {"pool_pre_ping": True}

        elif p.db_type == "sqlite":
            path = p.sqlite_path or ":memory:"
            if path != ":memory:":
                path = os.path.abspath(path)
            url = f"sqlite:///{path}"
            return url, {"pool_pre_ping": True}

        else:
            raise ValueError(f"Unsupported db_type: {p.db_type}")

    @staticmethod
    def build_engine(profile: ConnectionProfile, cm: ConnectionManager) -> Engine:
        pwd = None if profile.db_type in ("sqlite",) or profile.use_integrated else cm.load_password(profile)
        url, kwargs = SqlEngineFactory.make_url_and_kwargs(profile, pwd)
        eng = create_engine(url, **kwargs)
        if profile.query_timeout and profile.db_type in ("postgres","mysql"):
            with eng.connect() as c:
                if profile.db_type == "postgres":
                    c.execute(text(f"SET statement_timeout TO {profile.query_timeout * 1000}"))
                elif profile.db_type == "mysql":
                    c.execute(text(f"SET SESSION MAX_EXECUTION_TIME={profile.query_timeout * 1000}"))
        return eng

    @staticmethod
    def test_connection(engine: Engine) -> Tuple[bool, str]:
        try:
            with engine.connect() as c:
                c.execute(text("SELECT 1"))
            return True, "Connection OK"
        except Exception as e:
            return False, str(e)

class ConnectionDialog(tk.Toplevel):
    def __init__(self, master, conn_mgr: ConnectionManager, on_apply):
        super().__init__(master)
        self.title("Database Connection")
        self.resizable(False, False)
        self.conn_mgr = conn_mgr
        self.on_apply = on_apply

        self.profile_var = tk.StringVar()
        self.dbtype_var = tk.StringVar(value="mssql")
        self.name_var = tk.StringVar(value="Default")
        self.host_var = tk.StringVar(value="localhost")
        self.port_var = tk.StringVar()
        self.db_var = tk.StringVar()
        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.odbc_var = tk.StringVar(value="ODBC Driver 18 for SQL Server")
        self.integrated_var = tk.BooleanVar(value=False)
        self.encrypt_var = tk.BooleanVar(value=True)
        self.tsc_var = tk.BooleanVar(value=True)
        self.sqlite_path_var = tk.StringVar()
        self.timeout_var = tk.IntVar(value=30)
        self.active_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._refresh_profile_list()

        self.transient(master)
        self.grab_set()
        self.wait_visibility()
        self.focus()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0)

        ttk.Label(frm, text="Profile:").grid(row=0, column=0, sticky="w")
        self.profile_combo = ttk.Combobox(frm, textvariable=self.profile_var, width=28, state="readonly")
        self.profile_combo.grid(row=0, column=1, sticky="we", columnspan=2)
        ttk.Button(frm, text="Load", command=self._load_selected).grid(row=0, column=3, padx=(6,0))
        ttk.Button(frm, text="Delete", command=self._delete_selected).grid(row=0, column=4, padx=(6,0))

        row = 1
        ttk.Label(frm, text="Profile Name").grid(row=row, column=0, sticky="w"); 
        ttk.Entry(frm, textvariable=self.name_var, width=30).grid(row=row, column=1, sticky="we", columnspan=3)
        row += 1

        ttk.Label(frm, text="Database Type").grid(row=row, column=0, sticky="w")
        dbtype = ttk.Combobox(frm, textvariable=self.dbtype_var, values=["mssql","postgres","mysql","sqlite"], width=12, state="readonly")
        dbtype.grid(row=row, column=1, sticky="w")
        dbtype.bind("<<ComboboxSelected>>", lambda e: self._toggle_fields())
        row += 1

        ttk.Label(frm, text="Host").grid(row=row, column=0, sticky="w"); ttk.Entry(frm, textvariable=self.host_var).grid(row=row, column=1, sticky="we")
        ttk.Label(frm, text="Port").grid(row=row, column=2, sticky="w"); ttk.Entry(frm, textvariable=self.port_var, width=8).grid(row=row, column=3, sticky="w")
        row += 1
        ttk.Label(frm, text="Database").grid(row=row, column=0, sticky="w"); ttk.Entry(frm, textvariable=self.db_var).grid(row=row, column=1, sticky="we")
        ttk.Label(frm, text="Username").grid(row=row, column=2, sticky="w"); ttk.Entry(frm, textvariable=self.user_var).grid(row=row, column=3, sticky="we")
        row += 1
        ttk.Label(frm, text="Password").grid(row=row, column=0, sticky="w"); ttk.Entry(frm, textvariable=self.pass_var, show="*").grid(row=row, column=1, sticky="we")
        ttk.Label(frm, text="Query Timeout (s)").grid(row=row, column=2, sticky="w"); ttk.Entry(frm, textvariable=self.timeout_var, width=8).grid(row=row, column=3, sticky="w")
        row += 1

        self.mssql_box = ttk.LabelFrame(frm, text="SQL Server (ODBC)")
        self.mssql_box.grid(row=row, column=0, columnspan=5, sticky="we", pady=(6,0))
        ttk.Label(self.mssql_box, text="ODBC Driver").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.mssql_box, textvariable=self.odbc_var, width=28).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(self.mssql_box, text="Integrated Security (Windows auth)", variable=self.integrated_var, command=self._toggle_fields).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(self.mssql_box, text="Encrypt", variable=self.encrypt_var).grid(row=2, column=0, sticky="w")
        ttk.Checkbutton(self.mssql_box, text="Trust Server Certificate", variable=self.tsc_var).grid(row=2, column=1, sticky="w")

        row += 1
        self.sqlite_box = ttk.LabelFrame(frm, text="SQLite")
        self.sqlite_box.grid(row=row, column=0, columnspan=5, sticky="we", pady=(6,0))
        ttk.Entry(self.sqlite_box, textvariable=self.sqlite_path_var, width=40).grid(row=0, column=0, sticky="we")
        ttk.Button(self.sqlite_box, text="Browse…", command=self._pick_sqlite_file).grid(row=0, column=1, padx=6)

        row += 1
        ttk.Checkbutton(frm, text="Set as Active Profile", variable=self.active_var).grid(row=row, column=0, sticky="w")
        ttk.Button(frm, text="Test Connection", command=self._on_test).grid(row=row, column=2, sticky="e")
        ttk.Button(frm, text="Save", command=self._on_save).grid(row=row, column=3, sticky="e")
        ttk.Button(frm, text="Save & Use", command=self._on_save_and_use).grid(row=row, column=4, sticky="e")

        self._toggle_fields()

    def _refresh_profile_list(self):
        names = sorted(self.conn_mgr.list_profiles().keys())
        self.profile_combo["values"] = names
        act = self.conn_mgr.get_active()
        if act:
            self.profile_var.set(act.name)

    def _serialize_from_form(self):
        try:
            port = int(self.port_var.get()) if self.port_var.get() else None
        except ValueError:
            port = None
        p = ConnectionProfile(
            name=self.name_var.get().strip() or "Default",
            db_type=self.dbtype_var.get(),
            host=self.host_var.get().strip(),
            port=port,
            database=self.db_var.get().strip(),
            username=self.user_var.get().strip(),
            odbc_driver=self.odbc_var.get().strip(),
            use_integrated=bool(self.integrated_var.get()),
            encrypt=bool(self.encrypt_var.get()),
            trust_server_cert=bool(self.tsc_var.get()),
            sqlite_path=self.sqlite_path_var.get().strip(),
            query_timeout=int(self.timeout_var.get() or 30),
            active=bool(self.active_var.get())
        )
        pwd = self.pass_var.get()
        if p.db_type in ("sqlite",) or p.use_integrated:
            pwd = None
        return p, pwd

    def _apply_profile_to_form(self, p: ConnectionProfile):
        self.name_var.set(p.name)
        self.dbtype_var.set(p.db_type)
        self.host_var.set(p.host)
        self.port_var.set("" if p.port is None else str(p.port))
        self.db_var.set(p.database)
        self.user_var.set(p.username)
        self.pass_var.set("")
        self.odbc_var.set(p.odbc_driver or "ODBC Driver 18 for SQL Server")
        self.integrated_var.set(p.use_integrated)
        self.encrypt_var.set(p.encrypt)
        self.tsc_var.set(p.trust_server_cert)
        self.sqlite_path_var.set(p.sqlite_path)
        self.timeout_var.set(p.query_timeout or 30)
        self.active_var.set(p.active)
        self._toggle_fields()

    def _toggle_fields(self):
        dt = self.dbtype_var.get()
        is_mssql = dt == "mssql"
        is_sqlite = dt == "sqlite"
        self.mssql_box.grid() if is_mssql else self.mssql_box.grid_remove()
        self.sqlite_box.grid() if is_sqlite else self.sqlite_box.grid_remove()
        state_up = "disabled" if (is_sqlite or (is_mssql and self.integrated_var.get())) else "normal"
        for w in self._widgets_for_userpass(self):
            try: w.configure(state=state_up)
            except Exception: pass
        state_hp = "disabled" if is_sqlite else "normal"
        for w in self._widgets_for_hostportdb(self):
            try: w.configure(state=state_hp)
            except Exception: pass

    def _widgets_for_userpass(self, root):
        return [self._find_entry_by_var(self.user_var), self._find_entry_by_var(self.pass_var)]

    def _widgets_for_hostportdb(self, root=None):
        return [self._find_entry_by_var(self.host_var),
                self._find_entry_by_var(self.port_var),
                self._find_entry_by_var(self.db_var)]

    def _find_entry_by_var(self, var):
        for child in self.winfo_children():
            entry = self._search_entry(child, var)
            if entry: return entry
        return ttk.Entry(self)

    def _search_entry(self, widget, var):
        if isinstance(widget, ttk.Entry) and getattr(widget, "cget", None):
            try:
                if widget.cget("textvariable") == str(var):
                    return widget
            except tk.TclError:
                pass
        for ch in widget.winfo_children():
            found = self._search_entry(ch, var)
            if found: return found
        return None

    def _pick_sqlite_file(self):
        p = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB","*.db *.sqlite *.sqlite3"), ("All files","*.*")])
        if p:
            self.sqlite_path_var.set(p)

    def _load_selected(self):
        name = self.profile_var.get()
        profs = self.conn_mgr.list_profiles()
        if name in profs:
            self._apply_profile_to_form(profs[name])

    def _delete_selected(self):
        name = self.profile_var.get()
        if not name: return
        if messagebox.askyesno("Delete Profile", f"Delete profile '{name}'?"):
            self.conn_mgr.delete_profile(name)
            self._refresh_profile_list()

    def _on_test(self):
        profile, pwd = self._serialize_from_form()
        try:
            tmp_mgr = self.conn_mgr
            if pwd is not None:
                tmp_mgr.save_password(profile, pwd)
            eng = SqlEngineFactory.build_engine(profile, tmp_mgr)
            ok, msg = SqlEngineFactory.test_connection(eng)
            messagebox.showinfo("Connection Test", msg if ok else f"Failed: {msg}")
        except Exception as e:
            messagebox.showerror("Connection Test", f"Failed: {e}")

    def _on_save(self):
        self._save_profile(active_only=False)

    def _on_save_and_use(self):
        self._save_profile(active_only=True)

    def _save_profile(self, active_only: bool):
        profile, pwd = self._serialize_from_form()
        self.conn_mgr.upsert_profile(profile, save_password=pwd)
        if active_only:
            self.conn_mgr.set_active(profile.name)
            try:
                eng = SqlEngineFactory.build_engine(profile, self.conn_mgr)
                ok, msg = SqlEngineFactory.test_connection(eng)
                if ok:
                    self.on_apply(profile, eng)
                else:
                    messagebox.showwarning("Connection", f"Profile saved but connection failed: {msg}")
            except Exception as e:
                messagebox.showerror("Connection", f"Profile saved but engine failed: {e}")
        self._refresh_profile_list()
        messagebox.showinfo("Saved", f"Profile '{profile.name}' saved.")
# === END UNIVERSAL DB CONNECTION MANAGER =====================================

# ---------- DATABASE ----------
class DatabaseManager:
    def __init__(self, server=SQL_SERVER, database=DATABASE, engine: Engine = None):
        """
        DatabaseManager can operate in two modes:
        - pyodbc mode: connect() will create a pyodbc.Connection using server/database
        - SQLAlchemy engine mode: if `engine` is provided, queries will run via SQLAlchemy.

        Inputs:
        - server, database: used when no engine provided (pyodbc)
        - engine: SQLAlchemy Engine instance (optional)

        Behavior:
        - If engine is provided, DatabaseManager.query() will execute SQL via the engine.
        - If engine is not provided, connect() will attempt pyodbc connections as before.
        """
        self.server = server
        self.database = database
        self.conn = None
        self.engine = engine

    def connect(self):
        # If an engine is provided, we don't create a pyodbc connection here.
        if self.engine is not None:
            return self.engine

        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;"
        try:
            self.conn = pyodbc.connect(conn_str, autocommit=True, timeout=5)
        except pyodbc.Error:
            conn_str = conn_str.replace("ODBC Driver 17", "ODBC Driver 18")
            self.conn = pyodbc.connect(conn_str, autocommit=True, timeout=5)
        return self.conn

    def query(self, sql, params=None):
        # If running against a SQLAlchemy engine, execute via engine
        if self.engine is not None:
            # SQLAlchemy expects positional parameters as a dict or sequence depending on dialect.
            try:
                # Support legacy code that passes positional parameters using '?' placeholders.
                bind_params = {}
                exec_sql = sql
                if params and isinstance(params, (list, tuple)):
                    # Replace each '?' with a named parameter :p0, :p1, ...
                    parts = exec_sql.split('?')
                    if len(parts) - 1 == len(params):
                        new_sql = parts[0]
                        for idx, part in enumerate(parts[1:]):
                            pname = f":p{idx}"
                            new_sql += pname + part
                            bind_params[f"p{idx}"] = params[idx]
                        exec_sql = new_sql
                    else:
                        # Fallback: no replacement, rely on SQLAlchemy to handle params if possible
                        exec_sql = sql
                        bind_params = {}
                elif params and isinstance(params, dict):
                    bind_params = params

                with self.engine.connect() as conn:
                    result = conn.execute(text(exec_sql), bind_params)
                    rows = result.fetchall()
                    return [tuple(r) for r in rows]
            except Exception:
                raise

        if not self.conn:
            raise Exception("Database not connected.")
        cur = self.conn.cursor()
        # For pyodbc connections, ensure the connection is using the configured database.
        # Some drivers or execution contexts don't allow "USE db;" as part of a multi-statement
        # so we execute it separately here (best-effort). If it fails, we continue and let
        # the next statement run (fully-qualified queries will still work).
        try:
            cur.execute(sql, params or [])
            return cur.fetchall()
        finally:
            pass

# ---------- UTILITIES ----------
class AlarmUtility:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_active(self):
        sql = f"""
        SELECT alarm_history_id, alarm_source_id, alarm_name, site_id, 
               alarm_activation_time, alarm_deactivation_time, alarm_active, alarm_title
        FROM [{TELOG_DB}].dbo.alarm_history
        WHERE alarm_active = 1
        ORDER BY alarm_activation_time DESC;
        """
        return self.db.query(sql)

    def get_repeated(self):
        one_week_ago = datetime.now() - timedelta(days=7)
        sql = f"""
        SELECT alarm_name, site_id, COUNT(*) AS occ_count, 
               MAX(alarm_activation_time) AS last_activated, MAX(alarm_title)
        FROM [{TELOG_DB}].dbo.alarm_history
        WHERE alarm_activation_time >= ?
        GROUP BY alarm_name, site_id
        HAVING COUNT(*) >= 2
        ORDER BY occ_count DESC;
        """
        rows = self.db.query(sql, [one_week_ago])
        # If nothing found in 7 days, try 30 days, then try without time filter to assist
        # environments where timestamps are stored in different zones or units.
        if not rows:
            one_month_ago = datetime.now() - timedelta(days=30)
            rows = self.db.query(sql, [one_month_ago])
        if not rows:
            sql_all = f"""
            SELECT alarm_name, site_id, COUNT(*) AS occ_count, 
                   MAX(alarm_activation_time) AS last_activated, MAX(alarm_title)
            FROM [{TELOG_DB}].dbo.alarm_history
            GROUP BY alarm_name, site_id
            HAVING COUNT(*) >= 2
            ORDER BY occ_count DESC;
            """
            rows = self.db.query(sql_all)
        return rows

    def get_orphan(self):
        # Strategy 1: string-cast join (works when site_id formats match as strings)
        try:
            sql_str = f"""
            SELECT ah.alarm_history_id, ah.alarm_source_id, ah.alarm_name, ah.site_id, 
                   ah.alarm_activation_time, ah.alarm_deactivation_time, 
                   ah.alarm_system_time, ah.alarm_title
            FROM [{TELOG_DB}].dbo.alarm_history AS ah
            LEFT JOIN [{TELOG_DB}].dbo.sites AS s ON LTRIM(RTRIM(CAST(ISNULL(ah.site_id, '') AS VARCHAR(200)))) = LTRIM(RTRIM(CAST(ISNULL(s.site_id, '') AS VARCHAR(200))))
            WHERE s.site_id IS NULL
            ORDER BY ah.alarm_activation_time DESC;
            """
            rows = self.db.query(sql_str)
        except Exception:
            rows = []

        # Strategy 2: numeric match using TRY_CAST (handles numeric IDs stored as strings)
        if not rows:
            try:
                sql_num = f"""
                SELECT ah.alarm_history_id, ah.alarm_source_id, ah.alarm_name, ah.site_id, 
                       ah.alarm_activation_time, ah.alarm_deactivation_time, 
                       ah.alarm_system_time, ah.alarm_title
                FROM [{TELOG_DB}].dbo.alarm_history AS ah
                LEFT JOIN [{TELOG_DB}].dbo.sites AS s ON TRY_CAST(ah.site_id AS BIGINT) = TRY_CAST(s.site_id AS BIGINT)
                WHERE s.site_id IS NULL
                ORDER BY ah.alarm_activation_time DESC;
                """
                rows = self.db.query(sql_num)
            except Exception:
                rows = []

        # Strategy 3: anti-join NOT EXISTS using trimmed string comparison (robust fallback)
        if not rows:
            try:
                sql_notexists = f"""
                SELECT ah.alarm_history_id, ah.alarm_source_id, ah.alarm_name, ah.site_id, 
                       ah.alarm_activation_time, ah.alarm_deactivation_time, 
                       ah.alarm_system_time, ah.alarm_title
                FROM [{TELOG_DB}].dbo.alarm_history AS ah
                WHERE NOT EXISTS (
                    SELECT 1 FROM [{TELOG_DB}].dbo.sites s
                    WHERE LTRIM(RTRIM(CAST(ISNULL(s.site_id, '') AS VARCHAR(200)))) = LTRIM(RTRIM(CAST(ISNULL(ah.site_id, '') AS VARCHAR(200))))
                )
                ORDER BY ah.alarm_activation_time DESC;
                """
                rows = self.db.query(sql_notexists)
            except Exception:
                rows = []

        # Strategy 4: relaxed check for NULL/blank site_id in alarm_history
        if not rows:
            try:
                sql_blank = f"""
                SELECT ah.alarm_history_id, ah.alarm_source_id, ah.alarm_name, ah.site_id, 
                       ah.alarm_activation_time, ah.alarm_deactivation_time, 
                       ah.alarm_system_time, ah.alarm_title
                FROM [{TELOG_DB}].dbo.alarm_history AS ah
                WHERE ah.site_id IS NULL OR LTRIM(RTRIM(CAST(ah.site_id AS VARCHAR(200)))) = ''
                ORDER BY ah.alarm_activation_time DESC;
                """
                rows = self.db.query(sql_blank)
            except Exception:
                rows = []

        # If still nothing, return a diagnostic summary row to help troubleshooting
        if not rows:
            try:
                diag_sql = f"""
                SELECT
                    (SELECT COUNT(1) FROM [{TELOG_DB}].dbo.alarm_history) AS alarm_history_count,
                    (SELECT COUNT(1) FROM [{TELOG_DB}].dbo.sites) AS sites_count,
                    (SELECT COUNT(1) FROM [{TELOG_DB}].dbo.alarm_history WHERE site_id IS NULL OR LTRIM(RTRIM(CAST(site_id AS VARCHAR(200)))) = '') AS blank_siteid_count,
                    (SELECT COUNT(DISTINCT CAST(ISNULL(site_id,'') AS VARCHAR(200))) FROM [{TELOG_DB}].dbo.alarm_history) AS distinct_alarm_siteids
                """
                diag = self.db.query(diag_sql)
                # Return a human-readable single row explaining counts
                if diag:
                    ar = diag[0]
                    msg = (f"Diagnostics: alarm_history={ar[0]}, sites={ar[1]}, "
                           f"blank_siteid={ar[2]}, distinct_alarm_siteids={ar[3]}")
                else:
                    msg = "No data available for diagnostics."
            except Exception:
                msg = "Unable to run diagnostics (DB error)."
            return [("DIAGNOSTIC", msg, "", "", "", "", "")]

        return rows


class TableUtility:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all_tables(self):
        sql = f"""
        SELECT s.name, t.name, SUM(p.rows)
        FROM [{TELOG_DB}].sys.schemas s
        JOIN [{TELOG_DB}].sys.tables t ON t.schema_id = s.schema_id
        LEFT JOIN [{TELOG_DB}].sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1)
        GROUP BY s.name, t.name
        ORDER BY s.name, t.name;
        """
        return self.db.query(sql)

    def get_with_info(self):
        return [r for r in self.get_all_tables() if (r[2] or 0) > 0]

    def get_without_info(self):
        return [r for r in self.get_all_tables() if (r[2] or 0) == 0]


class DeviceHealthUtility:
    """
    Device health utility - queries device status from MCRWS-Telog database.
    
    Note: This requires the device_health table or appropriate source tables
    to be available in the MCRWS-Telog database.
    
    Returns rows: (device_id, device_name, status, last_checked)
    """

    def __init__(self, db: "DatabaseManager"):
        self.db = db

    def get_device_status(self):
        """
        Attempts to retrieve device health status.
        Returns empty list if tables don't exist (will display "No data found").
        """
        try:
            # First try to query a device_health table if it exists
            sql = f"""
            SELECT 
                device_id, 
                device_name, 
                status, 
                last_checked
            FROM [{TELOG_DB}].dbo.device_health
            ORDER BY last_checked DESC;
            """
            return self.db.query(sql)
        except Exception:
            # If device_health table doesn't exist, try alternative sources
            try:
                # Fall back: return last activity per site using alarm_history timestamps
                sql = f"""
                SELECT TOP 100
                    s.site_id AS device_id,
                    s.site_name AS device_name,
                    'Status Unknown' AS status,
                    MAX(ah.alarm_activation_time) AS last_checked
                FROM [{TELOG_DB}].dbo.sites s
                LEFT JOIN [{TELOG_DB}].dbo.alarm_history ah ON s.site_id = ah.site_id
                GROUP BY s.site_id, s.site_name
                ORDER BY MAX(ah.alarm_activation_time) DESC;
                """
                rows = self.db.query(sql)
                # If the query returned times as NULL for sites with no alarms, coerce to None
                normalized = []
                for r in rows:
                    device_id = r[0]
                    device_name = r[1]
                    status = r[2]
                    last_checked = r[3] if len(r) > 3 else None
                    normalized.append((device_id, device_name, status, last_checked))
                return normalized
            except Exception:
                # If no tables available, return empty (will show "No data found")
                return []
    
class SystemReliabilityUtility:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_site_reliability(self):
        """
        Computes site reliability combining alarm_log, alarm_states, and RecPowerInfoTable.
        Safely handles NULL values and large sums (BIGINT), avoids SQL Server warnings and overflow.
        """
        sql = f"""
        -- Normalize raw sums and detect likely millisecond units by thresholding.
        -- If raw sums exceed 10 years in seconds (approx 315,360,000), assume values may be
        -- reported in milliseconds and divide by 1000. This heuristic prevents absurd
        -- "90 year" values from skewing results.
        WITH RawDurations AS (
            SELECT
                site_id,
                SUM(CAST(ISNULL(alarm_event_duration, 0) AS BIGINT)) AS raw_downtime,
                COUNT(*) AS outage_count
            FROM [{TELOG_DB}].dbo.alarm_log
            GROUP BY site_id
        ),
        AlarmDurations AS (
            SELECT
                site_id,
                CASE
                    WHEN raw_downtime IS NULL THEN 0
                    WHEN raw_downtime > 315360000 THEN CAST(raw_downtime AS FLOAT) / 1000.0
                    ELSE CAST(raw_downtime AS FLOAT)
                END AS downtime_seconds,
                outage_count
            FROM RawDurations
        ),
        PowerInfo AS (
            SELECT
                CAST(RecIdKey AS VARCHAR(50)) AS measurement_id,
                SUM(CAST(ISNULL(RecordingInterval, 0) AS BIGINT)) AS raw_expected
            FROM [{TELOG_DB}].dbo.RecPowerInfoTable
            GROUP BY CAST(RecIdKey AS VARCHAR(50))
        ),
        PowerNormalized AS (
            SELECT
                measurement_id,
                CASE
                    WHEN raw_expected IS NULL THEN 0
                    WHEN raw_expected > 315360000 THEN CAST(raw_expected AS FLOAT) / 1000.0
                    ELSE CAST(raw_expected AS FLOAT)
                END AS expected_uptime_seconds
            FROM PowerInfo
        ),
        SitePower AS (
            SELECT a.site_id,
                   SUM(CAST(ISNULL(p.expected_uptime_seconds, 0) AS BIGINT)) AS expected_uptime_seconds
            FROM AlarmDurations a
            LEFT JOIN [{TELOG_DB}].dbo.alarm_log al ON a.site_id = al.site_id
            LEFT JOIN PowerNormalized p ON CAST(ISNULL(al.measurement_id, '') AS VARCHAR(50)) = p.measurement_id
            GROUP BY a.site_id
        )
        SELECT
            a.site_id,
            a.outage_count,
            CAST(ISNULL(a.downtime_seconds, 0) AS BIGINT) AS downtime_seconds,
            CAST(ISNULL(sp.expected_uptime_seconds, 0) AS BIGINT) AS expected_uptime_seconds,
            CAST(
                (
                    CASE
                        WHEN ISNULL(sp.expected_uptime_seconds, 0) = 0
                            THEN
                                CASE WHEN a.downtime_seconds = 0 THEN 1.0
                                     ELSE
                                        CASE WHEN 1.0 - (a.downtime_seconds * 1.0 / 86400.0) < 0 THEN 0
                                             ELSE 1.0 - (a.downtime_seconds * 1.0 / 86400.0)
                                        END
                                END
                        ELSE
                            CASE WHEN 1.0 - (a.downtime_seconds * 1.0 / sp.expected_uptime_seconds) < 0 THEN 0
                                 ELSE 1.0 - (a.downtime_seconds * 1.0 / sp.expected_uptime_seconds)
                            END
                    END
                )
            AS DECIMAL(6,4)) AS reliability_score
        FROM AlarmDurations a
        LEFT JOIN SitePower sp ON a.site_id = sp.site_id
        ORDER BY reliability_score ASC, outage_count DESC
        """
        return self.db.query(sql)

    def format_for_treeview(self, rows):
        """
        Convert raw SQL output into formatted lists for Treeview.
        Adds comma separators for large numbers and two decimals for reliability.
        """
        formatted = []
        for r in rows:
            site_id, outages, downtime, expected, reliability = r
            # Ensure numeric types and safe formatting
            try:
                downtime_n = int(downtime or 0)
            except Exception:
                downtime_n = 0
            try:
                expected_n = int(expected or 0)
            except Exception:
                expected_n = 0
            try:
                reli_n = float(reliability or 0)
            except Exception:
                reli_n = 0.0

            # Display reliability as percentage with two decimals
            reli_pct = f"{reli_n * 100:.2f}%"

            formatted.append([
                str(site_id),
                str(outages),
                f"{downtime_n:,}",
                f"{expected_n:,}",
                reli_pct
            ])
        return formatted



# ---------- GUI ----------
class UtilityGUI(tk.Tk):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.title("Utility App")
        self.state('zoomed')
        self.configure(bg=BG_BLACK)
        self._setup_styles()
        self._create_sidebar()
        self._create_main_panel()
        self.alarm_submenu_visible = False
        self.reliability_submenu_visible = False

    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use('clam')

        s.configure("TFrame", background=BG_BLACK)
        s.configure("Left.TFrame", background=PANEL_BG)
        s.configure("Main.TFrame", background=BG_BLACK)
        s.configure("TLabel", background=BG_BLACK, foreground=TEXT_COLOR)
        s.configure("Accent.TButton", background=DARK_GREEN, foreground=CREAM)
        s.map("Accent.TButton", background=[('active', DARK_GREEN)], foreground=[('active', CREAM)])

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
        s.map("Treeview.Heading",
              background=[('active', '#1a7b50')],
              foreground=[('active', CREAM)])

        s.map("Treeview",
              background=[('selected', '#1a7b50')],
              foreground=[('selected', 'white')])

    def _create_sidebar(self):
        self.sidebar = ttk.Frame(self, style="Left.TFrame", width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="Menu", font=("Segoe UI", 14, "bold"),
                 bg=PANEL_BG, fg=CREAM).pack(pady=(16, 8))

        # --- Alarms main button ---
        self.alarm_button = ttk.Button(
            self.sidebar, text="Alarms ▸", style="Accent.TButton",
            command=self._toggle_alarm_menu
        )
        self.alarm_button.pack(fill="x", padx=12, pady=(6, 0))

        # Alarm dropdown container
        self.alarm_container = tk.Frame(self.sidebar, bg=PANEL_BG)
        self.alarm_container.pack(fill="x", padx=0, pady=0)
        self.alarm_frame = tk.Frame(self.alarm_container, bg=PANEL_BG)
        self.alarm_frame.pack_forget()

        # Alarm submenu buttons
        tk.Button(self.alarm_frame, text="Active", bg=PANEL_BG, fg=CREAM,
                  relief="flat", anchor="w",
                  command=lambda: self.app.show_active_alarms()).pack(fill="x", pady=2)
        tk.Button(self.alarm_frame, text="Repeated", bg=PANEL_BG, fg=CREAM,
                  relief="flat", anchor="w",
                  command=lambda: self.app.show_repeated_alarms()).pack(fill="x", pady=2)
        tk.Button(self.alarm_frame, text="Orphan", bg=PANEL_BG, fg=CREAM,
                  relief="flat", anchor="w",
                  command=lambda: self.app.show_orphan_alarms()).pack(fill="x", pady=2)

        # --- Device Health button ---
        ttk.Button(self.sidebar, text="Device Health", style="Accent.TButton",
                   command=lambda: self.app.show_device_health()).pack(fill="x", padx=12, pady=6)


        # --- System Reliability dropdown ---
        self.reliability_button = ttk.Button(
            self.sidebar, text="System Reliability ▸", style="Accent.TButton",
            command=self._toggle_reliability_menu
        )
        self.reliability_button.pack(fill="x", padx=12, pady=(6, 0))

        self.reliability_container = tk.Frame(self.sidebar, bg=PANEL_BG)
        self.reliability_container.pack(fill="x", padx=0, pady=0)
        self.reliability_frame = tk.Frame(self.reliability_container, bg=PANEL_BG)
        self.reliability_frame.pack_forget()

        tk.Button(self.reliability_frame, text="Site Reliability", bg=PANEL_BG, fg=CREAM,
                  relief="flat", anchor="w",
                  command=lambda: self.app.show_system_reliability()).pack(fill="x", pady=2)
        # --- Tables ---
        ttk.Button(self.sidebar, text="Tables w/ Info", style="Accent.TButton",
                   command=lambda: self.app.show_tables_with_info()).pack(fill="x", padx=12, pady=6)
        ttk.Button(self.sidebar, text="Tables w/o Info", style="Accent.TButton",
                   command=lambda: self.app.show_tables_without_info()).pack(fill="x", padx=12, pady=6)

        # DB connection label
        self.conn_label = tk.Label(self.sidebar, text="DB: Connecting...",
                                   bg=PANEL_BG, fg=CREAM)
        self.conn_label.pack(side="bottom", pady=10)
        # Button to open DB Profiles dialog
        ttk.Button(self.sidebar, text="DB Profiles", style="Accent.TButton",
                   command=lambda: ConnectionDialog(self, self.app.conn_mgr if hasattr(self.app, 'conn_mgr') else ConnectionManager(), self.app._on_db_apply if hasattr(self.app, '_on_db_apply') else (lambda *a, **k: None))).pack(side="bottom", fill="x", padx=12, pady=(0,6))

    def _create_main_panel(self):
        self.main_frame = ttk.Frame(self, style="Main.TFrame")
        self.main_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self.title_label = tk.Label(
            self.main_frame, text="", font=("Segoe UI", 18, "bold"),
            bg=BG_BLACK, fg=CREAM, anchor="w"
        )
        self.title_label.pack(fill="x", pady=(0, 5))

        table_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=(), show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    # --- Toggle methods ---
    def _toggle_alarm_menu(self):
        if self.alarm_submenu_visible:
            self.alarm_frame.pack_forget()
            self.alarm_button.config(text="Alarms ▸")
        else:
            self.alarm_frame.pack(fill="x", padx=24)
            self.alarm_button.config(text="Alarms ▾")
        self.alarm_submenu_visible = not self.alarm_submenu_visible

    def _toggle_reliability_menu(self):
        if self.reliability_submenu_visible:
            self.reliability_frame.pack_forget()
            self.reliability_button.config(text="System Reliability ▸")
        else:
            self.reliability_frame.pack(fill="x", padx=24)
            self.reliability_button.config(text="System Reliability ▾")
        self.reliability_submenu_visible = not self.reliability_submenu_visible

# ---------- APP CONTROLLER ----------
class UtilityApp:
    def __init__(self):
        # Initialize connection manager first so GUI can open connection dialog and
        # DatabaseManager can use an existing SQLAlchemy engine if available.
        try:
            self.conn_mgr = ConnectionManager()
        except Exception:
            # If connection manager fails for any reason, continue with no profiles
            self.conn_mgr = None

        # Prefer engine from connection manager if available
        eng = None
        if self.conn_mgr is not None and hasattr(self.conn_mgr, "engine"):
            eng = getattr(self.conn_mgr, "engine")

        if eng is not None:
            self.db = DatabaseManager(engine=eng)
        else:
            self.db = DatabaseManager()
            try:
                self.db.connect()
            except Exception as e:
                try:
                    messagebox.showerror("Connection Error", str(e))
                except Exception:
                    pass

        self.alarms = AlarmUtility(self.db)
        self.tables = TableUtility(self.db)
        self.devices = DeviceHealthUtility(self.db)
        self.gui = UtilityGUI(self)

        # Update connection label in GUI
        try:
            if self.conn_mgr and getattr(self.conn_mgr, "engine", None):
                self.gui.conn_label.config(text=f"DB: {getattr(self.conn_mgr.get_active(), 'name', 'engine')}")
            else:
                self.gui.conn_label.config(text=f"DB: {self.db.server}:{self.db.database}")
        except Exception:
            pass

        self.show_active_alarms()

    def _on_db_apply(self, profile: ConnectionProfile, engine: Engine):
        """Handler called when user selects 'Save & Use' in the ConnectionDialog.
        Replace the DatabaseManager to use the provided engine and refresh GUI label.
        """
        try:
            self.db = DatabaseManager(engine=engine)
            self.alarms = AlarmUtility(self.db)
            self.tables = TableUtility(self.db)
            self.devices = DeviceHealthUtility(self.db)
            if self.gui:
                self.gui.conn_label.config(text=f"DB: {profile.name}")
        except Exception as e:
            try:
                messagebox.showerror("DB Apply Error", str(e))
            except Exception:
                pass

    # ---- ALARM VIEWS ----
    def show_active_alarms(self):
        self.gui.title_label.config(text="Active Alarms")
        threading.Thread(target=self._load_active_alarms, daemon=True).start()

    def _load_active_alarms(self):
        try:
            rows = self.alarms.get_active()
            now = datetime.now()
            formatted = []
            for r in rows:
                activated = r[4]
                duration = now - activated
                days = duration.days
                hours, rem = divmod(duration.seconds, 3600)
                mins = rem // 60
                duration_str = f"{days}d {hours}h {mins}m"
                formatted.append((*r[:5], duration_str, r[7]))
        except Exception as e:
            self._show_error(str(e))
            return
        self._populate_tree(formatted, ("ID", "Source", "Alarm Name", "SiteID", "Activated", "Duration", "Title"))

    def show_repeated_alarms(self):
        self.gui.title_label.config(text="Repeated Alarms")
        threading.Thread(target=self._load_repeated_alarms, daemon=True).start()

    def _load_repeated_alarms(self):
        try:
            rows = self.alarms.get_repeated()
        except Exception as e:
            self._show_error(str(e))
            return
        self._populate_tree(rows, ("Alarm Name", "Site", "Occurrences", "Last Activated", "Title"))

    def show_orphan_alarms(self):
        self.gui.title_label.config(text="Orphan Alarms")
        threading.Thread(target=self._load_orphan_alarms, daemon=True).start()

    def _load_orphan_alarms(self):
        try:
            rows = self.alarms.get_orphan()
        except Exception as e:
            self._show_error(str(e))
            return
        self._populate_tree(rows, ("ID", "Source", "Name", "Site", "Activated", "System Time", "Title"))

    # ---- TABLE VIEWS ----
    def show_tables_with_info(self):
        self.gui.title_label.config(text="Tables with Info")
        rows = self.tables.get_with_info()
        # Format rows: ensure row counts are integers and formatted with commas
        formatted = []
        for r in rows:
            schema = r[0] if len(r) > 0 else ""
            table = r[1] if len(r) > 1 else ""
            cnt = r[2] if len(r) > 2 and r[2] is not None else 0
            try:
                cnt_str = f"{int(cnt):,}"
            except Exception:
                cnt_str = str(cnt)
            formatted.append((schema, table, cnt_str))
        self._populate_tree(formatted, ("Schema", "Table", "Rows"))

    def show_tables_without_info(self):
        self.gui.title_label.config(text="Tables without Info")
        rows = self.tables.get_without_info()
        formatted = []
        for r in rows:
            schema = r[0] if len(r) > 0 else ""
            table = r[1] if len(r) > 1 else ""
            cnt = r[2] if len(r) > 2 and r[2] is not None else 0
            try:
                cnt_str = f"{int(cnt):,}"
            except Exception:
                cnt_str = str(cnt)
            formatted.append((schema, table, cnt_str))
        self._populate_tree(formatted, ("Schema", "Table", "Rows"))

    # ---- DEVICE HEALTH VIEW ----
    def show_device_health(self):
        self.gui.title_label.config(text="Device Health")
        threading.Thread(target=self._load_device_health, daemon=True).start()

    def _load_device_health(self):
        try:
            rows = self.devices.get_device_status()
        except Exception as e:
            self._show_error(str(e))
            return
        # Post-process rows to infer normalized status: Critical, Warning, Good
        formatted = []
        now = datetime.now()
        for r in rows:
            # Expecting rows: (device_id, device_name, status, last_checked)
            try:
                device_id = r[0]
                device_name = r[1]
                raw_status = str(r[2]) if r[2] is not None else ""
                last_checked = r[3] if len(r) > 3 else None
            except Exception:
                # If row shape is unexpected, coerce to strings
                device_id = r[0] if len(r) > 0 else ""
                device_name = r[1] if len(r) > 1 else ""
                raw_status = str(r[2]) if len(r) > 2 else ""
                last_checked = r[3] if len(r) > 3 else None

            # Normalize last_checked to datetime or None
            lc_dt = None
            try:
                if isinstance(last_checked, str):
                    try:
                        lc_dt = datetime.fromisoformat(last_checked)
                    except Exception:
                        lc_dt = None
                else:
                    lc_dt = last_checked
            except Exception:
                lc_dt = None

            # Determine inferred status
            s = raw_status.lower()
            inferred = "Good"
            if any(tok in s for tok in ("dead", "critical", "no data", "deleted")):
                inferred = "Critical"
            elif "offline" in s:
                # offline more than 7 days -> critical, else warning
                if lc_dt is None:
                    inferred = "Critical"
                else:
                    try:
                        if (now - lc_dt).days >= 7:
                            inferred = "Critical"
                        else:
                            inferred = "Warning"
                    except Exception:
                        inferred = "Warning"
            elif any(tok in s for tok in ("dead","critical")):
                inferred = "Critical"
            elif any(tok in s for tok in ("low","lolo","warning","battery")):
                # treat battery low/status as Warning unless clearly critical
                if "dead" in s or "critical" in s:
                    inferred = "Critical"
                else:
                    inferred = "Warning"

            # If last_checked is very recent and no issues, keep Good
            if inferred == "Good" and lc_dt is not None:
                try:
                    if (now - lc_dt).days >= 30:
                        # no recent check in 30+ days -> Warning
                        inferred = "Warning"
                except Exception:
                    pass

            # Format last_checked string
            if lc_dt is None:
                last_str = "Unknown"
            else:
                try:
                    last_str = lc_dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    last_str = str(lc_dt)

            formatted.append((device_id, device_name, inferred, last_str))

        self._populate_tree(formatted, ("Device ID", "Device Name", "Status", "Last Checked"))

    # ---- System Reliability View----
    def show_system_reliability(self):
        self.gui.title_label.config(text="System Reliability & Operations")
        threading.Thread(target=self._load_system_reliability, daemon=True).start()

    def _load_system_reliability(self):
        try:
            util = SystemReliabilityUtility(self.db)
            rows = util.get_site_reliability()
            formatted_rows = util.format_for_treeview(rows)
        except Exception as e:
            self._show_error(str(e))
            return
        self._populate_tree(formatted_rows, ("Site ID", "Outages", "Downtime (s)", "Expected Uptime (s)", "Reliability Score"))

    # ---- HELPERS ----
    def _populate_tree(self, rows, cols):
        tree = self.gui.tree
        tree.delete(*tree.get_children())
        tree["columns"] = cols
        tree["show"] = "headings"

        for c in cols:
            # Configure headings and column anchors by semantic column name
            col_anchor = "center"
            col_width = 150
            lc = c.lower()
            if "rows" in lc or lc.endswith("(s)") or lc.strip().lower() in ("rows",):
                col_anchor = "e"
                col_width = 120
            elif "table" in lc or "device name" in lc or "alarm name" in lc or "title" in lc:
                col_anchor = "w"
                col_width = 320
            elif "schema" in lc:
                col_anchor = "w"
                col_width = 180
            elif "id" in lc and "message" not in lc and "device name" not in lc:
                col_anchor = "center"
                col_width = 120
            elif "message" in lc:
                col_anchor = "center"
                col_width = 800
            tree.heading(c, text=c, anchor=col_anchor)
            tree.column(c, width=col_width, anchor=col_anchor)

        if not rows:
            tree["columns"] = ("Message",)
            tree.heading("Message", text="")
            tree.column("Message", anchor="center", width=800)
            tree.insert("", "end", values=("⚠️ No data found.",))
            return

        for i, r in enumerate(rows):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            # If we're showing Device Health, map normalized statuses to colored tags
            if cols == ("Device ID", "Device Name", "Status", "Last Checked"):
                status = str(r[2]).strip().lower()  # third column is Status
                if status == "critical":
                    tag = "status_critical"
                elif status == "warning":
                    tag = "status_warning"
                elif status == "good":
                    tag = "status_good"
                else:
                    # Fallback heuristics for legacy/raw values
                    if any(tok in status for tok in ("battery", "offline", "no data", "deleted", "out of service", "dead", "critical")):
                        tag = "status_warning"
            tree.insert("", "end", values=r, tags=(tag,))

        # Configure row tag styles (parity + status)
        tree.tag_configure("evenrow", background="#000000", foreground=CREAM)
        tree.tag_configure("oddrow", background="#0f3021", foreground=CREAM)
        tree.tag_configure("status_critical", background="#661111", foreground=CREAM)
        tree.tag_configure("status_warning", background="#7a4e00", foreground=CREAM)
        tree.tag_configure("status_good", background=DARK_GREEN, foreground=CREAM)

    def _show_error(self, msg):
        messagebox.showerror("Error", msg)


if __name__ == "__main__":
    app = UtilityApp()
    app.gui.mainloop()
