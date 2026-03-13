import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="/data/ecosystem.db"):
        # create data/ folder if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path    = db_path
        self.connection = sqlite3.connect(db_path)
        self.cursor     = self.connection.cursor()
        self.create_tables()
        print(f"Database connected: {db_path}")

    def create_tables(self):
        """Creates all tables if they don't already exist."""

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tick_number INTEGER,
                timestamp   TEXT,
                population  INTEGER
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS creature_states (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tick_id     INTEGER,
                creature_id TEXT,
                species     TEXT,
                sex         TEXT,
                age         INTEGER,
                hunger      REAL,
                thirst      REAL,
                pos_x       REAL,
                pos_y       REAL,
                alive       INTEGER
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_states (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                tick_id       INTEGER,
                resource_id   TEXT,
                resource_type TEXT,
                quantity      REAL,
                pos_x         REAL,
                pos_y         REAL
            )
        ''')

        self.connection.commit()
        print("Tables created successfully.")

    def close(self):
        """Closes the database connection."""
        self.connection.close()