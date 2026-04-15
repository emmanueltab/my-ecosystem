import random
import math
from creatures.base_creature import BaseCreature
from creatures.r2.erf import erf # Needed to identify prey

class glooper(BaseCreature):
    """Glooper: Primary predator that hunts erfs."""
    def __init__(self, position):
        super().__init__(
            position, speed=0.9, vision_range=15, food_capacity=200,
            water_capacity=200, hunger_rate=0.2, thirst_rate=0.2, max_age=400, name="glooper", dimension="2D"
        )
        self.sex = random.choice([True, False])  # True=F, False=M
        self.reproduction_threshold = 80
        self.reproduction_cooldown = 0
        self.reproduction_cooldown_duration = 40
        self.reproduction_age_threshold = 20

        # Gestation
        self.pregnant = False
        self.gestation_duration = 20
        self.gestation_timer = 0
        self.birth_pending = False

    @property
    def ready_to_reproduce(self):
        """Female cannot reproduce while pregnant."""
        if self.sex and self.pregnant:
            return False
        return (self.alive and self.age >= self.reproduction_age_threshold and
                self.reproduction_cooldown == 0 and
                self.food_level >= self.reproduction_threshold and
                self.water_level >= self.reproduction_threshold)

    def update(self):
        """Update with gestation metabolic costs and birth timing."""
        if not self.alive:
            return

        # Gestating glooper burns slightly more food/water
        if self.pregnant:
            self.food_level -= 0.25
            self.water_level -= 0.25

        super().update()

        if self.pregnant and self.alive:
            self.gestation_timer -= 1
            if self.gestation_timer <= 0:
                self.pregnant = False
                self.birth_pending = True

    def reproduce(self, nearby_creatures):
        """Female pregnancy/birth logic."""
        if not self.sex:
            return None

        if self.birth_pending:
            self.birth_pending = False
            self.reproduction_cooldown = self.reproduction_cooldown_duration
            return glooper(self.position)

        if self.pregnant:
            return None

        # Find mate (GLOOPER-specific)
        mate = next((c for c in nearby_creatures if isinstance(c, glooper) and
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
        """Decision tree: Mate -> Water -> Hunt Erfs -> Wander."""
        visible = self.look(world_objects)
        
        # 1. Reproduction Priority
        if self.ready_to_reproduce:
            self.wander(world_width, world_height)
            return

        # 2. Water Priority
        if (self.water_level / self.water_capacity) < 0.5:
            water = [o for o in visible if o.get_type() == "water"]
            if water:
                target = min(water, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
                return

        # 3. Hunting Erf Priority (Meat)
        if self.food_level < (self.food_capacity * 0.9):
            prey_list = [o for o in visible if isinstance(o, erf) and o.alive]
            if prey_list:
                target_prey = min(prey_list, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target_prey.position, world_width, world_height)
                self._attack(target_prey)
                return

        # 4. Default Wander
        self.wander(world_width, world_height)

    def _attack(self, prey):
        """Kill the prey and replenish food if close enough."""
        dist = math.dist(self.position, prey.position)
        if dist <= self.speed + 2: 
            prey.die()
            self.food_level = min(self.food_level + 100, self.food_capacity)

    def __str__(self):
        sex_label = "F" if self.sex else "M"
        status = "pregnant" if self.pregnant else "alive"
        return (f"glooper [{sex_label}] | Age: {self.age} | "
                f"food_level: {self.food_level}/{self.food_capacity} | "
                f"water_level: {self.water_level}/{self.water_capacity} | "
                f"Position: ({self.position[0]:.1f}, {self.position[1]:.1f}) | "
                f"{status}")
