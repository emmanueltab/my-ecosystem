"""Server launcher for the ecosystem simulation.

This module starts a FastAPI application, creates and runs the simulation
loop as a background task, and broadcasts snapshots to connected Godot
clients over WebSockets.
"""

import random
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from simulation import Simulation
from creatures.r2.erf import erf
from creatures.r2.glooper import glooper  # Added Glooper import
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
from database import Database

# ── Configuration ─────────────────
RESUME = False
RESUME_ID = 1
TICK_RATE = 0.25
DB_SAVE_INTERVAL = 10

NUMBER_OF_ERFS = 50   # Split the creature count for variety
NUMBER_OF_GLOOPERS = 0 # Predators should usually have a lower starting pop
NUMBER_OF_FOOD = 20
NUMBER_OF_WATER = 20

# Predefined positions for food and water sources
positions_of_food = [(20, 20), (80, 20), (20, 80), (80, 80), (50, 50), (30, 70), (70, 30), (60, 60), (40, 40), (25, 75), (75, 25), (55, 55), (45, 45), (35, 65), (65, 35), (15, 85), (85, 15), (10, 90), (90, 10), (50, 30), (30, 50), (70, 70), (70, 50), (50, 70)]
positions_of_water = [(30, 30), (70, 30), (30, 70), (70, 70), (50, 20), (20, 50), (80, 50), (50, 80), (40, 60), (60, 40)]

# if there are more food sources than predefined positions, generate random positions
if NUMBER_OF_FOOD > len(positions_of_food):
    pos_needed = NUMBER_OF_FOOD - len(positions_of_food)
    for _ in range(pos_needed):
        positions_of_food.append((random.uniform(0, 100), random.uniform(0, 100)))
elif NUMBER_OF_FOOD < len(positions_of_food):
    positions_of_food = positions_of_food[:NUMBER_OF_FOOD]

# if there are more water sources than predefined positions, generate random positions
if NUMBER_OF_WATER > len(positions_of_water):
    pos_needed = NUMBER_OF_WATER - len(positions_of_water)
    for _ in range(pos_needed):
        positions_of_water.append((random.uniform(0, 100), random.uniform(0, 100)))
elif NUMBER_OF_WATER < len(positions_of_water):
    positions_of_water = positions_of_water[:NUMBER_OF_WATER]

sim: Simulation | None = None
connected_clients: list[WebSocket] = []

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
    """Initialize the simulation with both erfs and gloopers."""
    global sim
    db = Database()
    sim = Simulation(db=db)

    if RESUME:
        db.resume_run(RESUME_ID)
        sim.load_state(db, RESUME_ID)
    else:
        db.start_run(f"Run {RESUME_ID}", "Predator-Prey Baseline")

        # Spawn Erfs
        for _ in range(NUMBER_OF_ERFS):
            sim.add_creature(erf((random.uniform(0, 100), random.uniform(0, 100))))
        
        # Spawn Gloopers
        for _ in range(NUMBER_OF_GLOOPERS):
            sim.add_creature(glooper((random.uniform(0, 100), random.uniform(0, 100))))
        
        for pos in positions_of_food:
            sim.add_food(FoodSource(pos))

        for pos in positions_of_water:
            sim.add_water(WaterSource(pos, quantity=1500, replenish_rate=10))

    print("✅ Simulation Initialized with erfs and gloopers")

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