#title: 'Alarms'
#btn: 'Active'
#btn: 'Repeated'
#btn: 'Orphan'

import pyodbc
from datetime import datetime, timedelta

SQL_SERVER = "HAILEY"
DATABASE = "MCRWS-Telog"

class AlarmUtility:
    def __init__(self):
        self.conn = self.connect_db()

    def connect_db(self):
        """Connect to SQL Server using ODBC."""
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE};Trusted_Connection=yes;"
        try:
            return pyodbc.connect(conn_str, autocommit=True, timeout=5)
        except pyodbc.Error:
            # fallback to ODBC Driver 18
            conn_str = conn_str.replace("ODBC Driver 17", "ODBC Driver 18")
            return pyodbc.connect(conn_str, autocommit=True, timeout=5)

    def query(self, sql, params=None):
        """Run a read-only query."""
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchall()

    # ---------------- ALARMS ----------------
    def get_active(self):
        sql = """
        SELECT alarm_history_id, alarm_source_id, alarm_name, site_id, 
               alarm_activation_time, alarm_deactivation_time, alarm_active, alarm_title
        FROM dbo.alarm_history
        WHERE alarm_active = 1
        ORDER BY alarm_activation_time DESC;
        """
        rows = self.query(sql)
        now = datetime.now()
        formatted = []
        for r in rows:
            activated = r[4]
            duration = now - activated
            duration_str = f"{duration.days}d {duration.seconds//3600}h {(duration.seconds//60)%60}m"
            formatted.append((r[0], r[1], r[2], r[3], r[4], duration_str, r[7]))
        columns = ("ID", "Source", "Name", "SiteID", "Activated", "Duration", "Title")
        return columns, formatted

    def get_repeated(self):
        one_week_ago = datetime.now() - timedelta(days=7)
        sql = """
        SELECT alarm_name, site_id, COUNT(*) AS occ_count, MAX(alarm_activation_time), MAX(alarm_title)
        FROM dbo.alarm_history
        WHERE alarm_activation_time >= ?
        GROUP BY alarm_name, site_id
        HAVING COUNT(*) >= 2
        ORDER BY occ_count DESC;
        """
        rows = self.query(sql, [one_week_ago])
        formatted = [(r[0], r[1], r[2], r[3], r[4]) for r in rows]
        columns = ("Alarm Name", "Site", "Occurrences", "Last Activated", "Title")
        return columns, formatted

    def get_orphan(self):
        sql = """
        SELECT ah.alarm_history_id, ah.alarm_source_id, ah.alarm_name, ah.site_id, 
               ah.alarm_activation_time, ah.alarm_deactivation_time, 
               ah.alarm_system_time, ah.alarm_title
        FROM dbo.alarm_history AS ah
        LEFT JOIN dbo.sites AS s ON ah.site_id = s.site_id
        WHERE s.site_id IS NULL
        ORDER BY ah.alarm_activation_time DESC;
        """
        rows = self.query(sql)
        formatted = [(r[0], r[1], r[2], r[3], r[4], r[6], r[7]) for r in rows]
        columns = ("ID", "Source", "Name", "SiteID", "Activated", "System Time", "Title")
        return columns, formatted


# Optional standalone test
if __name__ == "__main__":
    alarms = AlarmUtility()
    '''for btn in ["get_active", "get_repeated", "get_orphan"]:
        cols, rows = getattr(alarms, btn)()
        print(f"\n{btn.upper()}:")
        print(cols)
        for r in rows:
            print(r)'''
