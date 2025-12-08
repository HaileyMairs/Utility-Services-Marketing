''' ======================================================================
                         DATA FRESHNESS UTILITY
 ======================================================================'''

#title: 'Data Freshness'
#btn: 'Latest Values by Location'
#btn: 'Stale Variables'

"""
NOTE FOR TEAM — OPSTSBP REAL TABLES
-----------------------------------
This utility is built ONLY on tables we KNOW exist in the OPSTSBP
database export:

    • DATADDF.csv   -> table: dbo.DATADDF
    • LOCATION.csv  -> table: dbo.LOCATION

From the DATADDF CSV, each row looks like:

    0: location_code   (e.g. 'NARANJODL', 'seymourrd')
    1: edit_time       (datetime)
    2: sample_time     (datetime)  <-- date/time of measurement
    3: variable_id     (int)
    4: value           (numeric)
    5: stored_value    (numeric, rounded or scaled)
    6: flag1           (int)
    7: flag2           (int)

From LOCATION CSV, rows look like:

    0: location_code   (same as DATADDF col 0)
    1: last_edit_time
    2: location_id
    3: group_name      (e.g. 'WWTP Water Quality', 'Environmental')
    4: description     (text)

The EXACT column names in SQL Server may differ, but the TABLE NAMES
(dbo.DATADDF and dbo.LOCATION) are real. Update the mappings in __init__
to match what you see in Azure Data Studio.

What this utility provides:

    get_latest_values_by_location(days_back=365)
        -> For each (location, variable), shows the most recent sample,
           last value, and days since last sample.

    get_stale_variables(days_stale=30)
        -> Filters the above to only variables whose last sample is older
           than N days (e.g., missing data / sampling gaps).

Both are directly useful to answer:
    • "Which parameters are we actively sampling?"
    • "Which variables at which locations haven't been updated recently?"
"""


class DataFreshnessUtility:
    """
    Provides:
        get_latest_values_by_location()
        get_stale_variables()

    Uses:
        self.db.query(sql) -> list of tuples

    You MUST set the correct column names in __init__ based on the
    dbo.DATADDF and dbo.LOCATION schema in SQL Server.
    """

    def __init__(self, db):
        self.db = db

        # ---------------- TABLE & COLUMN MAPPINGS ----------------
        # OPSTSBP CSV mappings (dbo.DATADDF.csv / dbo.LOCATION.csv)
        self.data_table        = "dbo.DATADDF"
        self.col_loc_code      = "VARID"           # using VARID as identifier (no explicit location code in CSV)
        self.col_sample_time   = "DATESTAMP"
        self.col_var_id        = "VARID"
        self.col_value         = "CURVALUE"

        # LOCATION.csv has many fields; keep join optional
        self.loc_table         = None              # set to "dbo.LOCATION" if a usable key appears
        self.loc_col_code      = "LOCATION"
        self.loc_col_group     = "DESCRIPTION"

    # ------------------------------------------------------------------
    # 1) Latest Values by Location
    # ------------------------------------------------------------------
    def query_latest_values_by_location(self, days_back=365):
        sql = f"""
        WITH Recent AS (
            SELECT
                d.{self.col_loc_code}    AS location_code,
                d.{self.col_var_id}      AS variable_id,
                d.{self.col_sample_time} AS sample_time,
                d.{self.col_value}       AS value
            FROM {self.data_table} AS d
            WHERE d.{self.col_sample_time} >= DATEADD(DAY, -{days_back}, GETDATE())
        ),
        Latest AS (
            SELECT
                r.location_code,
                r.variable_id,
                MAX(r.sample_time) AS last_sample_time
            FROM Recent AS r
            GROUP BY r.location_code, r.variable_id
        )
        SELECT
            L.location_code,
            '' AS location_group,
            L.variable_id,
            L.last_sample_time,
            d.value AS last_value,
            DATEDIFF(DAY, L.last_sample_time, GETDATE()) AS days_since_last_sample
        FROM Latest AS L
        LEFT JOIN {self.data_table} AS d
            ON d.{self.col_loc_code}    = L.location_code
           AND d.{self.col_var_id}      = L.variable_id
           AND d.{self.col_sample_time} = L.last_sample_time
        ORDER BY L.location_code, L.variable_id;
        """
        try:
            return self.db.query(sql)
        except Exception:
            return []

    # ------------------------------------------------------------------
    # 2) Stale Variables
    # ------------------------------------------------------------------
    def query_stale_variables(self, days_stale=30, days_lookback=365):
        sql = f"""
        WITH Recent AS (
            SELECT
                d.{self.col_loc_code}    AS location_code,
                d.{self.col_var_id}      AS variable_id,
                d.{self.col_sample_time} AS sample_time,
                d.{self.col_value}       AS value
            FROM {self.data_table} AS d
            WHERE d.{self.col_sample_time} >= DATEADD(DAY, -{days_lookback}, GETDATE())
        ),
        Latest AS (
            SELECT
                r.location_code,
                r.variable_id,
                MAX(r.sample_time) AS last_sample_time
            FROM Recent AS r
            GROUP BY r.location_code, r.variable_id
        )
        SELECT
            L.location_code,
            '' AS location_group,
            L.variable_id,
            L.last_sample_time,
            d.value AS last_value,
            DATEDIFF(DAY, L.last_sample_time, GETDATE()) AS days_since_last_sample
        FROM Latest AS L
        LEFT JOIN {self.data_table} AS d
            ON d.{self.col_loc_code}    = L.location_code
           AND d.{self.col_var_id}      = L.variable_id
           AND d.{self.col_sample_time} = L.last_sample_time
        WHERE DATEDIFF(DAY, L.last_sample_time, GETDATE()) >= {days_stale}
        ORDER BY days_since_last_sample DESC, L.location_code, L.variable_id;
        """
        try:
            return self.db.query(sql)
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Formatting helpers for GUI treeviews
    # ------------------------------------------------------------------
    def format_latest_for_treeview(self, rows):
        """
        Expects rows from get_latest_values_by_location():
            (location_code, location_group, variable_id,
             last_sample_time, last_value, days_since)
        """
        formatted = []
        for r in rows:
            loc_code, loc_group, var_id, last_time, last_val, days_since = r
            formatted.append([
                str(loc_code),
                loc_group or "",
                str(var_id),
                str(last_time),
                f"{last_val:.3f}" if last_val is not None else "",
                str(days_since if days_since is not None else ""),
            ])
        return formatted

    def format_stale_for_treeview(self, rows):
        """
        Expects rows from get_stale_variables().
        """
        formatted = []
        for r in rows:
            loc_code, loc_group, var_id, last_time, last_val, days_since = r
            formatted.append([
                str(loc_code),
                loc_group or "",
                str(var_id),
                str(last_time),
                f"{last_val:.3f}" if last_val is not None else "",
                str(days_since if days_since is not None else ""),
            ])
        return formatted

    # ------------------------------------------------------------------
    # GUI button handlers (must return (columns, rows))
    # ------------------------------------------------------------------
    def get_latest_values_by_location(self):
        raw = self.query_latest_values_by_location()
        columns = (
            "Location Code",
            "Location Group",
            "Variable ID",
            "Last Sample Time",
            "Last Value",
            "Days Since Last Sample",
        )
        return columns, self.format_latest_for_treeview(raw)

    def get_stale_variables(self):
        raw = self.query_stale_variables()
        columns = (
            "Location Code",
            "Location Group",
            "Variable ID",
            "Last Sample Time",
            "Last Value",
            "Days Since Last Sample",
        )
        return columns, self.format_stale_for_treeview(raw)
