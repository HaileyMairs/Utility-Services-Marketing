# ======================================================================
#                     STATISTICAL SUMMARY UTILITY
# ======================================================================

#title: 'Statistical Summary'
#btn: 'Run Summary'

class StatisticalSummaryUtility:

    def __init__(self, db):
        self.db = db

    # ------------------------------------------------------------------
    # Core SQL Summary Function
    # ------------------------------------------------------------------
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
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Formatting Helper
    # ------------------------------------------------------------------
    def format_stats_for_treeview(self, rows):
        if not rows:
            return []

        count_v, avg_v, min_v, max_v, std_v, var_v = rows[0]

        return [[
            f"{count_v:,}",
            f"{avg_v:.3f}" if avg_v else "0.000",
            f"{min_v:.3f}" if min_v else "0.000",
            f"{max_v:.3f}" if max_v else "0.000",
            f"{std_v:.3f}" if std_v else "0.000",
            f"{var_v:.3f}" if var_v else "0.000",
        ]]

    # ==================================================================
    #                     BUTTON GETTER (REQUIRED)
    # ==================================================================
    def get_run_summary(self):
        """
        Getter for the 'Run Summary' button.
        Must return (columns, rows).

        IMPORTANT:
        The GUI will handle selecting the table + column.
        This getter only wraps the summarize() function.
        """

        # In the real GUI, these are passed from dropdowns.
        # Here we safely detect missing inputs.
        try:
            table = self.current_table      # expected GUI injection
            column = self.current_column    # expected GUI injection
        except AttributeError:
            columns = ("Error",)
            rows = [("No table/column selected. GUI must set current_table/current_column.",)]
            return columns, rows

        try:
            raw = self.summarize(table, column)
            formatted = self.format_stats_for_treeview(raw)
        except Exception as e:
            columns = ("Error",)
            return columns, [(str(e),)]

        columns = ("Count", "Average", "Minimum", "Maximum", "StdDev", "Variance")
        return columns, formatted
