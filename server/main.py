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
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
from database import Database

# ── Configuration ─────────────────
RESUME = False
RESUME_ID = 4
TICK_RATE = 0.25
DB_SAVE_INTERVAL = 10

NUMBER_OF_CREATURES = 100
NUMBER_OF_FOOD = 50
NUMBER_OF_WATER = 50

# Predefined positions for food and water sources to ensure they are not randomly placed every time, which can help with testing and consistency. If you want them to be random, you can remove these lists and generate random positions in the loop.
positions_of_food = [(20, 20), (80, 20), (20, 80), (80, 80), (50, 50), (30, 70), (70, 30), (60, 60), (40, 40), (25, 75), (75, 25), (55, 55), (45, 45), (35, 65), (65, 35), (15, 85), (85, 15), (10, 90), (90, 10), (50, 30), (30, 50), (70, 70), (70, 50), (50, 70)]
positions_of_water = [(30, 30), (70, 30), (30, 70), (70, 70), (50, 20), (20, 50), (80, 50), (50, 80), (40, 60), (60, 40)]

# if there are more food sources than predefined positions, generate random positions for the remaining food sources
if NUMBER_OF_FOOD > len(positions_of_food):
    pos_needed = NUMBER_OF_FOOD - len(positions_of_food)
    for _ in range(pos_needed):
        positions_of_food.append((random.uniform(0, 100), random.uniform(0, 100)))

elif NUMBER_OF_FOOD < len(positions_of_food):
    positions_of_food = positions_of_food[:NUMBER_OF_FOOD]
else:
    pass

# if there are more water sources than predefined positions, generate random positions for the remaining water sources and vice versa.
if NUMBER_OF_WATER > len(positions_of_water):
    pos_needed = NUMBER_OF_WATER - len(positions_of_water)
    for _ in range(pos_needed):
        positions_of_water.append((random.uniform(0, 100), random.uniform(0, 100)))

elif NUMBER_OF_WATER < len(positions_of_water):
    positions_of_water = positions_of_water[:NUMBER_OF_WATER]
else:
    pass

sim: Simulation | None = None
connected_clients: list[WebSocket] = []

def get_snapshot():
    """takes snapshot of the simulation and shrinks it into 
    Dictionary that can be turned into a JSON string and sent over the internet."""
    if sim is None:
        return {}
    creatures = [
        {
            "id": c.id,
            "species": c.name,
            "sex": "F" if c.sex else "M",
            "age": c.age,
            "food": c.food_level,
            "water": c.water_level,
            # rounds position to two decimal places to make text shorter (5.234234, 6.45645635) -> (5,23, 6.45)
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
    """send snapshot to every Godot instance (client) that is currently listening."""
    if not connected_clients:
        return
    # translate to string. cant send ditrionaries.
    data = json.dumps(get_snapshot()) 
    # Iterate on a copy to avoid "list size changed during iteration" errors
    for client in connected_clients[:]:
        try:
            await client.send_text(data)
        except Exception:
            connected_clients.remove(client)

async def save_to_db(db: Database, tick_count: int):
    """Save the current simulation state to the database in a non-blocking way."""
    # Offload DB blocking calls to a thread if your DB driver is synchronous
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: _sync_save(db, tick_count))

def _sync_save(db: Database, tick_count: int):
    tick_id = db.save_tick(tick_count, len(sim.creatures))
    db.save_creature_states(tick_id, sim.creatures)
    db.save_resource_states(tick_id, sim.food_sources, sim.water_sources)

async def run_simulation():                 
    """Initialize the simulation, then run the continuous async main loop."""
    global sim
    db = Database()
    sim = Simulation(db=db)

    if RESUME:
        db.resume_run(RESUME_ID)
        sim.load_state(db, RESUME_ID)
    else:
        db.start_run(f"Run {RESUME_ID}", "Baseline simulation")

        # adds creatures and resources to the simulation. If resuming, they will be loaded from the database instead.
        # if there is not a set position for a resource, then it will be placed in a random position. This is to ensure that the simulation is not always the same and to add some variability.

        for _ in range(NUMBER_OF_CREATURES):
            sim.add_creature(erf((random.uniform(0, 100), random.uniform(0, 100))))
        
        # Use each predefined food position once, or from randomly generated positions
        for pos in positions_of_food:
            sim.add_food(FoodSource(pos))

        # Use each predefined water position once
        for pos in positions_of_water:
            sim.add_water(WaterSource(pos, quantity=1500, replenish_rate=10))

    print("✅ Simulation Initialized")

    while True:
        sim.tick()
        await broadcast_snapshot()

        if sim.tick_count % DB_SAVE_INTERVAL == 0:
            asyncio.create_task(save_to_db(db, sim.tick_count))

        await asyncio.sleep(TICK_RATE)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the simulation when the FastAPI app launches and cancel it at shutdown."""
    sim_task = asyncio.create_task(run_simulation())
    yield
    sim_task.cancel()

app = FastAPI(lifespan=lifespan) 

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Accept WebSocket clients and keep them connected for live snapshots."""
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True:
            await ws.receive_text() # Heartbeat
    except WebSocketDisconnect:
        if ws in connected_clients:
            connected_clients.remove(ws)

if __name__ == "__main__":
    """Run the FastAPI application directly when the module is executed."""
    uvicorn.run(app, host="0.0.0.0", port=8000)
