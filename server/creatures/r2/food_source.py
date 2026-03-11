from creatures.base_world_object import BaseWorldObject

class FoodSource(BaseWorldObject):
    def __init__(self, position, energy_value=20, quantity=100, replenish_rate=5):
        super().__init__(
            position       = position,
            object_type    = "food",
            quantity       = quantity,
            replenish_rate = replenish_rate
        )
        self.energy_value = energy_value

    def get_eaten(self, amount=10):
        """Called when a creature eats from this source."""
        self.deplete(amount)
        return self.energy_value

    def __str__(self):
        return (f"FoodSource | Position: {self.position} | "
                f"Quantity: {self.quantity}/{self.max_quantity} | "
                f"Depleted: {self.is_depleted}")