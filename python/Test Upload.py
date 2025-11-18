"""
My custom utilities for the group project.
Written by Andres — With comments that explain everything
so y’all know exactly what I added and why.

NOTE:
    - This script does NOT change the GUI.
    - This script plugs into the GUI using the same structure as generic.py.
    - All SQL is written for SQL Server.
    - If a table name doesn’t exist on your local database, the code safely fails
      and the GUI won’t crash.

How to use:
    - Add: `from my_utilities import DeviceHealthUtility, TableInfoUtility`
      in whichever main file you are integrating.
    - Then initialize these in UtilityApp the same way you did for SystemReliabilityUtility.
"""

# ===============================
#       IMPORTS
# ===============================
# These are the only imports needed because everything goes through DatabaseManager.
# DatabaseManager takes care of the SQL Server connection.
# (The GUI file already imports everything else.)

from datetime import datetime


# ======================================================================
#                     DEVICE HEALTH UTILITY
# ======================================================================

class DeviceHealthUtility:
    """
    My Device Health utility.
    This is the part of the project that I built out. This allows the GUI
    to show battery health, voltage stats, and offline devices.

    IMPORTANT:
        Replace the placeholder table name below (dbo.DeviceBatteryHistory)
        with whatever table in the telemetry dumps actually contains
        voltage or device reading timestamps. I coded assuming generic names
        so the GUI doesn’t break.
    """

    def __init__(self, db):
        self.db = db

    def get_battery_health(self):
        """
        Returns aggregated battery/voltage stats for each device.
        This builds the Device Health table in the GUI.

        Logic:
            - Average voltage
            - Min voltage
            - Max voltage
            - Last time device checked in
            - Automatic health classification

        If the table does not exist, GUI shows an empty table safely.
        """

        sql = """
        WITH BatteryAgg AS (
            SELECT
                site_id,
                device_id,
                MAX(sample_time) AS last_seen,
                AVG(CAST(ISNULL(battery_voltage, 0.0) AS FLOAT)) AS avg_voltage,
                MIN(CAST(ISNULL(battery_voltage, 0.0) AS FLOAT)) AS min_voltage,
                MAX(CAST(ISNULL(battery_voltage, 0.0) AS FLOAT)) AS max_voltage
            FROM dbo.DeviceBatteryHistory   -- TODO: Replace table name with your actual voltage table
            GROUP BY site_id, device_id
        )
        SELECT
            site_id,
            device_id,
            last_seen,
            avg_voltage,
            min_voltage,
            max_voltage,
            CASE
                WHEN avg_voltage < 11.5 THEN 'CRITICAL'
                WHEN avg_voltage < 12.0 THEN 'WARNING'
                ELSE 'OK'
            END AS health_status
        FROM BatteryAgg
        ORDER BY health_status DESC, last_seen DESC;
        """

        try:
            return self.db.query(sql)
        except Exception:
            return []  # Fails safely if table missing

    def get_offline_devices(self, days_offline=7):
        """
        Returns devices that haven’t checked in for X days.
        This is an optional add-on tab if the team wants it.

        Default:
            days_offline = 7
        """

        sql = f"""
        SELECT
            site_id,
            device_id,
            MAX(sample_time) AS last_seen
        FROM dbo.DeviceBatteryHistory   -- TODO: Replace with actual table name
        GROUP BY site_id, device_id
        HAVING DATEDIFF(DAY, MAX(sample_time), GETDATE()) >= {days_offline}
        ORDER BY last_seen ASC;
        """

        try:
            return self.db.query(sql)
        except Exception:
            return []  # Fail safe

    # ========== Formatting helpers (for GUI Treeview) ==========

    def format_battery_for_treeview(self, rows):
        """
        Formats battery health rows into Treeview-friendly lists.
        """
        formatted = []
        for r in rows:
            site_id, device_id, last_seen, avg_v, min_v, max_v, status = r

            formatted.append([
                str(site_id),
                str(device_id),
                str(last_seen),
                f"{avg_v:.2f}" if avg_v else "0.00",
                f"{min_v:.2f}" if min_v else "0.00",
                f"{max_v:.2f}" if max_v else "0.00",
                status,
            ])
        return formatted

    def format_offline_for_treeview(self, rows):
        """
        Formatting helper for offline devices.
        """
        formatted = []
        for r in rows:
            site_id, device_id, last_seen = r

            formatted.append([
                str(site_id),
                str(device_id),
                str(last_seen),
            ])
        return formatted



# ======================================================================
#                     TABLE INFORMATION UTILITY
# ======================================================================

class TableInfoUtility:
    """
    This utility handles "Tables w/ Info" and "Tables w/o Info".
    Very useful for development, debugging, and understanding what’s inside
    this monster SQL database we inherited.

    This uses sys.tables, sys.schemas, and sys.partitions (standard SQL Server).
    """

    def __init__(self, db):
        self.db = db

    def get_tables_with_info(self, min_rows=1):
        """
        Returns tables that contain data.
        """
        sql = f"""
        SELECT
            s.name AS schema_name,
            t.name AS table_name,
            p.rows AS row_count
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        LEFT JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0,1)
        GROUP BY s.name, t.name, p.rows
        HAVING ISNULL(p.rows, 0) >= {min_rows}
        ORDER BY row_count DESC, s.name, t.name;
        """

        try:
            return self.db.query(sql)
        except:
            return []

    def get_tables_without_info(self):
        """
        Returns tables with exactly zero rows.
        """
        sql = """
        SELECT
            s.name AS schema_name,
            t.name AS table_name,
            ISNULL(p.rows, 0) AS row_count
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        LEFT JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0,1)
        GROUP BY s.name, t.name, p.rows
        HAVING ISNULL(p.rows, 0) = 0
        ORDER BY s.name, t.name;
        """

        try:
            return self.db.query(sql)
        except:
            return []

    # ========== Formatting helper ==========

    def format_for_treeview(self, rows):
        """
        Formats results for the Tkinter Treeview.
        """
        formatted = []
        for r in rows:
            schema_name, table_name, row_count = r

            formatted.append([
                schema_name,
                table_name,
                f"{row_count:,}",
            ])
        return formatted

# ======================================================================
#                     STATISTICAL SUMMARY UTILITY
# ======================================================================

class StatisticalSummaryUtility:
    """
    This class gives us basic statistical summaries from any numeric column.
    I'm adding this because our team talked about “statistical inference”
    but nobody had a clean way to do it yet.

    Usage:
        stats_util = StatisticalSummaryUtility(self.db)
        rows = stats_util.summarize("dbo.alarm_log", "alarm_event_duration")
    """

    def __init__(self, db):
        self.db = db

    def summarize(self, table_name, column_name):
        """
        Returns count, avg, min, max, stdev, variance on any numeric column.
        The GUI can dump this into the TreeView or into a pop-up.

        SQL Server 2022 supports STDEV, VAR, etc. — so this works out of the box.

        Example call:
            summarize("dbo.DeviceBatteryHistory", "battery_voltage")
        """
        sql = f"""
        SELECT
            COUNT({column_name}) AS count_values,
            AVG(CAST({column_name} AS FLOAT)) AS avg_val,
            MIN(CAST({column_name} AS FLOAT)) AS min_val,
            MAX(CAST({column_name} AS FLOAT)) AS max_val,
            STDEV(CAST({column_name} AS FLOAT)) AS std_dev,
            VAR(CAST({column_name} AS FLOAT)) AS variance
        FROM {table_name};
        """

        try:
            return self.db.query(sql)
        except Exception:
            return []

    def format_stats_for_treeview(self, rows):
        """
        Formats stats result for TreeView.
        """
        if not rows:
            return []

        r = rows[0]
        count_v, avg_v, min_v, max_v, std_v, var_v = r

        return [[
            f"{count_v:,}",
            f"{avg_v:.3f}" if avg_v else "0.000",
            f"{min_v:.3f}" if min_v else "0.000",
            f"{max_v:.3f}" if max_v else "0.000",
            f"{std_v:.3f}" if std_v else "0.000",
            f"{var_v:.3f}" if var_v else "0.000",
        ]]
    
# ======================================================================
#                     CORRELATION ANALYSIS UTILITY
# ======================================================================

class CorrelationUtility:
    """
    This class computes correlation between any two numeric columns.
    This was brought up by the team in the messages (“predictive categories”)
    so now we can do it for real.

    The correlation formula used:
        Pearson Correlation Coefficient
    """

    def __init__(self, db):
        self.db = db

    def correlation(self, table, col_x, col_y):
        """
        Computes correlation using SQL math.
        Returns a single value between -1 and 1.
        """

        sql = f"""
        SELECT
            (SUM(({col_x} - (SELECT AVG({col_x}) FROM {table}))
                 * ({col_y} - (SELECT AVG({col_y}) FROM {table})))
            /
            (SQRT(SUM(POWER({col_x} - (SELECT AVG({col_x}) FROM {table}), 2)))
             * 
             SQRT(SUM(POWER({col_y} - (SELECT AVG({col_y}) FROM {table}), 2))))
            AS correlation_value
        FROM {table}
        WHERE {col_x} IS NOT NULL AND {col_y} IS NOT NULL;
        """

        try:
            return self.db.query(sql)
        except:
            return []

    def format_corr_for_treeview(self, rows):
        """
        Format correlation output for GUI.
        """
        if not rows:
            return [["N/A"]]

        val = rows[0][0]
        if val is None:
            return [["N/A"]]

        return [[f"{val:.4f}"]]
    
# ======================================================================
#                     ANOMALY DETECTION UTILITY
# ======================================================================

class AnomalyDetectionUtility:
    """
    Simple anomaly detection using Z-score.

    Why?
        Our team discussed missing/outlier data and seasonal anomalies.
        This class gives us a starting point that is database-agnostic.

    Z-score rule:
        Values with |z| > threshold are flagged as anomalies.
    """

    def __init__(self, db):
        self.db = db

    def find_anomalies(self, table, column, z_threshold=3.0):
        """
        Finds values that exceed the Z-score threshold.

        SQL Strategy:
            - Compute mean + stdev
            - Compute Z-score for each row
            - Filter by |Z| > threshold
        """

        sql = f"""
        WITH stats AS (
            SELECT
                AVG(CAST({column} AS FLOAT)) AS mean_val,
                STDEV(CAST({column} AS FLOAT)) AS std_val
            FROM {table}
        ),
        zscores AS (
            SELECT
                *,
                (CAST({column} AS FLOAT) - stats.mean_val) / NULLIF(stats.std_val, 0) AS zscore
            FROM {table}, stats
            WHERE {column} IS NOT NULL
        )
        SELECT *
        FROM zscores
        WHERE ABS(zscore) > {z_threshold}
        ORDER BY zscore DESC;
        """

        try:
            return self.db.query(sql)
        except:
            return []

    def format_anomalies(self, rows):
        """
        Returns rows formatted for GUI preview.
        Only returns the first ~50 to prevent GUI overload.
        """
        formatted = []
        for r in rows[:50]:
            # We don't know table structure; convert everything to string
            formatted.append([str(x) for x in r])
        return formatted
# ===========================================================================
#                      END OF MY UTILITY SCRIPT
# ===========================================================================
