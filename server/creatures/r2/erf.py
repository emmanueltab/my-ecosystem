import random
import math
from creatures.base_creature import BaseCreature

class erf(BaseCreature):
    """ERF: Fast-moving, short-lived prey that reproduces quickly."""

    def __init__(self, position):
        super().__init__(
            position, speed=2, vision_range=15, food_capacity=100,
            water_capacity=100, max_age=400, name="erf", dimension="2D"
        )
        # Reproduction
        self.sex = random.choice([True, False])  # True=F, False=M
        self.reproduction_threshold = 65
        self.reproduction_cooldown = 0
        self.reproduction_cooldown_duration = 30
        self.reproduction_age_threshold = 20

        # Gestation
        self.pregnant = False
        self.gestation_duration = 20
        self.gestation_timer = 0
        self.birth_pending = False

    def update(self):
        """ERF-specific update with gestation costs."""
        if self.pregnant:
            self.food_level -= 0.4
            self.water_level -= 0.6
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
            self.reproduction_cooldown = self.reproduction_cooldown_duration
            return erf(self.position)

        if self.pregnant:
            return None

        # Find mate by name filter (ERF-specific)
        mate = next((c for c in nearby_creatures if getattr(c, 'name', '') == 'erf' and
                     c.sex != self.sex and c.alive and c.ready_to_reproduce), None)
        if mate:
            # Mate if close and eligible
            if math.dist(self.position, mate.position) <= self.vision_range:
                self.food_level -= 20
                self.water_level -= 20
                self.pregnant = True
                self.gestation_timer = self.gestation_duration
                self.reproduction_cooldown = self.reproduction_cooldown_duration
                mate.reproduction_cooldown = mate.reproduction_cooldown_duration
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

        # Reproduce
        if self.ready_to_reproduce:
            self.wander(world_width, world_height)
            return

        # Resources
        if self.food_level < 50 or self.water_level < 50:
            food = [o for o in visible if o.get_type() == 'food' and o.has_resource()]
            water = [o for o in visible if o.get_type() == 'water' and o.has_resource()]
            if food or water:
                # Prioritize lower level
                if self.food_level < self.water_level:
                    if food:
                        target = min(food, key=lambda o: math.dist(self.position, o.position))
                    else:
                        target = min(water, key=lambda o: math.dist(self.position, o.position))
                else:
                    if water:
                        target = min(water, key=lambda o: math.dist(self.position, o.position))
                    else:
                        target = min(food, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
                return

        self.wander(world_width, world_height)

    def get_type(self):
        return "creature"

    def __str__(self):
        sex_label = "F" if self.sex else "M"
        status = "pregnant" if self.pregnant else "alive"
        return (f"erf [{sex_label}] | Age: {self.age} | "
                f"food_level: {self.food_level}/{self.food_capacity} | "
                f"water_level: {self.water_level}/{self.water_capacity} | "
                f"Position: ({self.position[0]:.1f}, {self.position[1]:.1f}) | "
                f"{status}")
