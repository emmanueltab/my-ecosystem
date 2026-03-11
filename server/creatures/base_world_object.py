import uuid

class BaseWorldObject:
    def __init__(self, position, object_type, quantity, replenish_rate):
        # Identity
        self.id             = str(uuid.uuid4())
        self.position       = position
        self.type           = object_type

        # Resource properties
        self.quantity       = quantity
        self.max_quantity   = quantity
        self.replenish_rate = replenish_rate
        self.is_depleted    = False

    def get_type(self):
        """Returns the type of world object."""
        return self.type

    def has_resource(self):
        """Returns True if resource still has quantity remaining."""
        return self.quantity > 0

    def deplete(self, amount=10):
        """Reduces quantity when a creature interacts with it."""
        if self.has_resource():
            self.quantity -= amount
            if self.quantity <= 0:
                self.quantity    = 0
                self.is_depleted = True

    def replenish(self):
        """Replenishes quantity each tick."""
        if self.is_depleted or self.quantity < self.max_quantity:
            self.quantity    = min(self.quantity + self.replenish_rate, self.max_quantity)
            self.is_depleted = False

    def __str__(self):
        return (f"{self.type} | Position: {self.position} | "
                f"Quantity: {self.quantity}/{self.max_quantity} | "
                f"Depleted: {self.is_depleted}")