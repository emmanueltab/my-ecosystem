"""Server launcher for the ecosystem simulation.

This module starts a FastAPI application, creates and runs the simulation
loop as a background task, and broadcasts snapshots to connected Godot
clients over WebSockets.
"""

import random
import json
import math
import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from simulation import Simulation
from creatures.r2.erf import erf
from creatures.r2.glooper import glooper
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
from database import Database

# ── Configuration ─────────────────
RESUME = False
RESUME_ID = 1  # This can stay for DB logic
RUN_CONFIG_NAME = "run one" # The key in your JSON
TICK_RATE = 0.25
DB_SAVE_INTERVAL = 10

sim: Simulation | None = None
connected_clients: list[WebSocket] = []

def load_config(config_name):
    """Loads a specific run configuration from the JSON file."""
    config_path = os.path.join(os.path.dirname(__file__), "runs_config.json")
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            return data.get(config_name)
    except FileNotFoundError:
        print("❌ Error: run_configs.json not found in server directory.")
        return None

def get_snapshot():
    """takes snapshot of the simulation and shrinks it into Dictionary."""
    if sim is None:
        return {}
    creatures = [
        {
            "id": c.id,
            "species": c.name, # Correctly uses "erf" or "Glooper"
            "sex": "F" if c.sex else "M",
            "age": c.age,
            "food": c.food_level,
            "water": c.water_level,
            "pos": [round(c.position[0], 2), round(c.position[1], 2)],
            "alive": c.alive
        }
        for c in sim.creatures.values()
    ]
    resources = (
        [{"id": f.id, "type": "food", "qty": f.quantity, "pos": list(f.position)} for f in sim.food_sources.values()] +
        [{"id": w.id, "type": "water", "qty": w.quantity, "pos": list(w.position)} for w in sim.water_sources.values()]
    )
    return {
        "tick": sim.tick_count,
        "population": len(sim.creatures),
        "creatures": creatures,
        "resources": resources
    }

async def broadcast_snapshot():
    """send snapshot to every Godot instance listening."""
    if not connected_clients:
        return
    data = json.dumps(get_snapshot()) 
    for client in connected_clients[:]:
        try:
            await client.send_text(data)
        except Exception:
            connected_clients.remove(client)

async def save_to_db(db: Database, tick_count: int):
    """Save the current simulation state to the database."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: _sync_save(db, tick_count))

def _sync_save(db: Database, tick_count: int):
    tick_id = db.save_tick(tick_count, len(sim.creatures))
    db.save_creature_states(tick_id, sim.creatures)
    db.save_resource_states(tick_id, sim.food_sources, sim.water_sources)

async def run_simulation():                 
    """Initialize the simulation using the JSON config."""
    global sim
    db = Database()
    sim = Simulation(db=db)

    # 1. Load the configuration
    config = load_config(RUN_CONFIG_NAME)
    if not config:
        print(f"❌ Could not load config: {RUN_CONFIG_NAME}. Stopping.")
        return

    if RESUME:
        db.resume_run(RESUME_ID)
        sim.load_state(db, RESUME_ID)
    else:
        # Use the name from JSON for the DB run name
        db.start_run(RUN_CONFIG_NAME, "Configured JSON Run")

        # 2. Extract values from config
        num_erfs = config.get("num_erfs", 0)
        num_gloopers = config.get("num_gloopers", 0)
        num_food = config.get("num_food", 0)
        num_water = config.get("num_water", 0)
        raw_food_pos = config.get("food_positions", [])
        raw_water_pos = config.get("water_positions", [])

        # 3. Use your static method to align counts and fix overlaps
        final_food, final_water = Simulation.setup_resources(
            num_food, num_water, raw_food_pos, raw_water_pos
        )

        # 4. Spawn Resources
        for pos in final_food:
            sim.add_food(FoodSource(pos))

        for pos in final_water:
            sim.add_water(WaterSource(pos, quantity=1500, replenish_rate=10))

        # 5. Spawn Creatures
        for _ in range(num_erfs):
            sim.add_creature(erf((random.uniform(0, 100), random.uniform(0, 100))))
        
        for _ in range(num_gloopers):
            sim.add_creature(glooper((random.uniform(0, 100), random.uniform(0, 100))))

    print(f"✅ Simulation Initialized: {RUN_CONFIG_NAME}")
    print(f"Stats: {len(sim.creatures)} Creatures, {num_food} Food, {num_water} Water")

    while True:
        sim.tick()
        await broadcast_snapshot()

        if sim.tick_count % DB_SAVE_INTERVAL == 0:
            asyncio.create_task(save_to_db(db, sim.tick_count))

        await asyncio.sleep(TICK_RATE)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop simulation task."""
    sim_task = asyncio.create_task(run_simulation())
    yield
    sim_task.cancel()

app = FastAPI(lifespan=lifespan) 

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in connected_clients:
            connected_clients.remove(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)