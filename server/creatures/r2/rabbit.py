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

    def reproduce(self):
        if self.hunger >= 80:
            self.hunger -= 20
            return Rabbit(self.position)
        return None