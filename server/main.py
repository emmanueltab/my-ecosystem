"""
Interactive Shell for the Ecosystem Simulation.
Displays the Erf splash screen and handles create/resume/delete commands.
"""

import random
import json
import asyncio
import os
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from simulation import Simulation
from creatures.r2.erf import erf
from creatures.r2.glooper import glooper
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
from database import Database

# ── Global State (Controlled by the Menu) ──
RESUME = False
RUN_CONFIG_NAME = "" 
TICK_RATE = 0.25
DB_SAVE_INTERVAL = 10

sim: Simulation | None = None
connected_clients: list[WebSocket] = []

def print_splash(run_name="READY"):
    """The Erf Splash Screen."""
    THEME = ["\033[38;5;46m", "\033[38;5;40m", "\033[38;5;34m", "\033[38;5;28m", "\033[38;5;22m"]
    RESET = "\033[0m"
    erf_ascii = [
        "                          ############       ",
        "                          ##        ##       ",
        "      ############        ##        ##       ",
        "      ##        ##        ##        ##       ",
        "      ##  ####  ##        ##  ####  ##       ",
        "      ##  ####  ##        ##  ####  ##       ",
        "      ##  ####  ##        ##  ####  ##       ",
        "  ######        ############        ######   ",
        "  ##  ############        ##        ##  ##   ",
        "  ##                      ############  ##   ",
        "  ##                                    ##   ",
        "  ########################################   ",
        "            ##  ##        ##  ##             ",
        "            ##  ##        ##  ##             ",
        "            ######        ######             "
    ]
    for i, line in enumerate(erf_ascii):
        print(f"{THEME[i % len(THEME)]}{line}{RESET}")
    print(f"\n{THEME[0]}>> SYSTEM ONLINE{RESET} | {THEME[1]}TARGET: '{run_name}'{RESET} | {THEME[2]}PREY: ERF{RESET}\n")

def load_config(config_name):
    config_path = os.path.join(os.path.dirname(__file__), "runs_config.json")
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            return data.get(config_name)
    except FileNotFoundError:
        return None

# ── Simulation & Network Logic ─────────────────

def get_snapshot():
    if sim is None: return {}
    creatures = [{
        "id": c.id, "species": c.name, "sex": "F" if c.sex else "M",
        "age": c.age, "food": c.food_level, "water": c.water_level,
        "pos": [round(c.position[0], 2), round(c.position[1], 2)], "alive": c.alive
    } for c in sim.creatures.values()]
    
    resources = (
        [{"id": f.id, "type": "food", "qty": f.quantity, "pos": list(f.position)} for f in sim.food_sources.values()] +
        [{"id": w.id, "type": "water", "qty": w.quantity, "pos": list(w.position)} for w in sim.water_sources.values()]
    )
    return {"tick": sim.tick_count, "population": len(sim.creatures), "creatures": creatures, "resources": resources}

async def broadcast_snapshot():
    if not connected_clients: return
    data = json.dumps(get_snapshot()) 
    for client in connected_clients[:]:
        try:
            await client.send_text(data)
        except:
            connected_clients.remove(client)

async def run_simulation():                 
    global sim
    db = Database()
    sim = Simulation(db=db)

    config = load_config(RUN_CONFIG_NAME)
    if not config and not RESUME:
        print(f"Configuration '{RUN_CONFIG_NAME}' not found in JSON.")
        return

    if RESUME:
        # Resolve Name to ID
        db.cursor.execute('SELECT id FROM runs WHERE name = ?', (RUN_CONFIG_NAME,))
        row = db.cursor.fetchone()
        if row:
            actual_id = row['id']
            db.resume_run(actual_id)
            sim.load_state(db, actual_id)
        else:
            print(f"Cannot resume: '{RUN_CONFIG_NAME}' not found in Database.")
            return
    else:
        db.start_run(RUN_CONFIG_NAME, "New Simulation")
        # Spawn from config
        f_pos, w_pos = Simulation.setup_resources(
            config.get("num_food", 0), config.get("num_water", 0), 
            config.get("food_positions", []), config.get("water_positions", [])
        )
        for pos in f_pos: sim.add_food(FoodSource(pos))
        for pos in w_pos: sim.add_water(WaterSource(pos, quantity=1500, replenish_rate=10))
        for _ in range(config.get("num_erfs", 0)):
            sim.add_creature(erf((random.uniform(0, 100), random.uniform(0, 100))))
        for _ in range(config.get("num_gloopers", 0)):
            sim.add_creature(glooper((random.uniform(0, 100), random.uniform(0, 100))))

    while True:
        sim.tick()
        await broadcast_snapshot()
        if sim.tick_count % DB_SAVE_INTERVAL == 0:
            # Sync save in background
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: db.save_tick(sim.tick_count, len(sim.creatures)))
            # Note: You'd call your save_creature_states etc. here too
        await asyncio.sleep(TICK_RATE)

# ── FastAPI Setup ─────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    sim_task = asyncio.create_task(run_simulation())
    yield
    sim_task.cancel()

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        if ws in connected_clients: connected_clients.remove(ws)

# ── THE INTERACTIVE MENU ───────────────────────

import shlex  # Add this to your imports at the top!

if __name__ == "__main__":
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_splash("READY")
        
        print("Commands: create [name] | resume [name] | delete [name] | exit")
        raw_input = input(">> ").strip()
        
        if not raw_input: continue
        
        # shlex.split handles quotes correctly: "run one" becomes one item
        choice = shlex.split(raw_input)
        cmd = choice[0].lower()
        
        if cmd == "exit": break

        if len(choice) < 2:
            print("Error: Missing run name. (e.g. create \"run one\")")
            input("Press Enter to continue...")
            continue

        RUN_CONFIG_NAME = choice[1]

        if cmd == "delete":
            db = Database()
            db.delete_run(RUN_CONFIG_NAME)
            input("\nPress Enter to return to menu...")
        
        elif cmd in ["create", "resume"]:
            RESUME = (cmd == "resume")
            print(f"[*] Starting Server for '{RUN_CONFIG_NAME}'...")
            try:
                uvicorn.run(app, host="0.0.0.0", port=8000)
            except KeyboardInterrupt:
                print("\n[!] Simulation Stopped. Returning to menu...")
                input("Press Enter...")
        else:
            print(f"Unknown command: {cmd}")
            input("Press Enter...")