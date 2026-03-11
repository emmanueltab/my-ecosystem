import uuid
import random
import math

class BaseCreature:
    def __init__(self, name, dimension, position, speed, vision_range, 
                 max_hunger, max_thirst, max_energy):
        # Identity
        self.id           = str(uuid.uuid4())
        self.name         = name
        self.dimension    = dimension
        self.alive        = True
        self.age          = 0

        # Reproduction
        self.sex                    = self.assign_sex()
        self.reproduction_threshold = 80
        self.reproduction_cooldown  = 0

        # Movement
        self.position     = position
        self.speed        = speed
        self.direction    = random.uniform(0, 360)

        # Vision
        self.vision_range = vision_range

        # Hunger & Thirst
        self.max_hunger   = max_hunger
        self.hunger       = max_hunger
        self.max_thirst   = max_thirst
        self.thirst       = max_thirst

        # Energy
        self.max_energy   = max_energy
        self.energy       = max_energy

    def update(self):
        """Called every tick."""
        if self.alive:
            self.age    += 1
            self.hunger -= 1
            self.thirst -= 2
            if self.hunger <= 0 or self.thirst <= 0:
                self.die()

    def move(self, world_width, world_height):
        """Moves creature in current direction."""
        if self.alive:
            angle = math.radians(self.direction)
            dx    = self.speed * math.cos(angle)
            dy    = self.speed * math.sin(angle)
            x, y  = self.position
            x    += dx
            y    += dy

            # Bounce off horizontal walls
            if x < 0 or x > world_width:
                self.direction = 180 - self.direction
                x = max(0, min(x, world_width))

            # Bounce off vertical walls
            if y < 0 or y > world_height:
                self.direction = 360 - self.direction
                y = max(0, min(y, world_height))

            self.position = (x, y)

    def move_toward(self, target_position, world_width, world_height):
        """Moves creature toward a target position."""
        tx, ty         = target_position
        x,  y          = self.position
        dx             = tx - x
        dy             = ty - y
        self.direction = math.degrees(math.atan2(dy, dx))
        self.move(world_width, world_height)

    def look(self, objects):
        """Scans for objects within vision range."""
        visible = []
        for obj in objects:
            dist = math.dist(self.position, obj.position)
            if dist <= self.vision_range:
                visible.append(obj)
        return visible

    def seek(self, world_objects, world_width, world_height):
        visible = self.look(world_objects)

        # separate food and water
        food  = [o for o in visible if o.get_type() == "food" and o.has_resource()]
        water = [o for o in visible if o.get_type() == "water" and o.has_resource()]

        # determine priority based on which stat is lower
        hunger_percent = self.hunger / self.max_hunger
        thirst_percent = self.thirst / self.max_thirst

        if hunger_percent < thirst_percent:
            # hunger is more urgent
            if food:
                target = min(food, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
            elif water and thirst_percent < 0.5:
                # no food visible but thirst is also getting low
                target = min(water, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
            else:
                self.wander(world_width, world_height)

        elif thirst_percent < hunger_percent:
            # thirst is more urgent
            if water:
                target = min(water, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
            elif food and hunger_percent < 0.5:
                # no water visible but hunger is also getting low
                target = min(food, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
            else:
                self.wander(world_width, world_height)

        else:
            # both equal — seek whichever is visible
            if food:
                target = min(food, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
            elif water:
                target = min(water, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
            else:
                self.wander(world_width, world_height)

    def interact(self, world_object):
        """Interacts with a world object if close enough."""
        dist = math.dist(self.position, world_object.position)
        if dist <= self.speed + 1:
            if world_object.get_type() == "food" and world_object.has_resource():
                amount      = world_object.get_eaten()
                self.hunger = min(self.hunger + amount, self.max_hunger)
                print(f"{self.name} ate! Hunger: {self.hunger}")
            elif world_object.get_type() == "water" and world_object.has_resource():
                amount      = world_object.get_drunk()
                self.thirst = min(self.thirst + amount, self.max_thirst)
                print(f"{self.name} drank! Thirst: {self.thirst}")

    def eat(self, food):
        """Replenishes hunger from a food source."""
        if self.alive:
            self.hunger = min(self.hunger + food.energy_value, self.max_hunger)

    def drink(self, water):
        """Replenishes thirst from a water source."""
        if self.alive:
            self.thirst = min(self.thirst + water.thirst_value, self.max_thirst)

    def wander(self, world_width, world_height):
        """Randomly changes direction and moves."""
        self.direction = random.uniform(0, 360)
        self.move(world_width, world_height)


    # reproduction:
    def assign_sex(self):
        """Override in child class to define how sex is assigned.
        Returns True for Female, False for Male by default."""
        return random.choice([True, False])

    @property
    def ready_to_reproduce(self):
        """Returns True if creature is able to reproduce."""
        return (self.alive
                and self.reproduction_cooldown == 0
                and self.hunger >= self.reproduction_threshold
                and self.thirst >= self.reproduction_threshold)

    def reproduce(self, nearby_creatures):
        """Override in child class to define reproduction behavior."""
        pass

    def die(self):
        """Marks creature as dead."""
        self.alive = False
        print(f"{self.name} [{self.id[:6]}] died at age {self.age}.")

    def __str__(self):
        return (f"{self.name} | Age: {self.age} | "
                f"Hunger: {self.hunger}/{self.max_hunger} | "
                f"Thirst: {self.thirst}/{self.max_thirst} | "
                f"Position: ({self.position[0]:.1f}, {self.position[1]:.1f}) | "
                f"Alive: {self.alive}")