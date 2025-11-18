'''Current GUI as of 11/5/25 1331
*** Reads every SQL dump placed in python/sql_data ***
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
from tkinter import ttk, messagebox
import threading
import sys
from datetime import datetime

from local_sql_loader import LocalSqlDatabase

# ---------- CONFIG ----------
REFRESH_MS = 60_000

BG_BLACK = "#000000"
CREAM = "#FFF8E1"
DARK_GREEN = "#0b5d3b"
PANEL_BG = "#0f0f0f"
TEXT_COLOR = CREAM
# ----------------------------


def _parse_timestamp(value):
    if not value or value in ("NULL", "null"):
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


# ---------- DATABASE ----------
class DatabaseManager(LocalSqlDatabase):
    def __init__(self):
        super().__init__()

    def connect(self):
        return self.conn

# ---------- UTILITIES ----------
class AlarmUtility:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_active(self):
        sql = """
        SELECT alarm_history_id, alarm_source_id, alarm_name, site_id, 
               alarm_activation_time, alarm_deactivation_time, alarm_active, alarm_title
        FROM dbo.alarm_history
        WHERE IFNULL(alarm_active, '0') = '1'
              OR alarm_deactivation_time IS NULL
              OR alarm_deactivation_time = ''
              OR UPPER(alarm_deactivation_time) = 'NULL'
        ORDER BY datetime(alarm_activation_time) DESC
        LIMIT 200;
        """
        rows = self.db.query(sql)
        if rows:
            return rows
        fallback = """
        SELECT alarm_history_id, alarm_source_id, alarm_name, site_id, 
               alarm_activation_time, alarm_deactivation_time, alarm_active, alarm_title
        FROM dbo.alarm_history
        ORDER BY datetime(alarm_activation_time) DESC
        LIMIT 200;
        """
        return self.db.query(fallback)

    def get_repeated(self):
        sql = """
        SELECT alarm_name, site_id, COUNT(*) AS occ_count, 
               MAX(alarm_activation_time) AS last_activated, MAX(alarm_title)
        FROM dbo.alarm_history
        GROUP BY alarm_name, site_id
        HAVING COUNT(*) >= 2
        ORDER BY occ_count DESC, datetime(last_activated) DESC
        LIMIT 200;
        """
        return self.db.query(sql)

    def get_orphan(self):
        sql = """
        SELECT ah.alarm_history_id, ah.alarm_source_id, ah.alarm_name, ah.site_id, 
               ah.alarm_activation_time, ah.alarm_deactivation_time, 
               ah.alarm_system_time, ah.alarm_title
        FROM dbo.alarm_history AS ah
        LEFT JOIN dbo.sites_table AS s ON ah.site_id = s.site_id
        WHERE s.site_id IS NULL
               OR ah.measurement_id IS NULL
               OR UPPER(ah.measurement_id) = 'NULL'
        ORDER BY datetime(ah.alarm_activation_time) DESC
        LIMIT 200;
        """
        return self.db.query(sql)


class TableUtility:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all_tables(self):
        sql = """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name LIKE 'dbo.%'
        ORDER BY name;
        """
        tables = self.db.query(sql)
        rows = []
        for (name,) in tables:
            schema, table = name.split(".", 1)
            count_sql = f"SELECT COUNT(*) FROM {name}"
            row_count = self.db.scalar(count_sql) or 0
            rows.append((schema, table, row_count))
        return rows

    def get_with_info(self):
        return [r for r in self.get_all_tables() if (r[2] or 0) > 0]

    def get_without_info(self):
        return [r for r in self.get_all_tables() if (r[2] or 0) == 0]


class DeviceHealthUtility:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_device_status(self):
        sql = """
        SELECT device_id,
               device_name,
               device_type_id,
               device_leave_modem_on,
               device_leave_switcher_off
        FROM dbo.devices
        ORDER BY device_name ASC;
        """
        return self.db.query(sql)
class SystemReliabilityUtility:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_site_reliability(self):
        sql = """
        SELECT site_id,
               alarm_activation_time,
               alarm_deactivation_time
        FROM dbo.alarm_history
        WHERE alarm_activation_time IS NOT NULL
        ORDER BY site_id
        LIMIT 10000;
        """

        rows = self.db.query(sql)
        summary = {}
        for site_id, activated, deactivated in rows:
            start = _parse_timestamp(activated)
            end = _parse_timestamp(deactivated) or start
            if not start:
                continue
            delta = max((end - start).total_seconds(), 0) if end else 0
            data = summary.setdefault(
                site_id,
                {"outages": 0, "downtime": 0.0, "first": start, "last": start},
            )
            data["outages"] += 1
            data["downtime"] += delta
            if start < data["first"]:
                data["first"] = start
            if end and end > data["last"]:
                data["last"] = end

        results = []
        for site_id, data in summary.items():
            span = max((data["last"] - data["first"]).total_seconds(), 1)
            expected = max(span, data["downtime"])
            reliability = max(0.0, 1.0 - (data["downtime"] / expected))
            results.append((site_id, data["outages"], int(data["downtime"]), int(expected), reliability))

        results.sort(key=lambda r: (r[4], -r[1]))
        return results

    def format_for_treeview(self, rows):
        """
        Convert raw SQL output into formatted lists for Treeview.
        Adds comma separators for large numbers and two decimals for reliability.
        """
        formatted = []
        for r in rows:
            site_id, outages, downtime, expected, reliability = r
            formatted.append([
                str(site_id),
                str(outages),
                f"{downtime:,}",       # 123456 -> 123,456
                f"{expected:,}",       # 123456 -> 123,456
                f"{reliability:.2f}"   # 0.95432 -> 0.95
            ])
        return formatted



# ---------- GUI ----------
class UtilityGUI(tk.Tk):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.title("Utility App")
        self._maximize_window()
        self.configure(bg=BG_BLACK)
        self._setup_styles()
        self._create_sidebar()
        self._create_main_panel()
        self.alarm_submenu_visible = False
        self.reliability_submenu_visible = False

    def _maximize_window(self):
        """Cross-platform friendly maximize helper."""
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

    def set_selected_database(self, _index: int):
        """Placeholder retained for compatibility."""
        return

# ---------- APP CONTROLLER ----------
class UtilityApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.db.connect()

        self.alarms = AlarmUtility(self.db)
        self.tables = TableUtility(self.db)
        self.devices = DeviceHealthUtility(self.db)
        self.gui = UtilityGUI(self)
        self.gui.conn_label.config(text="Data: Local SQL dumps")

        self.show_active_alarms()

    # ---- ALARM VIEWS ----
    def show_active_alarms(self):
        self.gui.title_label.config(text="Active Alarms")
        threading.Thread(target=self._load_active_alarms, daemon=True).start()

    def _load_active_alarms(self):
        try:
            rows = self.alarms.get_active()
            now = datetime.utcnow()
            formatted = []
            for r in rows:
                activated = _parse_timestamp(r[4])
                duration = now - activated if activated else None
                days = duration.days if duration else 0
                seconds = duration.seconds if duration else 0
                hours, rem = divmod(seconds, 3600)
                mins = rem // 60
                duration_str = f"{days}d {hours}h {mins}m" if duration else "N/A"
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
        self._populate_tree(rows, ("Schema", "Table", "Rows"))

    def show_tables_without_info(self):
        self.gui.title_label.config(text="Tables without Info")
        rows = self.tables.get_without_info()
        self._populate_tree(rows, ("Schema", "Table", "Rows"))

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
        formatted = []
        for r in rows:
            modem = "Yes" if str(r[3]).strip() == "1" else "No"
            switcher = "Yes" if str(r[4]).strip() == "1" else "No"
            formatted.append((r[0], r[1], r[2], modem, switcher))
        self._populate_tree(formatted, ("Device ID", "Device Name", "Type", "Leave Modem On", "Leave Switcher Off"))

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

    def _show_error(self, msg):
        messagebox.showerror("Error", msg)


if __name__ == "__main__":
    try:
        app = UtilityApp()
    except FileNotFoundError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Missing SQL data",
            f"{exc}\n\nDrop at least one .sql file into sql_data/ and restart the tool.",
        )
        root.destroy()
        sys.exit(0)
    app.gui.mainloop()
