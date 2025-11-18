#title: 'Alarms'
#btn: 'Active'
#btn: 'Repeated'
#btn: 'Orphan'

from datetime import datetime

from local_sql_loader import LocalSqlDatabase


class AlarmUtility:
    def __init__(self, db: LocalSqlDatabase | None = None):
        self.db = db or LocalSqlDatabase()

    def query(self, sql, params=None):
        return self.db.query(sql, params)

    def _parse_timestamp(self, value):
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

    def _format_duration(self, delta: timedelta | None):
        if not delta:
            return "N/A"
        seconds = int(delta.total_seconds())
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        mins = rem // 60
        return f"{days}d {hours}h {mins}m"

    # ---------------- ALARMS ----------------
    def get_active(self):
        base_sql = """
        SELECT alarm_history_id,
               alarm_source_id,
               alarm_name,
               site_id,
               alarm_activation_time,
               alarm_deactivation_time,
               alarm_active,
               alarm_title
        FROM dbo.alarm_history
        WHERE IFNULL(alarm_active, '0') = '1'
              OR alarm_deactivation_time IS NULL
              OR alarm_deactivation_time = ''
              OR UPPER(alarm_deactivation_time) = 'NULL'
        ORDER BY datetime(alarm_activation_time) DESC
        LIMIT 200;
        """
        rows = self.query(base_sql)
        if not rows:
            rows = self.query(
                """
                SELECT alarm_history_id,
                       alarm_source_id,
                       alarm_name,
                       site_id,
                       alarm_activation_time,
                       alarm_deactivation_time,
                       alarm_active,
                       alarm_title
                FROM dbo.alarm_history
                ORDER BY datetime(alarm_activation_time) DESC
                LIMIT 200;
                """
            )
        now = datetime.utcnow()
        formatted = []
        for r in rows:
            activated = self._parse_timestamp(r[4])
            duration = self._format_duration(now - activated if activated else None)
            formatted.append((r[0], r[1], r[2], r[3], r[4], duration, r[7]))
        columns = ("ID", "Source", "Name", "SiteID", "Activated", "Duration", "Title")
        return columns, formatted

    def get_repeated(self):
        sql = """
        SELECT alarm_name,
               site_id,
               COUNT(*) AS occ_count,
               MAX(alarm_activation_time) AS last_activated,
               MAX(alarm_title) AS alarm_title
        FROM dbo.alarm_history
        GROUP BY alarm_name, site_id
        HAVING COUNT(*) >= 2
        ORDER BY occ_count DESC, datetime(last_activated) DESC
        LIMIT 200;
        """
        rows = self.query(sql)
        formatted = [(r[0], r[1], r[2], r[3], r[4]) for r in rows]
        columns = ("Alarm Name", "Site", "Occurrences", "Last Activated", "Title")
        return columns, formatted

    def get_orphan(self):
        sql = """
        SELECT ah.alarm_history_id,
               ah.alarm_source_id,
               ah.alarm_name,
               ah.site_id,
               ah.alarm_activation_time,
               ah.alarm_system_time,
               ah.alarm_title
        FROM dbo.alarm_history AS ah
        LEFT JOIN dbo.sites_table AS s ON ah.site_id = s.site_id
        WHERE s.site_id IS NULL
               OR ah.measurement_id IS NULL
               OR UPPER(ah.measurement_id) = 'NULL'
        ORDER BY datetime(ah.alarm_activation_time) DESC
        LIMIT 200;
        """
        rows = self.query(sql)
        formatted = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows]
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
