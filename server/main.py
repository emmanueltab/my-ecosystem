from simulation import Simulation
from creatures.r2.rabbit import Rabbit
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
from database import Database
import random
from fastapi import FastAPI
import uvicorn
import threading

# ── FastAPI app ──────────────────────────────────────
# Creates the FastAPI application that listens for HTTP requests
app = FastAPI()

# ── Shared simulation state ──────────────────────────
# Declared at the top level so FastAPI endpoints can access
# the simulation object while it runs in the background thread
sim = None

@app.get("/status")
def status():
    # Returns basic simulation status
    if sim is None:
        return {"status": "starting"}
    return {
        "status":     "running" if sim.running else "paused",
        "tick":       sim.tick_count,
        "population": len(sim.creatures)
    }

@app.get("/creatures")
def get_creatures():
    # Returns the current state of all living creatures
    if sim is None:
        return {"error": "Simulation not started yet"}
    return [
        {
            "id":          c.id,
            "species":     c.name,
            "sex":         "F" if c.sex else "M",
            "age":         c.age,
            "food_level":  c.food_level,
            "water_level": c.water_level,
            "position":    c.position,
            "alive":       c.alive
        }
        for c in sim.creatures.values()
    ]

@app.get("/resources")
def get_resources():
    # Returns the current state of all food and water sources
    if sim is None:
        return {"error": "Simulation not started yet"}
    food = [
        {"id": f.id, "type": "food", "quantity": f.quantity, "position": f.position}
        for f in sim.food_sources.values()
    ]
    water = [
        {"id": w.id, "type": "water", "quantity": w.quantity, "position": w.position}
        for w in sim.water_sources.values()
    ]
    return food + water

@app.post("/pause")
def pause():
    # Pauses the simulation loop
    if sim is None:
        return {"error": "Simulation not started yet"}
    sim.pause()
    return {"status": "paused"}

@app.post("/resume")
def resume():
    # Resumes the simulation loop in a new thread
    if sim is None:
        return {"error": "Simulation not started yet"}
    thread = threading.Thread(target=sim.run)
    thread.daemon = True
    thread.start()
    return {"status": "resumed"}

# ── Configure run here ──────────────────────────────
RESUME    = False  # set to True to resume an existing run
RESUME_ID = 1     # run id to resume (check DB Browser)
# ────────────────────────────────────────────────────

def run_simulation():
    # ── Database & simulation setup ──────────────────
    # Created inside the thread so SQLite stays in the
    # same thread it was created in
    global sim
    db  = Database()
    sim = Simulation(db=db)

    # Either resume an existing run or start a fresh one
    if RESUME:
        db.resume_run(RESUME_ID)
        sim.load_state(db, RESUME_ID)
    else:
        db.start_run(
            name  = "Run 1 — baseline",
            notes = "200 rabbits, 10 food, 10 water, 100x100 world"
        )
        # ── Populate the world ───────────────────────
        # Only runs on a fresh run — load_state() handles
        # repopulation when resuming
        for i in range(200):
            position = (random.uniform(0, 100), random.uniform(0, 100))
            sim.add_creature(Rabbit(position))
        for i in range(20):
            position = (random.uniform(0, 100), random.uniform(0, 100))
            sim.add_food(FoodSource(position))
        for i in range(20):
            position = (random.uniform(0, 100), random.uniform(0, 100))
            sim.add_water(WaterSource(position))

    # ── Run the simulation loop ──────────────────────
    # Runs indefinitely until the server is stopped
    sim.run()

# ── Start simulation in background thread ────────────
# Runs the simulation in a separate worker so FastAPI
# can listen for requests at the same time.
# daemon=True ensures the thread dies when the server is stopped.
sim_thread = threading.Thread(target=run_simulation)
sim_thread.daemon = True
sim_thread.start()

# ── Start FastAPI server ─────────────────────────────
# Starts the server and keeps it running, listening for requests.
# This must be last since uvicorn.run() blocks the main thread.
uvicorn.run(app, host="0.0.0.0", port=8000)