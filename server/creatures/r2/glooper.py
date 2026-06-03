import random
import math
from creatures.base_creature import BaseCreature

class glooper(BaseCreature):
    """Glooper: Built on the exact logic of the Erf but modified to hunt."""

    def __init__(self, position):
        # Increased capacity and slightly lower speed than Erf to balance the simulation
        super().__init__(
            position, speed=0.9, vision_range=15, food_capacity=200,
            water_capacity=200, hunger_rate=0.2, thirst_rate=0.2, max_age=400, aging_rate=0.5, name="glooper", dimension="2D"
        )
        # Reproduction
        self.sex = random.choice([True, False])
        self.reproduction_threshold = 80
        self.reproduction_cooldown = 0
        self.reproduction_cooldown_duration = 40
        self.reproduction_age_threshold = 20

        # Gestation
        self.pregnant = False
        self.gestation_duration = 20
        self.gestation_timer = 0
        self.birth_pending = False

    def update(self):
        if self.pregnant:
            self.food_level -= self.hunger_rate * 1.2
            self.water_level -= self.hunger_rate * 1.2 
        super().update()

        if self.pregnant and self.alive:
            self.gestation_timer -= 1
            if self.gestation_timer <= 0:
                self.pregnant = False
                self.birth_pending = True

    @property
    def ready_to_reproduce(self):
        if self.sex and self.pregnant:
            return False
        return (self.alive and self.age >= self.reproduction_age_threshold and
                self.reproduction_cooldown == 0 and
                self.food_level >= self.reproduction_threshold and
                self.water_level >= self.reproduction_threshold)

    def reproduce(self, nearby_creatures):
        if not self.sex: return None
        if self.birth_pending:
            self.birth_pending = False
            self.reproduction_cooldown = self.reproduction_cooldown_duration
            return glooper(self.position)
        if self.pregnant: return None

        # Identifies mates using name string to avoid circular imports
        mate = next((c for c in nearby_creatures if getattr(c, 'name', '') == 'glooper' and
                     c.sex != self.sex and c.alive and c.ready_to_reproduce), None)
        
        if mate:
            dist = math.dist(self.position, mate.position)
            if dist <= self.vision_range:
                self.food_level -= 20
                self.water_level -= 20
                self.pregnant = True
                self.gestation_timer = self.gestation_duration
                self.reproduction_cooldown = self.reproduction_cooldown_duration
                mate.reproduction_cooldown = mate.reproduction_cooldown_duration
        return None

    def seek(self, world_objects, world_width, world_height):
        visible = self.look(world_objects)
        
        # 1. Reproduction Mode
        if self.ready_to_reproduce:
            mates = [o for o in visible if getattr(o, 'name', '') == 'glooper' and 
                     o.sex != self.sex and o.ready_to_reproduce]
            if mates:
                target = min(mates, key=lambda m: math.dist(self.position, m.position))
                self.move_toward(target.position, world_width, world_height)
                return
            else:
                self.wander(world_width, world_height)
                return

        # 2. Resource/Hunting Mode
        if self.food_level < (self.food_capacity * 0.9) or self.water_level < (self.water_capacity * 0.7):
            water_sources = [o for o in visible if o.get_type() == 'water' and o.has_resource()]
            # Predator change: Hunt erfs instead of looking for food sources
            prey_list = [o for o in visible if getattr(o, 'name', '') == 'erf' and o.alive]
            
            target = None

            # Priority Logic (Lower level first)
            if self.water_level <= self.food_level:
                if water_sources:
                    target = min(water_sources, key=lambda o: math.dist(self.position, o.position))
                else:
                    self.wander(world_width, world_height)
                    return
            else:
                if prey_list:
                    target = min(prey_list, key=lambda o: math.dist(self.position, o.position))
                else:
                    self.wander(world_width, world_height)
                    return

            if target:
                dist = math.dist(self.position, target.position)
                # If the target is an Erf, attack; if it's Water, drink.
                if getattr(target, 'name', '') == 'erf':
                    if dist <= self.speed + 2:
                        self._attack(target)
                    else:
                        self.move_toward(target.position, world_width, world_height)
                else:
                    if dist <= self.speed:
                        self.interact(target)
                    else:
                        self.move_toward(target.position, world_width, world_height)
                return

        self.wander(world_width, world_height)

    def _attack(self, prey):
        prey.die()
        self.food_level = min(self.food_level + 100, self.food_capacity)

    def get_type(self):
        return "creature"

    def __str__(self):
        sex_label = "F" if self.sex else "M"
        status = "pregnant" if self.pregnant else "alive"
        return (f"glooper [{sex_label}] | Age: {self.age} | "
                f"food: {self.food_level}/{self.food_capacity} | "
                f"water: {self.water_level}/{self.water_capacity} | {status}")