import random
import math
from creatures.base_creature import BaseCreature

class Glooper(BaseCreature):
    def __init__(self, position):
        # Predators are usually slightly faster and have better vision than prey
        super().__init__(
            name           = "Glooper",
            dimension      = "2D",
            position       = position,
            speed          = 1.2,        # Erf speed is usually 1.0
            vision_range   = 15,       # Wider vision to spot moving prey
            food_capacity  = 200,      # Larger stomach for "feast or famine"
            water_capacity = 150
        )
        self.max_age = 500
        self.reproduction_threshold = 140
        
        # Gestation logic
        self.pregnant = False
        self.gestation_timer = 0
        self.gestation_duration = 50

    def update(self):
        """Override base update to include gestation costs."""
        if not self.alive:
            return

        super().update() # Handles aging, base hunger, and thirst

        if self.pregnant:
            self.food_level -= 0.2  # Extra hunger cost for pregnancy
            self.gestation_timer += 1
            if self.gestation_timer >= self.gestation_duration:
                self.pregnant = False
                self.gestation_timer = 0
                return "birth_event" # Signal for the simulation loop
        return None

    def seek(self, world_objects, world_width, world_height):
        """Predator Decision Tree."""
        visible = self.look(world_objects)
        
        # 1. Thirst is always the highest priority (hard to hunt while dehydrated)
        if (self.water_level / self.water_capacity) < 0.4:
            water = [o for o in visible if o.get_type() == "water"]
            if water:
                target = min(water, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
                return

        # 2. Reproduction
        if self.ready_to_reproduce:
            # Reuses your logic for finding a mate from BaseCreature
            super().seek(world_objects, world_width, world_height)
            return

        # 3. Hunting (The Carnivore Part)
        if self.food_level < (self.food_capacity * 0.8):
            # Find all Erfs that are currently alive
            prey_list = [o for o in visible 
                         if getattr(o, "name", "") == "erf" and o.alive]
            
            if prey_list:
                target_prey = min(prey_list, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target_prey.position, world_width, world_height)
                self._attack(target_prey)
                return

        # 4. Default: Wander
        self.wander(world_width, world_height)

    def _attack(self, prey):
        """Check if close enough to 'eat' the prey."""
        dist = math.dist(self.position, prey.position)
        if dist <= self.speed + 2: # Slightly larger range for a lunge/bite
            prey.die()
            self.food_level = min(self.food_level + 100, self.food_capacity)
            print(f"🍴 {self.name} hunted an Erf! Food Level: {self.food_level}")