import time
import random
from creatures.r2.rabbit import Rabbit
from creatures.r2.food_source import FoodSource
from creatures.r2.water_source import WaterSource
import math
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

class Simulation:
    def __init__(self, world_width=100, world_height=100):
        # World boundaries
        self.world_width   = world_width
        self.world_height  = world_height

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

    def run(self, ticks=20):
        self.running = True
        plt.ion()
        for _ in range(ticks):
            if not self.running:
                break
            self.tick()
            self.visualize()
            time.sleep(0.5)
        plt.ioff()
        plt.show()

    def pause(self):
        self.running = False

    def reset(self):
        self.creatures     = {}
        self.food_sources  = {}
        self.water_sources = {}
        self.tick_count    = 0
        self.running       = False

    def visualize(self):
        plt.clf()
        ax = plt.gca()
        ax.set_facecolor('black')
        plt.gcf().set_facecolor('black')
        plt.xlim(0, self.world_width)
        plt.ylim(0, self.world_height)

        # plot food sources
        for food in self.food_sources.values():
            plt.scatter(*food.position, color='green', s=100, marker='s')

        # plot water sources
        for water in self.water_sources.values():
            plt.scatter(*water.position, color='blue', s=100, marker='s')

        # plot rabbits
        for creature in self.creatures.values():
            plt.scatter(*creature.position, color='white', s=50)

        plt.title(f"Tick: {self.tick_count} | Population: {len(self.creatures)}", 
                color='white')
        plt.pause(0.1)