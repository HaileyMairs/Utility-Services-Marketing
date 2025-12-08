# ======================================================================
#                     ANOMALY DETECTION UTILITY
# ======================================================================

#title: 'Anomaly Detection'
#btn: 'Run Anomaly Detection'

class AnomalyDetectionUtility:

    def __init__(self, db):
        self.db = db

    # ------------------------------------------------------------------
    # Main SQL logic 
    # ------------------------------------------------------------------
    def find_anomalies(self, table, column, z_threshold=3.0):
        # Clean inputs so SQL Server doesn't freak out
        table = table.strip().strip("[]")
        column = column.strip().strip("[]")

        sql = f"""
        WITH stats AS (
            SELECT AVG(CAST({column} AS FLOAT)) AS mean_val,
                   STDEV(CAST({column} AS FLOAT)) AS std_val
            FROM [{table}]
        ),
        z AS (
            SELECT *,
                   (CAST({column} AS FLOAT) - stats.mean_val) / NULLIF(stats.std_val, 0) AS zscore
            FROM [{table}], stats
            WHERE {column} IS NOT NULL
        )
        SELECT *
        FROM z
        WHERE ABS(zscore) > {z_threshold}
        ORDER BY zscore DESC;
        """
        try:
            return self.db.query(sql)
        except Exception as e:
            # Return error text to GUI instead of failing silently
            return [["QUERY ERROR", str(e)]]

    # ------------------------------------------------------------------
    def format_anomalies(self, rows):
        # rows may be an error structure OR normal data
        formatted = [[str(x) for x in r] for r in rows[:50]]
        return formatted

    # ==================================================================
    #                     BUTTON GETTER (REQUIRED FORMAT)
    # ==================================================================
    def get_run_anomaly_detection(self):
        """
        Getter for the 'Run Anomaly Detection' button.
        Must return (columns, rows).
        """

        # ---- Check GUI input first ----
        missing_inputs = []
        for attr in ["table", "column", "z_threshold"]:
            if not hasattr(self, attr):
                missing_inputs.append(attr)

        if missing_inputs:
            return ("Error",), [(f"Missing required input(s): {', '.join(missing_inputs)}",)]

        # ---- Extract + sanitize ----
        table = str(self.table).strip()
        column = str(self.column).strip()

        # ---- Handle Z-score threshold errors ----
        try:
            z = float(self.z_threshold)
        except:
            return ("Error",), [("Z-threshold must be numeric.",)]

        # ---- Run detection ----
        rows = self.find_anomalies(table, column, z_threshold=z)

        # If the query returned an error list (2-column "QUERY ERROR")
        if isinstance(rows, list) and len(rows) == 1 and "QUERY ERROR" in rows[0][0]:
            return ("Error", "Detail"), rows

        # If no anomalies detected
        if not rows:
            return ("Message",), [("No anomalies found or table is empty.",)]

        formatted = self.format_anomalies(rows)

        # Dynamically build column headers
        col_count = len(formatted[0])
        columns = tuple(f"Col {i+1}" for i in range(col_count))

        return columns, formatted
