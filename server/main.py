import random
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from simulation import Simulation
from creatures.r2.rabbit import Rabbit
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
from database import Database

# ── Configuration ─────────────────
RESUME = False
RESUME_ID = 1
TICK_RATE = 0.25
DB_SAVE_INTERVAL = 10

sim: Simulation | None = None
connected_clients: list[WebSocket] = []

def get_snapshot():
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
    if not connected_clients:
        return
    
    data = json.dumps(get_snapshot())
    # Iterate on a copy to avoid "list size changed during iteration" errors
    for client in connected_clients[:]:
        try:
            await client.send_text(data)
        except Exception:
            connected_clients.remove(client)

async def save_to_db(db: Database, tick_count: int):
    # Offload DB blocking calls to a thread if your DB driver is synchronous
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: _sync_save(db, tick_count))

def _sync_save(db: Database, tick_count: int):
    tick_id = db.save_tick(tick_count, len(sim.creatures))
    db.save_creature_states(tick_id, sim.creatures)
    db.save_resource_states(tick_id, sim.food_sources, sim.water_sources)

async def run_simulation():
    global sim
    db = Database()
    sim = Simulation(db=db)

    if RESUME:
        db.resume_run(RESUME_ID)
        sim.load_state(db, RESUME_ID)
    else:
        db.start_run(f"Run {RESUME_ID}", "Baseline simulation")
        for _ in range(100):
            sim.add_creature(Rabbit((random.uniform(0, 100), random.uniform(0, 100))))
        for _ in range(50):
            sim.add_food(FoodSource((random.uniform(0, 100), random.uniform(0, 100))))
        # Inside your simulation setup
        for _ in range(3): # Only 3 substantial lakes for the whole 100x100 map
            x = random.uniform(10, 90) # Keep them slightly away from the absolute edges
            y = random.uniform(10, 90)
            lake = WaterSource((x, y), quantity=1500, replenish_rate=10)
            sim.add_water(lake)

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
            await ws.receive_text() # Heartbeat
    except WebSocketDisconnect:
        if ws in connected_clients:
            connected_clients.remove(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)