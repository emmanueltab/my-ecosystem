from simulation import Simulation
from creatures.r2.rabbit import Rabbit
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
import random

sim = Simulation()

# spawn 5 rabbits
for i in range(5):
    position = (random.uniform(0, 100), random.uniform(0, 100))
    sim.add_creature(Rabbit(position))

# spawn 3 food sources
for i in range(3):
    position = (random.uniform(0, 100), random.uniform(0, 100))
    sim.add_food(FoodSource(position))

# spawn 3 water sources
for i in range(3):
    position = (random.uniform(0, 100), random.uniform(0, 100))
    sim.add_water(WaterSource(position))

sim.run(ticks=20)