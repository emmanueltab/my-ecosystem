import random
import math
from creatures.base_creature import BaseCreature

class erf(BaseCreature):
    """ERF: Fast-moving, short-lived prey that reproduces quickly.
    the stuff in the parametersr are the traits that the offspring will inhereit. may consider moving them to a bag."""

    def __init__(self, position, speed=2, vision_range=15, max_age=400):
        super().__init__(
            position, speed=speed, vision_range=vision_range, food_capacity=100,
            water_capacity=100, hunger_rate=0.2, thirst_rate=0.2, max_age=max_age, aging_rate=0.5, name="erf", dimension="2D"
        )
        # Reproduction
        self.sex = random.choice([True, False])  # True=F, False=M
        self.reproduction_threshold = 40 # required food and water in order to reproduce
        self.reproduction_cooldown = 0
        self.reproduction_cooldown_duration = 30
        self.reproduction_age_threshold = 20

        # Gestation
        self.pregnant = False
        self.gestation_duration = 20 # amount of ticks pregrancy lasts
        self.gestation_timer = 0
        self.birth_pending = False
        self.reproduction_cost = 15 # amount of food/water lost after giving birth

        self.father_genes = None

    def update(self):
        """ERF-specific update with gestation costs."""
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
        """Female cannot reproduce while pregnant."""
        if self.sex and self.pregnant:
            return False
        return (self.alive and self.age >= self.reproduction_age_threshold and
                self.reproduction_cooldown == 0 and
                self.food_level >= self.reproduction_threshold and
                self.water_level >= self.reproduction_threshold)

    def reproduce(self, nearby_creatures):
        """Female pregnancy/birth logic."""
        if not self.sex:
            return None

        if self.birth_pending:
                self.birth_pending = False
                
                # 1. Calculate the Averages (Inheritance)
                avg_speed = (self.speed + self.father_genes['speed']) / 2
                avg_vision = (self.vision_range + self.father_genes['vision']) / 2
                avg_max_age = (self.max_age + self.father_genes['max_age']) / 2

                # 2. Apply Percentage-Based Mutation (e.g., +/- 10%)
                # This scales automatically: 10% of 2 is 0.2, 10% of 400 is 40.
                def mutate(value, percent=0.1):
                    mutation_multiplier = random.uniform(1 - percent, 1 + percent)
                    return value * mutation_multiplier

                child_speed   = mutate(avg_speed, percent=0.05)   # 5% mutation
                child_vision  = mutate(avg_vision, percent=0.05)  # 5% mutation
                child_max_age = mutate(avg_max_age, percent=0.05) # 5% mutation

                # 3. Create the child with scaled traits
                return erf(
                    self.position, 
                    speed=max(0.5, child_speed), 
                    vision_range=max(5, child_vision), 
                    max_age=max(100, child_max_age)
                )
       
        if self.pregnant:
            return None

        # Find mate by name filter (ERF-specific)
        mate = next((c for c in nearby_creatures if getattr(c, 'name', '') == 'erf' and
                     c.sex != self.sex and c.alive and c.ready_to_reproduce), None)
        if mate:
            # Mate if close and eligible
            if math.dist(self.position, mate.position) <= self.vision_range:
                self.food_level -= self.reproduction_cost
                self.water_level -= self.reproduction_cost
                self.pregnant = True
                self.gestation_timer = self.gestation_duration
                self.reproduction_cooldown = self.reproduction_cooldown_duration
                mate.reproduction_cooldown = mate.reproduction_cooldown_duration
               
                self.father_genes = { 
                    'speed': mate.speed, 
                    'vision': mate.vision_range,
                    'max_age': mate.max_age
                }
               
                return None
            
        return None

    def seek(self, world_objects, world_width, world_height):
        """ERF behavior: Flee gloopers > Reproduce > Resources > Wander."""
        visible = self.look(world_objects)

        # Flee predators
        predators = [o for o in visible if getattr(o, 'name', '') == 'glooper' and o.alive]
        if predators:
            closest = min(predators, key=lambda p: math.dist(self.position, p.position))
            dx = closest.position[0] - self.position[0]
            dy = closest.position[1] - self.position[1]
            angle_to_pred = math.degrees(math.atan2(dy, dx))
            self.direction = (angle_to_pred + 180) % 360
            self.move(world_width, world_height)
            return

        elif self.ready_to_reproduce:
            # Use the 'visible' list we already calculated!
            mates = [o for o in visible if getattr(o, 'name', '') == 'erf' and 
                    o.sex != self.sex and o.ready_to_reproduce]
            if mates:
                target = min(mates, key=lambda m: math.dist(self.position, m.position))
                self.move_toward(target.position, world_width, world_height)
                return # Priority: Mating over Food/Wander

        # Resources Logic
        if self.food_level < self.reproduction_threshold or self.water_level < self.reproduction_threshold:
            food_sources = [o for o in visible if o.get_type() == 'food' and o.has_resource()]
            water_sources = [o for o in visible if o.get_type() == 'water' and o.has_resource()]

            target = None

            # 1. Logic for (w <= 50) and (f <= 50) AND (f == w)
            if self.food_level == self.water_level:
                choice = random.choice(['f', 'w'])
                if choice == 'f':
                    target = min(food_sources, key=lambda o: math.dist(self.position, o.position)) if food_sources else None
                else:
                    target = min(water_sources, key=lambda o: math.dist(self.position, o.position)) if water_sources else None

            # 2. Logic for (w < f) - Priority: Water
            elif self.water_level < self.food_level:
                if water_sources:
                    target = min(water_sources, key=lambda o: math.dist(self.position, o.position))
                else:
                    # SEARCH MODE: I need water but don't see it. 
                    # Pick a direction and move until I find it.
                    self.wander(world_width, world_height)
                    return

            # 3. Logic for (f < w) - Priority: Food
            elif self.food_level < self.water_level:
                if food_sources:
                    target = min(food_sources, key=lambda o: math.dist(self.position, o.position))
                else:
                    # SEARCH MODE: I need food but don't see it.
                    self.wander(world_width, world_height)
                    return

            # EXECUTION: If a target was found in FOV, move to it or eat it
            if target:
                dist = math.dist(self.position, target.position)
                if dist <= self.speed:
                    self.interact(target)
                else:
                    self.move_toward(target.position, world_width, world_height)
                return

        # DEFAULT: If levels > 50 or we are just exploring
        self.wander(world_width, world_height)

    def get_type(self):
        return "creature"

    def __str__(self):
        sex_label = "F" if self.sex else "M"
        status = "pregnant" if self.pregnant else "alive"
        
        # New: Genetic trait summary
        genes = f"S:{self.speed:.2f} | V:{self.vision_range:.1f} | MA:{self.max_age:.0f}"

        return (f"erf [{sex_label}] | {genes} | Age: {self.age:.1f} | "
                f"food_level: {self.food_level}/{self.food_capacity} | "
                f"water_level: {self.water_level}/{self.water_capacity} | "
                f"Pos: ({self.position[0]:.1f}, {self.position[1]:.1f}) | "
                f"{status}")
