#title: 'Table Info'
#btn: 'Tables with Info'
#btn: 'Tables without Info'

import pyodbc

SQL_SERVER = "HAILEY"
DATABASE = "MCRWS-Telog"

class TableUtility:
    def __init__(self):
        self.conn = self.connect_db()

    def connect_db(self):
        """Connect to SQL Server using ODBC."""
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE};Trusted_Connection=yes;"
        try:
            return pyodbc.connect(conn_str, autocommit=True, timeout=5)
        except pyodbc.Error:
            # fallback to ODBC Driver 18
            conn_str = conn_str.replace("ODBC Driver 17", "ODBC Driver 18")
            return pyodbc.connect(conn_str, autocommit=True, timeout=5)

    def query(self, sql, params=None):
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchall()

    # ---------------- TABLES ----------------
    def get_all_tables(self):
        sql = """
        SELECT s.name, t.name, SUM(p.rows)
        FROM sys.schemas s
        JOIN sys.tables t ON t.schema_id = s.schema_id
        LEFT JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1)
        GROUP BY s.name, t.name
        ORDER BY s.name, t.name;
        """
        return self.query(sql)

    def get_tables_with_info(self):
        rows = [r for r in self.get_all_tables() if (r[2] or 0) > 0]
        columns = ("Schema", "Table", "Rows")
        return columns, rows

    def get_tables_without_info(self):
        rows = [r for r in self.get_all_tables() if (r[2] or 0) == 0]
        columns = ("Schema", "Table", "Rows")
        return columns, rows

# Optional standalone test
if __name__ == "__main__":
    tables = TableUtility()
    for btn in ["get_tables_with_info", "get_tables_without_info"]:
        cols, rows = getattr(tables, btn)()
        print(f"\n{btn.upper()}:")
        print(cols)
        for r in rows:
            print(r)
