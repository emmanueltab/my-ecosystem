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
            max_hunger   = 100,
            max_thirst   = 100,
            max_energy   = 100
        )
        # rabbit specific properties
        self.max_age               = 200
        self.sex                   = random.choice([True, False])
        self.reproduction_threshold = 80
        self.reproduction_cooldown  = 0

    def reproduce(self, nearby_creatures):
        # only females reproduce
        if not self.sex:
            return None

        # find a nearby ready male
        mate = next((c for c in nearby_creatures
                     if isinstance(c, Rabbit)
                     and c.sex != self.sex
                     and c.alive
                     and c.ready_to_reproduce), None)

        if mate and self.ready_to_reproduce:
            self.hunger               -= 20
            self.thirst               -= 20
            self.reproduction_cooldown = 10
            mate.reproduction_cooldown = 10
            return Rabbit(self.position)

        return None

    def __str__(self):
        sex_label = "F" if self.sex else "M"
        return (f"Rabbit [{sex_label}] | Age: {self.age} | "
                f"Hunger: {self.hunger}/{self.max_hunger} | "
                f"Thirst: {self.thirst}/{self.max_thirst} | "
                f"Position: ({self.position[0]:.1f}, {self.position[1]:.1f}) | "
                f"Alive: {self.alive}")