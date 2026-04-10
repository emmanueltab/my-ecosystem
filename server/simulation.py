import time
import random
import math
from creatures.r2.erf import erf
from creatures.r2.glooper import glooper  # Added Glooper import
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
        """represents one unit of time. This is what occurs in each time unit of the simulation."""

        self.tick_count += 1
        print(f"\n--- Tick {self.tick_count} ---")

        # combine food, water, and creatures into one list for seeking
        world_objects = (list(self.food_sources.values()) +
                         list(self.water_sources.values()) +
                         list(self.creatures.values()))

        # update all creatures
        for creature in self.creatures.values():
            creature.seek(world_objects, self.world_width, self.world_height)
            creature.update() # get older, lose energy levels, die, etc)
            print(creature)

        # replenish all world objects at every tick
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

        # last action for the simulaton. Removes dead creatures every tick.
        self.remove_dead()
        print(f"Population: {len(self.creatures)}")

        # save the dictionaries of ehe state to the database if connected
        if self.db:
            tick_id = self.db.save_tick(self.tick_count, len(self.creatures))
            self.db.save_creature_states(tick_id, self.creatures)
            self.db.save_resource_states(tick_id, self.food_sources, self.water_sources)

    def load_state(self, db, run_id):
        """Loads the last saved state of a run using dictionary keys."""
        result = db.get_last_tick(run_id)
        if not result:
            print(f"⚠️ No saved state found for run_id: {run_id}")
            return

        # result is a sqlite3.Row, access by name
        tick_id = result["id"]
        self.tick_count = result["tick_number"]
        print(f"🔄 Resuming from tick {self.tick_count}...")

        # Clear current simulation state to avoid duplicates
        self.creatures.clear()
        self.food_sources.clear()
        self.water_sources.clear()

        # Mapping dictionary to handle multiple species dynamically
        species_map = {
            "erf": erf,
            "glooper": glooper
        }

        # reload creatures
        for row in db.get_creature_states(tick_id):
            # row is a dict thanks to the DB update
            pos = (row["pos_x"], row["pos_y"])
            
            species_name = row["species"]
            if species_name in species_map:
                creature_class = species_map[species_name]
                creature = creature_class(pos)
                creature.id = row["creature_id"]
                # Convert "F"/"M" or 0/1 back to simulation booleans
                creature.sex = True if row["sex"] == "F" else False
                creature.age = row["age"]
                creature.food_level = row["food_level"]
                creature.water_level = row["water_level"]
                creature.alive = bool(row["alive"])
                self.add_creature(creature)
            else:
                print(f"⚠️ Unknown species found in DB: {species_name}")

        # reload resources
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

    def setup_resources(num_food, num_water, food_list, water_list, buffer=5.0):

        """ will have to come back to this later. allignment works but not the section to check if they overlap."""

        # updates 
        # 1. Align Counts (Priority: Numbers)
        # Trim if too many, extend with random if too few
        food_list = food_list[:num_food]
        while len(food_list) < num_food:
            food_list.append((random.uniform(0, 100), random.uniform(0, 100)))

        water_list = water_list[:num_water]
        while len(water_list) < num_water:
            water_list.append((random.uniform(0, 100), random.uniform(0, 100)))

        # 2. Resolve Overlaps and Distance
        final_positions = []
        
        # Process Food
        updated_food = []
        for pos in food_list:
            current_pos = pos
            # Check against all previously accepted positions
            while any(math.sqrt((current_pos[0]-p[0])**2 + (current_pos[1]-p[1])**2) < buffer for p in final_positions):
                current_pos = (random.uniform(0, 100), random.uniform(0, 100))
            updated_food.append(current_pos)
            final_positions.append(current_pos)

        # Process Water
        updated_water = []
        for pos in water_list:
            current_pos = pos
            # Check against all food AND already placed water
            while any(math.sqrt((current_pos[0]-p[0])**2 + (current_pos[1]-p[1])**2) < buffer for p in final_positions):
                current_pos = (random.uniform(0, 100), random.uniform(0, 100))
            updated_water.append(current_pos)
            final_positions.append(current_pos)
        
        return updated_food, updated_water
