import MySQLdb
from os import environ
from dotenv import load_dotenv

load_dotenv(".env")

MYSQL_DEFAULT_SETTINGS = {
    "host": environ.get("DB_HOST"),
    # "host": "localhost",
    "user": environ.get("DB_USER"),
    "passwd": environ.get("DB_PASSWD"),
    "db": environ.get("DB_NAME"),
    "charset": "utf8"
}


class MySQL:
    def __init__(self, **settings):
        self.settings = MYSQL_DEFAULT_SETTINGS.copy()

        for kw in settings:
            self.settings[kw] = settings[kw]

    def __enter__(self):
        self.conn = MySQLdb.connect(**self.settings)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()

        # Autocommit
        # self.conn.commit()

        self.conn.close()

