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

    def reproduce(self, nearby_creatures):
        # only females reproduce
        if not self.sex:
            return None

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

        if mate and self.ready_to_reproduce and mate.ready_to_reproduce:
            self.food_level               -= 20
            self.water_level               -= 20
            self.reproduction_cooldown = self.reproduction_cooldown_duration
            mate.reproduction_cooldown = mate.reproduction_cooldown_duration
            self.clear_mate_target()
            mate.clear_mate_target()
            return Rabbit(self.position)

        return None

    def __str__(self):
        """descibes what happens when you print a rabbit object"""
        sex_label = "F" if self.sex else "M"
        return (f"Rabbit [{sex_label}] | Age: {self.age} | "
                f"food_level: {self.food_level}/{self.food_capacity} | "
                f"water_level: {self.water_level}/{self.water_capacity} | "
                f"Position: ({self.position[0]:.1f}, {self.position[1]:.1f}) | "
                f"Alive: {self.alive}")