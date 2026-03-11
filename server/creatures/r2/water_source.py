from creatures.base_world_object import BaseWorldObject

class WaterSource(BaseWorldObject):
    def __init__(self, position, thirst_value=20, quantity=100, replenish_rate=8):
        super().__init__(
            position       = position,
            object_type    = "water",
            quantity       = quantity,
            replenish_rate = replenish_rate
        )
        self.thirst_value = thirst_value

    def get_drunk(self, amount=10):
        """Called when a creature drinks from this source."""
        self.deplete(amount)
        return self.thirst_value

    def __str__(self):
        return (f"WaterSource | Position: {self.position} | "
                f"Quantity: {self.quantity}/{self.max_quantity} | "
                f"Depleted: {self.is_depleted}")