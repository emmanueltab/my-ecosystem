import sqlite3
import os
from datetime import datetime

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "ecosystem.db")

class Database:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        self.db_path = db_path
        # Added timeout=30 to handle busy database files without crashing
        self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

        # --- WAL MODE & PERFORMANCE SETTINGS ---
        # 1. WAL mode allows concurrent reads and writes (Grafana + Simulation)
        self.cursor.execute("PRAGMA journal_mode=WAL;")
        # 2. NORMAL synchronous is faster and perfectly safe for WAL mode
        self.cursor.execute("PRAGMA synchronous=NORMAL;")
        # 3. Cache size increase (optional, uses ~20MB RAM to speed up queries)
        self.cursor.execute("PRAGMA cache_size=-20000;")
        
        self.current_run_id = None
        self.create_tables()
        print(f"Database connected: {db_path} (WAL Mode Enabled)")

    def create_tables(self):
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, started_at TEXT, ended_at TEXT, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER, tick_number INTEGER, timestamp TEXT, population INTEGER
            );
            CREATE TABLE IF NOT EXISTS creature_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick_id INTEGER, creature_id TEXT, species TEXT, sex TEXT,
                age INTEGER, food_level REAL, water_level REAL,
                pos_x REAL, pos_y REAL, alive INTEGER
            );
            CREATE TABLE IF NOT EXISTS resource_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick_id INTEGER, resource_id TEXT, resource_type TEXT,
                quantity REAL, pos_x REAL, pos_y REAL
            );
        ''')
        self.connection.commit()

    def resume_run(self, run_id):
        """Sets the current run context to an existing ID."""
        self.current_run_id = run_id
        print(f"📂 Resuming run id: {run_id}")

    def get_last_tick(self, run_id):
        """Returns the most recent tick for a specific run."""
        self.cursor.execute('''
            SELECT id, tick_number FROM ticks 
            WHERE run_id = ? 
            ORDER BY tick_number DESC LIMIT 1
        ''', (run_id,))
        return self.cursor.fetchone()

    def get_creature_states(self, tick_id):
        """Returns all creature states for a tick as a list of dictionaries."""
        self.cursor.execute('''
            SELECT * FROM creature_states WHERE tick_id = ?
        ''', (tick_id,))
        # Converting to standard dicts ensures compatibility with your Simulation logic
        return [dict(row) for row in self.cursor.fetchall()]

    def get_resource_states(self, tick_id):
        """Returns all resource states for a tick as a list of dictionaries."""
        self.cursor.execute('''
            SELECT * FROM resource_states WHERE tick_id = ?
        ''', (tick_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    # --- Keep your existing start_run, save_tick, save_creature_states, etc. ---
    
    def start_run(self, name, notes=""):
        started_at = datetime.now().isoformat()
        self.cursor.execute('INSERT INTO runs (name, started_at, notes) VALUES (?, ?, ?)', (name, started_at, notes))
        self.connection.commit()
        self.current_run_id = self.cursor.lastrowid
        return self.current_run_id

    def save_tick(self, tick_number, population):
        timestamp = datetime.now().isoformat()
        self.cursor.execute('INSERT INTO ticks (run_id, tick_number, timestamp, population) VALUES (?, ?, ?, ?)', 
                            (self.current_run_id, tick_number, timestamp, population))
        self.connection.commit()
        return self.cursor.lastrowid

    def save_creature_states(self, tick_id, creatures):
        data = [(tick_id, c.id, c.name, "F" if c.sex else "M", c.age, c.food_level, c.water_level, c.position[0], c.position[1], 1 if c.alive else 0) 
                for c in creatures.values()]
        self.cursor.executemany('INSERT INTO creature_states (tick_id, creature_id, species, sex, age, food_level, water_level, pos_x, pos_y, alive) VALUES (?,?,?,?,?,?,?,?,?,?)', data)
        self.connection.commit()

    def save_resource_states(self, tick_id, food, water):
        data = [(tick_id, r.id, r.get_type(), r.quantity, r.position[0], r.position[1]) 
                for r in list(food.values()) + list(water.values())]
        self.cursor.executemany('INSERT INTO resource_states (tick_id, resource_id, resource_type, quantity, pos_x, pos_y) VALUES (?,?,?,?,?,?)', data)
        self.connection.commit()

    def delete_run(self, run_name):
        """Deletes a simulation run and all associated data using the run name."""
        # 1. Find the internal ID based on the name provided in CLI
        self.cursor.execute('SELECT id FROM runs WHERE name = ?', (run_name,))
        result = self.cursor.fetchone()
        
        if not result:
            print(f"Run name '{run_name}' does not exist in the database.")
            return False
        
        run_id = result[0]
        
        # 2. Get all tick_ids for this run
        self.cursor.execute('SELECT id FROM ticks WHERE run_id = ?', (run_id,))
        tick_ids = [row[0] for row in self.cursor.fetchall()]
        
        # 3. Delete creature_states and resource_states for these ticks
        if tick_ids:
            placeholders = ','.join('?' for _ in tick_ids)
            # We use f-strings here only for the placeholders count; the data is still parameterized
            self.cursor.execute(f'DELETE FROM creature_states WHERE tick_id IN ({placeholders})', tick_ids)
            self.cursor.execute(f'DELETE FROM resource_states WHERE tick_id IN ({placeholders})', tick_ids)
        
        # 4. Delete ticks
        self.cursor.execute('DELETE FROM ticks WHERE run_id = ?', (run_id,))
        
        # 5. Delete the run itself
        self.cursor.execute('DELETE FROM runs WHERE id = ?', (run_id,))
        
        self.connection.commit()
        print(f"Successfully wiped all data for run: '{run_name}' (ID: {run_id})")
        return True