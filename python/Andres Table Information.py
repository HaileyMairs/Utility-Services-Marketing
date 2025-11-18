# ======================================================================
#                     TABLE INFORMATION UTILITY
# ======================================================================

#title: 'Table Info'
#btn: 'Tables with Info'
#btn: 'Tables without Info'

class TableInfoUtility:
    """
    Table Info utility rewritten to match teammate snake_case format
    and return (columns, rows) like her version.
    """

    def __init__(self, db):
        self.db = db

    # ---------------- INTERNAL ----------------
    def _get_all_tables(self):
        sql = """
        SELECT 
            s.name AS schema_name,
            t.name AS table_name,
            SUM(p.rows) AS row_count
        FROM sys.schemas s
        JOIN sys.tables t 
            ON t.schema_id = s.schema_id
        LEFT JOIN sys.partitions p 
            ON p.object_id = t.object_id
           AND p.index_id IN (0,1)
        GROUP BY s.name, t.name
        ORDER BY s.name, t.name;
        """
        try:
            return self.db.query(sql)
        except:
            return []

    # ---------------- PUBLIC ----------------
    def get_tables_with_info(self):
        all_rows = self._get_all_tables()
        rows = [r for r in all_rows if (r[2] or 0) > 0]
        columns = ("Schema", "Table", "Rows")
        return columns, rows

    def get_tables_without_info(self):
        all_rows = self._get_all_tables()
        rows = [r for r in all_rows if (r[2] or 0) == 0]
        columns = ("Schema", "Table", "Rows")
        return columns, rows

    def format_for_treeview(self, rows):
        formatted = []
        for schema_name, table_name, row_count in rows:
            formatted.append([
                schema_name,
                table_name,
                f"{row_count:,}" if row_count else "0"
            ])
        return formatted
