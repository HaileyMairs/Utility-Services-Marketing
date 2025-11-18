# ======================================================================
#                     STATISTICAL SUMMARY UTILITY
# ======================================================================

#title: 'Statistical Summary'
#btn: 'Run Summary'

class StatisticalSummaryUtility:

    def __init__(self, db):
        self.db = db

    def summarize(self, table_name, column_name):
        sql = f"""
        SELECT
            COUNT({column_name}),
            AVG(CAST({column_name} AS FLOAT)),
            MIN(CAST({column_name} AS FLOAT)),
            MAX(CAST({column_name} AS FLOAT)),
            STDEV(CAST({column_name} AS FLOAT)),
            VAR(CAST({column_name} AS FLOAT))
        FROM {table_name};
        """
        try:
            return self.db.query(sql)
        except:
            return []

    def format_stats_for_treeview(self, rows):
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
