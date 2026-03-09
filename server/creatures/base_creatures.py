class BaseCreature: 
    def __init__(self, name, age, energy, speed, max_energy, position, dimension):
        self.name = name
        self.age = 0
        self.energy = energy
        self.max_energy = max_energy
        self.speed = speed
        self.position = position
        self.dimension = dimension
        self.alive = True

    def update(self):
         """Called every tick. Ages the creature and drains energy."""
         if self.alive:
            self.age += 1 
            self.energy -= 1 
            if self.energy <= 0:
                self.die()

    def move(self, new_position):
         """Moves the creature to a new position."""
         if self.alive:
            self.position = new_position

    def eat(self, amount):
        """Gains energy from eating, capped at max_energy"""
        if self.alive:
            self.energy = min(self.energy + amount, self.max_energy)

    def reproduce(self):
        """Override in child class to define reproduction behavior."""
        pass

    def die(self):
        """Override in child class to define reproduction behavior."""
        self.alive = False
        print(f"{self.name} has died at age {self.age}.")

    def __str__(self):
        """Returns a readable summary of the creature."""
        return (f"{self.name} | Dimension: {self.dimension} | "
                f"Age: {self.age} | Energy: {self.energy}/{self.max_energy} | "
                f"Position: {self.position} | Alive: {self.alive}")
