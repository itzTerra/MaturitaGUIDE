import sqlite3


class SQLite:
    def __init__(self, file="sqlitedb.db"):
        self.file = file

    def __enter__(self):
        self.conn = sqlite3.connect(self.file)
        # self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, type, value, traceback):
        self.cursor.close()
        # self.conn.commit()
        self.conn.close()
