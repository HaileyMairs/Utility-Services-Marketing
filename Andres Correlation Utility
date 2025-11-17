# ======================================================================
#                     CORRELATION UTILITY
# ======================================================================

#title: 'Correlation Analysis'
#btn: 'Run Correlation'

class CorrelationUtility:
    """
    Computes Pearson correlation between two numeric columns.
    """

    def __init__(self, db):
        self.db = db

    def correlation(self, table, col_x, col_y):
        sql = f"""
        SELECT
            (SUM(({col_x} - (SELECT AVG({col_x}) FROM {table}))
                 * ({col_y} - (SELECT AVG({col_y}) FROM {table})))
            /
            (SQRT(SUM(POWER({col_x} - (SELECT AVG({col_x}) FROM {table}), 2)))
             * SQRT(SUM(POWER({col_y} - (SELECT AVG({col_y}) FROM {table}), 2))))
        FROM {table}
        WHERE {col_x} IS NOT NULL AND {col_y} IS NOT NULL;
        """
        try:
            return self.db.query(sql)
        except:
            return []

    def format_corr_for_treeview(self, rows):
        if not rows:
            return [["N/A"]]
        value = rows[0][0]
        return [["N/A"]] if value is None else [[f"{value:.4f}"]]
