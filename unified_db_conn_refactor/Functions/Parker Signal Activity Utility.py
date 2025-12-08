''' ======================================================================
                         SIGNAL ACTIVITY UTILITY
 ======================================================================'''
#title: 'Signal Activity'
#btn: 'High Runtime Signals'
#btn: 'Flatlined Signals'

from typing import List, Tuple, Any

# ---------------- Module Class ----------------
class SignalActivityUtility:
    """
    DynamicUtilityApp-compatible module for analyzing signal activity
    from the Telog trend_data table.

    Buttons (from metadata above):
      - 'High Runtime Signals'  -> get_high_runtime_signals()
      - 'Flatlined Signals'     -> get_flatlined_signals()

    Each getter MUST:
      - Be lowercase
      - Match button name with spaces -> underscores
      - Return (columns, rows)
    """

    def __init__(self, db):
        """
        Initialize column mappings and attach shared DB client.
        Adjust table/column names here if they differ in SQL Server.
        """
        self.db = db

        # ---- TABLE & COLUMN MAPPINGS ----
        # Matches MCRWS_Telog_csv/dbo.trend_data.csv headers
        self.trend_table = "dbo.trend_data"
        self.col_signal_id = "measurement_id"      # e.g. '1_0GP'
        self.col_time      = "trend_data_time"     # datetime
        self.col_interval  = "trend_data_interval" # in seconds (optional)
        self.col_value     = "trend_data_avg"      # numeric

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _query(self, sql: str, params: List[Any] = None):
        """
        Simple query wrapper.
        """
        return self.db.query(sql, params or [])

    # ------------------------------------------------------------------
    # 1) High Runtime Signals
    # Button: 'High Runtime Signals' -> get_high_runtime_signals()
    # ------------------------------------------------------------------
    def get_high_runtime_signals(self) -> Tuple[Tuple[str, ...], List[Tuple[Any, ...]]]:
        """
        Getter for 'High Runtime Signals' button.

        Identifies signals that are "active" (value <> 0) for a large
        fraction of samples in the last N days.

        Returns:
            columns: ("Signal ID", "Samples", "Active Samples", "Active %", "Min", "Max", "Avg")
            rows:    list of tuples, already formatted for the GUI.
        """
        days_back = 7
        min_active_pct = 0.5  # 50%

        sql = f"""
        WITH Recent AS (
            SELECT
                {self.col_signal_id}  AS signal_id,
                {self.col_time}       AS sample_time,
                {self.col_value}      AS value
            FROM {self.trend_table}
            WHERE {self.col_time} >= DATEADD(DAY, -{days_back}, GETDATE())
        ),
        Agg AS (
            SELECT
                signal_id,
                COUNT(*) AS sample_count,
                SUM(CASE WHEN value IS NOT NULL AND value <> 0 THEN 1 ELSE 0 END) AS active_count,
                MIN(value) AS min_value,
                MAX(value) AS max_value,
                AVG(CAST(value AS FLOAT)) AS avg_value
            FROM Recent
            GROUP BY signal_id
        )
        SELECT
            signal_id,
            sample_count,
            active_count,
            CAST(active_count * 1.0 / NULLIF(sample_count, 0) AS DECIMAL(10,4)) AS active_pct,
            min_value,
            max_value,
            avg_value
        FROM Agg
        WHERE (active_count * 1.0 / NULLIF(sample_count, 0)) >= {min_active_pct}
        ORDER BY active_pct DESC, sample_count DESC;
        """

        columns = (
            "Signal ID",
            "Samples",
            "Active Samples",
            "Active %",
            "Min",
            "Max",
            "Avg",
        )

        try:
            raw_rows = self._query(sql)
        except Exception as e:
            # If something goes wrong (bad columns, table missing, etc.)
            return ("Message",), [(f"Error in High Runtime query: {e}",)]

        # Format for readability
        rows: List[Tuple[Any, ...]] = []
        for r in raw_rows:
            signal_id, sample_count, active_count, active_pct, vmin, vmax, vavg = r
            rows.append((
                str(signal_id),
                int(sample_count or 0),
                int(active_count or 0),
                f"{float(active_pct or 0.0):.2%}",
                "" if vmin is None else f"{float(vmin):.3f}",
                "" if vmax is None else f"{float(vmax):.3f}",
                "" if vavg is None else f"{float(vavg):.3f}",
            ))

        return columns, rows

    # ------------------------------------------------------------------
    # 2) Flatlined Signals
    # Button: 'Flatlined Signals' -> get_flatlined_signals()
    # ------------------------------------------------------------------
    def get_flatlined_signals(self) -> Tuple[Tuple[str, ...], List[Tuple[Any, ...]]]:
        """
        Getter for 'Flatlined Signals' button.

        Identifies signals whose values barely change (very low std dev)
        over the last N days.

        Returns:
            columns: ("Signal ID", "Samples", "Min", "Max", "Avg", "Std Dev")
            rows:    list of tuples, already formatted for the GUI.
        """
        days_back = 30
        max_stddev = 0.0001

        sql = f"""
        WITH Recent AS (
            SELECT
                {self.col_signal_id}  AS signal_id,
                {self.col_value}      AS value
            FROM {self.trend_table}
            WHERE {self.col_time} >= DATEADD(DAY, -{days_back}, GETDATE())
        ),
        Agg AS (
            SELECT
                signal_id,
                COUNT(*) AS sample_count,
                MIN(value) AS min_value,
                MAX(value) AS max_value,
                AVG(CAST(value AS FLOAT)) AS avg_value,
                STDEV(CAST(value AS FLOAT)) AS stddev_value
            FROM Recent
            GROUP BY signal_id
        )
        SELECT
            signal_id,
            sample_count,
            min_value,
            max_value,
            avg_value,
            stddev_value
        FROM Agg
        WHERE
            sample_count > 0
            AND ISNULL(stddev_value, 0) <= {max_stddev}
        ORDER BY sample_count DESC;
        """

        columns = (
            "Signal ID",
            "Samples",
            "Min",
            "Max",
            "Avg",
            "Std Dev",
        )

        try:
            raw_rows = self._query(sql)
        except Exception as e:
            return ("Message",), [(f"Error in Flatlined query: {e}",)]

        rows: List[Tuple[Any, ...]] = []
        for r in raw_rows:
            signal_id, sample_count, vmin, vmax, vavg, vstd = r
            rows.append((
                str(signal_id),
                int(sample_count or 0),
                "" if vmin is None else f"{float(vmin):.3f}",
                "" if vmax is None else f"{float(vmax):.3f}",
                "" if vavg is None else f"{float(vavg):.3f}",
                "" if vstd is None else f"{float(vstd):.5f}",
            ))

        return columns, rows


# ---------------- Optional Standalone Test ----------------
if __name__ == "__main__":
    mod = SignalActivityUtility()
    for func_name in ["get_high_runtime_signals", "get_flatlined_signals"]:
        cols, rows = getattr(mod, func_name)()
        print("\n", func_name.upper())
        print(cols)
        for row in rows[:10]:
            print(row)
