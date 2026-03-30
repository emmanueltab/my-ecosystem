import random
from creatures.base_creature import BaseCreature

class Rabbit(BaseCreature):
    def __init__(self, position):
        super().__init__(
            name         = "Rabbit",
            dimension    = "2D",
            position     = position,
            speed        = 2,
            vision_range = 10,
            food_capacity   = 100,
            water_capacity   = 100,
        )
        # rabbit specific properties
        self.max_age               = 400
        self.sex                   = random.choice([True, False])
        self.reproduction_threshold = 80
        self.reproduction_cooldown  = 0

        # gestation / reproduction state
        self.pregnant              = False
        self.gestation_duration    = 20
        self.gestation_timer       = 0
        self.birth_pending         = False

    @property
    def ready_to_reproduce(self):
        """Female rabbits cannot reproduce while pregnant."""
        if self.sex and self.pregnant:
            return False
        return (self.alive
                and self.age >= self.reproduction_age_threshold
                and self.reproduction_cooldown == 0
                and self.food_level >= self.reproduction_threshold
                and self.water_level >= self.reproduction_threshold)

    def update(self):
        """Update with gestation metabolic costs and birth timing."""
        if not self.alive:
            return

        # Gestating rabbits burn slightly more food/water
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
        # only females can get pregnant / birth offspring
        if not self.sex:
            return None

        # If gestation is complete, give birth now
        if self.birth_pending:
            self.birth_pending = False
            self.reproduction_cooldown = self.reproduction_cooldown_duration
            return Rabbit(self.position)

        # While pregnant, do not initiate mating
        if self.pregnant:
            return None

        # If already matched with mate, validate it first
        mate = self.mate_target if self._is_valid_mate(self.mate_target) else None
        if mate is None:
            mate = next((c for c in nearby_creatures
                         if isinstance(c, Rabbit)
                         and c.sex != self.sex
                         and c.alive
                         and c.ready_to_reproduce
                         and (c.mate_target is None or c.mate_target is self)), None)
            if mate is not None and mate.mate_target is None:
                self.mate_target = mate
                mate.mate_target = self

        # Initiate gestation if both partners are eligible
        if mate and self.ready_to_reproduce and mate.ready_to_reproduce:
            self.food_level -= 20
            self.water_level -= 20
            self.pregnant = True
            self.gestation_timer = self.gestation_duration
            self.reproduction_cooldown = self.reproduction_cooldown_duration
            mate.reproduction_cooldown = mate.reproduction_cooldown_duration
            self.clear_mate_target()
            mate.clear_mate_target()
            return None

        return None

    def __str__(self):
        """descibes what happens when you print a rabbit object"""
        sex_label = "F" if self.sex else "M"
        return (f"Rabbit [{sex_label}] | Age: {self.age} | "
                f"food_level: {self.food_level}/{self.food_capacity} | "
                f"water_level: {self.water_level}/{self.water_capacity} | "
                f"Position: ({self.position[0]:.1f}, {self.position[1]:.1f}) | "
                f"Alive: {self.alive}")