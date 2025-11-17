# ======================================================================
#                     ANOMALY DETECTION UTILITY
# ======================================================================

#title: 'Anomaly Detection'
#btn: 'Run Anomaly Detection'

class AnomalyDetectionUtility:

    def __init__(self, db):
        self.db = db

    def find_anomalies(self, table, column, z_threshold=3.0):
        sql = f"""
        WITH stats AS (
            SELECT AVG(CAST({column} AS FLOAT)) AS mean_val,
                   STDEV(CAST({column} AS FLOAT)) AS std_val
            FROM {table}
        ),
        z AS (
            SELECT *,
                   (CAST({column} AS FLOAT) - stats.mean_val) / NULLIF(stats.std_val, 0) AS zscore
            FROM {table}, stats
            WHERE {column} IS NOT NULL
        )
        SELECT *
        FROM z
        WHERE ABS(zscore) > {z_threshold}
        ORDER BY zscore DESC;
        """
        try:
            return self.db.query(sql)
        except:
            return []

    def format_anomalies(self, rows):
        return [[str(x) for x in r] for r in rows[:50]]
