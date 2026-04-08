import time
import random
import math
from creatures.r2.erf import erf
from creatures.r2.glooper import Glooper
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

    # Registry for dynamic loading
        self.creature_registry = {
            "erf": erf,
            "Glooper": Glooper
        }

    # adder functions (creatures, food, and water)
    def add_creature(self, creature):
        self.creatures[creature.id] = creature

    def add_food(self, food):
        self.food_sources[food.id] = food

    def add_water(self, water):
        self.water_sources[water.id] = water

    # keep every creature that is alive, and disregard the ones are are not alive:
    def remove_dead(self):
        self.creatures = {
            id: c for id, c in self.creatures.items() if c.alive
        }

    def tick(self):
        """Represents one unit of time."""
        self.tick_count += 1
        print(f"\n--- Tick {self.tick_count} ---")

        # Combine food, water, and creatures into one list for seeking
        world_objects = (list(self.food_sources.values()) +
                         list(self.water_sources.values()) +
                         list(self.creatures.values()))

        # Handle Reproduction and Births
        new_creatures = []
        
        # 1. Update all creatures
        for creature in list(self.creatures.values()):
            # Handle special birth signals (like Gloopers)
            signal = creature.seek(world_objects, self.world_width, self.world_height)
            if signal == "birth_event":
                species_class = self.creature_registry.get(creature.name)
                if species_class:
                    new_creatures.append(species_class(creature.position))
                    print(f"Birth Event: New {creature.name} born via gestation!")

            creature.update() # Age, metabolism, etc.
            
            # 2. Handle standard contact reproduction (Erf style)
            nearby = [c for c in self.creatures.values()
                      if c != creature
                      and math.dist(creature.position, c.position) <= creature.vision_range]
            offspring = creature.reproduce(nearby)
            if offspring:
                new_creatures.append(offspring)
                print(f"New {offspring.name} [{offspring.sex}] born via contact!")

        # Add all newborns to simulation
        for offspring in new_creatures:
            self.add_creature(offspring)

        # Replenish resources
        for food in self.food_sources.values():
            food.replenish()
        for water in self.water_sources.values():
            water.replenish()

        # Final cleanup
        self.remove_dead()
        print(f"Population: {len(self.creatures)}")

        # Save to DB if connected (Every 10 ticks)
        if self.db and self.tick_count % 10 == 0:
            tick_id = self.db.save_tick(self.tick_count, len(self.creatures))
            self.db.save_creature_states(tick_id, self.creatures)
            self.db.save_resource_states(tick_id, self.food_sources, self.water_sources)

    def load_state(self, db, run_id):
        """Loads the last saved state of a run."""
        result = db.get_last_tick(run_id)
        if not result:
            print(f"⚠️ No saved state found for run_id: {run_id}")
            return

        tick_id = result["id"]
        self.tick_count = result["tick_number"]
        print(f"🔄 Resuming from tick {self.tick_count}...")

        self.creatures.clear()
        self.food_sources.clear()
        self.water_sources.clear()

        # Reload creatures dynamically via Registry
        for row in db.get_creature_states(tick_id):
            pos = (row["pos_x"], row["pos_y"])
            species_name = row["species"]
            
            # Use registry to find the correct class
            CreatureClass = self.creature_registry.get(species_name, erf)
            creature = CreatureClass(pos)
            
            creature.id = row["creature_id"]
            creature.sex = True if row["sex"] == "F" else False
            creature.age = row["age"]
            creature.food_level = row["food_level"]
            creature.water_level = row["water_level"]
            creature.alive = bool(row["alive"])
            self.add_creature(creature)

        # Reload resources
        for row in db.get_resource_states(tick_id):
            pos = (row["pos_x"], row["pos_y"])
            if row["resource_type"] == "food":
                food = FoodSource(pos)
                food.id = row["resource_id"]
                food.quantity = row["quantity"]
                self.add_food(food)
            elif row["resource_type"] == "water":
                water = WaterSource(pos)
                water.id = row["resource_id"]
                water.quantity = row["quantity"]
                self.add_water(water)

        print(f"✅ Resume complete: {len(self.creatures)} creatures restored.")

    def run(self, ticks=999999):
        """Runs the simulation loop for a given number of ticks.
        Defaults to 999999 so it runs indefinitely in server mode."""
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