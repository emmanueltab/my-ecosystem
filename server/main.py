class creature: 
    def __init__(self, name, energy): 
        self.name = name 
        self.energy = energy 

    def eat(self):
        self.energy += 10 
        print(f"{self.name} ate and gained more energy.")

    def die(self):
        print(f"{self.name} has died.")


