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

    # ------------------------------------------------------------------
    # Main SQL logic
    # ------------------------------------------------------------------
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

    # ==================================================================
    #                     BUTTON GETTER (REQUIRED FORMAT)
    # ==================================================================
    def get_run_correlation(self):
        """
        Getter for the 'Run Correlation' button.

        MUST return: (columns, rows)

        The GUI will set:
            self.table      -> the selected SQL table
            self.col_x      -> first numeric column
            self.col_y      -> second numeric column

        If something is missing or invalid → return error rows instead of crashing.
        """

        # ---- Validate GUI-injected attributes ----
        try:
            table = self.table
            col_x = self.col_x
            col_y = self.col_y
        except AttributeError:
            return ("Error",), [("Missing table or columns selection.",)]

        # ---- Execute correlation ----
        try:
            rows = self.correlation(table, col_x, col_y)
        except Exception:
            return ("Error",), [("Correlation failed.",)]

        # ---- Format results ----
        formatted = self.format_corr_for_treeview(rows)

        # Always one column called "Correlation"
        columns = ("Correlation",)

        return columns, formatted
