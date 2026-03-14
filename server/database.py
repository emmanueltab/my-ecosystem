import sqlite3
import os
from datetime import datetime

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "ecosystem.db")

class Database:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path        = db_path
        self.connection     = sqlite3.connect(db_path)
        self.cursor         = self.connection.cursor()
        self.current_run_id = None
        self.create_tables()
        print(f"Database connected: {db_path}")

    def create_tables(self):
        """Creates all tables if they don't already exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT,
                started_at TEXT,
                ended_at   TEXT,
                notes      TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      INTEGER,
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
                food_level      REAL,
                water_level      REAL,
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

    def start_run(self, name, notes=""):
        """Creates a new run and returns its id."""
        started_at = datetime.now().isoformat()
        self.cursor.execute('''
            INSERT INTO runs (name, started_at, notes)
            VALUES (?, ?, ?)
        ''', (name, started_at, notes))
        self.connection.commit()
        self.current_run_id = self.cursor.lastrowid
        print(f"Run started: {name} (id: {self.current_run_id})")
        return self.current_run_id

    def end_run(self):
        """Marks the current run as ended."""
        ended_at = datetime.now().isoformat()
        self.cursor.execute('''
            UPDATE runs SET ended_at = ? WHERE id = ?
        ''', (ended_at, self.current_run_id))
        self.connection.commit()
        print(f"Run ended: id {self.current_run_id}")

    def save_tick(self, tick_number, population):
        """Saves a tick record and returns the tick id."""
        timestamp = datetime.now().isoformat()
        self.cursor.execute('''
            INSERT INTO ticks (run_id, tick_number, timestamp, population)
            VALUES (?, ?, ?, ?)
        ''', (self.current_run_id, tick_number, timestamp, population))
        self.connection.commit()
        return self.cursor.lastrowid

    def save_creature_states(self, tick_id, creatures):
        """Saves the state of all creatures for a given tick."""
        for creature in creatures.values():
            sex_label = "F" if creature.sex else "M"
            self.cursor.execute('''
                INSERT INTO creature_states
                (tick_id, creature_id, species, sex, age, food_level, water_level, pos_x, pos_y, alive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tick_id,
                creature.id,
                creature.name,
                sex_label,
                creature.age,
                creature.food_level,
                creature.water_level,
                creature.position[0],
                creature.position[1],
                1 if creature.alive else 0
            ))
        self.connection.commit()

    def save_resource_states(self, tick_id, food_sources, water_sources):
        """Saves the state of all resources for a given tick."""
        all_resources = list(food_sources.values()) + list(water_sources.values())
        for resource in all_resources:
            self.cursor.execute('''
                INSERT INTO resource_states
                (tick_id, resource_id, resource_type, quantity, pos_x, pos_y)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                tick_id,
                resource.id,
                resource.get_type(),
                resource.quantity,
                resource.position[0],
                resource.position[1]
            ))
        self.connection.commit()

    def resume_run(self, run_id):
        """Resumes an existing run."""
        self.current_run_id = run_id
        print(f"Resuming run id: {run_id}")

    def get_last_tick(self, run_id):
        """Returns the last tick id and number for a run."""
        self.cursor.execute('''
            SELECT id, tick_number FROM ticks
            WHERE run_id = ?
            ORDER BY tick_number DESC
            LIMIT 1
        ''', (run_id,))
        return self.cursor.fetchone()

    def get_creature_states(self, tick_id):
        """Returns all alive creature states for a given tick."""
        self.cursor.execute('''
            SELECT creature_id, species, sex, age,
                   food_level, water_level, pos_x, pos_y
            FROM creature_states
            WHERE tick_id = ? AND alive = 1
        ''', (tick_id,))
        return self.cursor.fetchall()

    def get_resource_states(self, tick_id):
        """Returns all resource states for a given tick."""
        self.cursor.execute('''
            SELECT resource_id, resource_type,
                   quantity, pos_x, pos_y
            FROM resource_states
            WHERE tick_id = ?
        ''', (tick_id,))
        return self.cursor.fetchall()

    def close(self):
        """Closes the database connection."""
        self.connection.close()