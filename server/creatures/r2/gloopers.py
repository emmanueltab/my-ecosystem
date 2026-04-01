import random
from creatures.base_creature import BaseCreature

class Glooper(BaseCreature):
    """A slow-moving, hardy creature that can survive on lower food/water levels but reproduces less frequently.
    They are the natural predators of erf."""
    def __init__(self, position):
        super().__init__(
            name         = "Glooper",
            dimension    = "2D",
            position     = position,
            speed        = 1,
            vision_range = 5,
            food_capacity   = 150,
            water_capacity   = 150,
        )
        # glooper specific properties
        self.max_age               = 500
        self.sex                  = random.choice([True, False])
        self.reproduction_threshold = 120
        self.reproduction_cooldown  = 0

        # gestation / reproduction state
        self.pregnant              = False
        self.gestation_duration    = 40
        self.gestation_timer       = 0
        self.birth_pending         = False

    @property
    def ready_to_reproduce(self):
        """Female gloopers cannot reproduce while pregnant."""
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