import random
from creatures.base_creature import BaseCreature

class Glooper(BaseCreature):
    """A slow-moving, hardy creature that can survive on lower food/water levels but reproduces less frequently.
    They are the natural predators of rabbits."""
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
        self.reproduction_threshold = 120
        self.reproduction_cooldown  = 0

    @property
    def ready_to_reproduce(self):
        return (self.alive
                and self.age >= self.reproduction_age_threshold
                and self.reproduction_cooldown == 0
                and self.food_level >= self.reproduction_threshold
                and self.water_level >= self.reproduction_threshold)