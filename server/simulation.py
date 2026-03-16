import time
import random
import math
from creatures.r2.rabbit import Rabbit
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource

class Simulation:
    def __init__(self, world_width=100, world_height=100, db=None):
        # World boundaries
        self.world_width   = world_width
        self.world_height  = world_height

        # Database
        self.db            = db

        # Simulation objects
        self.creatures     = {}
        self.food_sources  = {}
        self.water_sources = {}

        # Simulation state
        self.tick_count    = 0
        self.running       = False

    def add_creature(self, creature):
        self.creatures[creature.id] = creature

    def add_food(self, food):
        self.food_sources[food.id] = food

    def add_water(self, water):
        self.water_sources[water.id] = water

    def remove_dead(self):
        self.creatures = {
            id: c for id, c in self.creatures.items() if c.alive
        }

    def tick(self):
        self.tick_count += 1
        print(f"\n--- Tick {self.tick_count} ---")

        # combine food and water into one list for seeking
        world_objects = (list(self.food_sources.values()) +
                         list(self.water_sources.values()))

        # update all creatures
        for creature in self.creatures.values():
            creature.seek(world_objects, self.world_width, self.world_height)
            creature.update()
            print(creature)

        # replenish all world objects
        for food in self.food_sources.values():
            food.replenish()
        for water in self.water_sources.values():
            water.replenish()

        # handle reproduction
        new_creatures = []
        for creature in self.creatures.values():
            nearby = [c for c in self.creatures.values()
                      if c != creature
                      and math.dist(creature.position, c.position) <= creature.vision_range]
            offspring = creature.reproduce(nearby)
            if offspring:
                new_creatures.append(offspring)
                print(f"New {offspring.name} [{offspring.sex}] born!")

        for offspring in new_creatures:
            self.add_creature(offspring)

        self.remove_dead()
        print(f"Population: {len(self.creatures)}")

        # save to database if connected
        if self.db:
            tick_id = self.db.save_tick(self.tick_count, len(self.creatures))
            self.db.save_creature_states(tick_id, self.creatures)
            self.db.save_resource_states(tick_id, self.food_sources, self.water_sources)

    def load_state(self, db, run_id):
        """Loads the last saved state of a run."""
        result = db.get_last_tick(run_id)
        if not result:
            print("No saved state found.")
            return

        tick_id, tick_number = result
        self.tick_count      = tick_number
        print(f"Loading state from tick {tick_number}...")

        # reload creatures
        for row in db.get_creature_states(tick_id):
            creature_id, species, sex, age, food_level, water_level, pos_x, pos_y = row
            if species == "Rabbit":
                rabbit           = Rabbit((pos_x, pos_y))
                rabbit.id        = creature_id
                rabbit.sex       = True if sex == "F" else False
                rabbit.age       = age
                rabbit.food_level  = food_level
                rabbit.water_level = water_level
                self.add_creature(rabbit)

        # reload resources
        for row in db.get_resource_states(tick_id):
            resource_id, resource_type, quantity, pos_x, pos_y = row
            if resource_type == "food":
                food          = FoodSource((pos_x, pos_y))
                food.id       = resource_id
                food.quantity = quantity
                self.add_food(food)
            elif resource_type == "water":
                water          = WaterSource((pos_x, pos_y))
                water.id       = resource_id
                water.quantity = quantity
                self.add_water(water)

        print(f"Loaded {len(self.creatures)} creatures and "
              f"{len(self.food_sources) + len(self.water_sources)} resources.")

    def run(self, ticks=999999):
        # Runs the simulation loop for a given number of ticks.
        # Defaults to 999999 so it runs indefinitely in server mode.
        self.running = True
        for _ in range(ticks):
            if not self.running:
                break
            self.tick()
            time.sleep(0.5)

    def pause(self):
        self.running = False

    def reset(self):
        self.creatures     = {}
        self.food_sources  = {}
        self.water_sources = {}
        self.tick_count    = 0
        self.running       = False

    def visualize(self):
        # Kept for reference — replaced by Godot in Phase 4
        pass