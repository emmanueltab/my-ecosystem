from creatures.base_world_object import BaseWorldObject


class WaterSource(BaseWorldObject):
    # Set much higher defaults for a "Lake" feel
    def __init__(self, position, thirst_value=30, quantity=1000, replenish_rate=5):
        super().__init__(
            position       = position,
            object_type    = "water",
            quantity       = quantity, # 1000 is 10x your previous puddles
            replenish_rate = replenish_rate
        )
        self.thirst_value = thirst_value

    def get_drunk(self, amount=15): # Creatures take a bigger gulp
        """Called when a creature drinks from this source."""
        # Logic: If the lake has 1000 units, it can support many drinks 
        # before needing to replenish.
        self.deplete(amount)
        return self.thirst_value