import random
import json
import time
import threading
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from simulation import Simulation
from creatures.r2.rabbit import Rabbit
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
from database import Database

# ── FastAPI app ─────────────────────────────────────
app = FastAPI()

# ── Shared simulation state ─────────────────────────
sim = None
connections = set()  # active WebSocket connections

# ── HTTP Endpoints (optional) ─────────────────────
@app.get("/status")
def status():
    if sim is None:
        return {"status": "starting"}
    return {
        "status": "running" if sim.running else "paused",
        "tick": sim.tick_count,
        "population": len(sim.creatures)
    }

# ── WebSocket Endpoint ─────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    print(f"Client connected: {len(connections)} total")
    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=1.0)
                data = json.loads(msg)
                if data.get("action") == "pause":
                    sim.pause()
                elif data.get("action") == "resume":
                    sim.running = True
            except asyncio.TimeoutError:
                pass  # no message, continue
    except WebSocketDisconnect:
        connections.remove(ws)
        print(f"Client disconnected: {len(connections)} remaining")

# ── Broadcast function ─────────────────────────────
async def broadcast_simulation_state():
    if sim is None:
        return
    data = {
        "tick": sim.tick_count,
        "creatures": [
            {
                "id": c.id,
                "species": c.name,
                "sex": "F" if c.sex else "M",
                "age": c.age,
                "food_level": c.food_level,
                "water_level": c.water_level,
                "position": c.position,
                "alive": c.alive
            }
            for c in sim.creatures.values()
        ],
        "resources": [
            {"id": f.id, "type": "food", "quantity": f.quantity, "position": f.position}
            for f in sim.food_sources.values()
        ] + [
            {"id": w.id, "type": "water", "quantity": w.quantity, "position": w.position}
            for w in sim.water_sources.values()
        ]
    }
    disconnected = []
    for ws in connections:
        try:
            await ws.send_text(json.dumps(data))
        except:
            disconnected.append(ws)
    for ws in disconnected:
        connections.remove(ws)

# ── Simulation Thread ─────────────────────────────
TICK_RATE = 0.5  # seconds per tick

def run_simulation_loop():
    global sim
    db = Database()
    sim = Simulation(db=db)

    # Populate world
    for i in range(200):
        position = (random.uniform(0, 100), random.uniform(0, 100))
        sim.add_creature(Rabbit(position))
    for i in range(20):
        position = (random.uniform(0, 100), random.uniform(0, 100))
        sim.add_food(FoodSource(position))
    for i in range(20):
        position = (random.uniform(0, 100), random.uniform(0, 100))
        sim.add_water(WaterSource(position))

    # Start simulation loop with proper tick rate
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        sim.tick()  # advance one tick
        loop.run_until_complete(broadcast_simulation_state())
        time.sleep(TICK_RATE)  # <- throttles to 2 ticks/sec

# ── Start simulation in background ────────────────
sim_thread = threading.Thread(target=run_simulation_loop, daemon=True)
sim_thread.start()

# ── Start FastAPI server ──────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)