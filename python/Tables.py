#title: 'Table Info'
#btn: 'Tables with Info'
#btn: 'Tables without Info'

from local_sql_loader import LocalSqlDatabase


class TableUtility:
    def __init__(self, db: LocalSqlDatabase | None = None):
        self.db = db or LocalSqlDatabase()

    # ---------------- TABLES ----------------
    def get_all_tables(self):
        sql = """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name LIKE 'dbo.%'
        ORDER BY name;
        """
        tables = self.db.query(sql)
        results = []
        for (name,) in tables:
            schema, table = name.split(".", 1)
            count_sql = f"SELECT COUNT(*) FROM {name}"
            row_count = self.db.scalar(count_sql) or 0
            results.append((schema, table, row_count))
        return results

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
