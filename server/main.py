from simulation import Simulation
from creatures.r2.rabbit import Rabbit
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
from database import Database
import random

# ── Configure run here ──────────────────────────────
RESUME    = False # resume an existing run
RESUME_ID = 1       # run id to resume (check DB Browser)
# ────────────────────────────────────────────────────

db  = Database()
sim = Simulation(db=db)

if RESUME:
    db.resume_run(RESUME_ID)
    sim.load_state(db, RESUME_ID)
else:
    db.start_run(
        name  = "Run 1 — baseline",
        notes = "20 rabbits, 10 food, 10 water, 100x100 world"
    )
    for i in range(20):
        position = (random.uniform(0, 100), random.uniform(0, 100))
        sim.add_creature(Rabbit(position))
    for i in range(10):
        position = (random.uniform(0, 100), random.uniform(0, 100))
        sim.add_food(FoodSource(position))
    for i in range(10):
        position = (random.uniform(0, 100), random.uniform(0, 100))
        sim.add_water(WaterSource(position))

sim.run(ticks=20)

db.end_run()
db.close()
print("Database closed.")