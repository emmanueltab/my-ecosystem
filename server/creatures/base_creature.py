import uuid
import random
import math

class BaseCreature:
    """
    https://www.geeksforgeeks.org/python/__init__-in-python/
    variables in the parameters may vary per creature.
    those declared with a hard value are univeral."""
    def __init__(self, position, speed, vision_range, food_capacity, water_capacity, max_age=None, name="BaseCreature", dimension="2D"):
        # Identity
        self.id           = str(uuid.uuid4()) 
        self.name         = name 
        self.dimension    = dimension
        self.alive        = True
        self.age          = 0
        self.max_age      = max_age

        # Movement
        self.position     = position
        self.speed        = speed
        self.direction    = random.uniform(0, 360)

        # Vision
        self.vision_range = vision_range

        # Resources (fundamental)
        self.food_capacity   = food_capacity
        self.food_level      = food_capacity // 2
        self.water_capacity  = water_capacity
        self.water_level     = water_capacity // 2

    def update(self):
        """Called every tick. Creatures die if food_level is depleted or max_age."""
        if self.alive:
            self.age    += 1
            self.food_level -= 0.5
            self.water_level -= 1
            if self.food_level <= 0 or self.water_level <= 0 or (self.max_age is not None and self.age >= self.max_age):
                self.die()

    def move(self, world_width, world_height):
        """Moves creature in current direction."""
        if self.alive:
            angle = math.radians(self.direction)
            dx    = self.speed * math.cos(angle)
            dy    = self.speed * math.sin(angle)
            x, y  = self.position # a tuple
            x    += dx
            y    += dy

            # Bounce off horizontal (x-axis) walls. changes direction.
            if x < 0 or x > world_width:
                self.direction = 180 - self.direction
                x = max(0, min(x, world_width))

            # Bounce off vertical (y-axis) walls. changes direction.
            if y < 0 or y > world_height:
                self.direction = 360 - self.direction
                y = max(0, min(y, world_height))

             # sets new position once calculations are finished
            self.position = (x, y) 

    def move_toward(self, target_position, world_width, world_height):
        """Moves creature toward a target position."""
        tx, ty         = target_position
        x,  y          = self.position
        # if erf at x=10 and food at x= 40, dx = 30
        dx             = tx - x
        dy             = ty - y
        # atan2 the gap (dy, dx) and finds what angle points the erf to the target.
        self.direction = math.degrees(math.atan2(dy, dx))
        self.move(world_width, world_height)

    def look(self, objects):
        """Scans for objects within vision range."""
        visible = []
        for obj in objects:
            if obj is self:
                continue
            dist = math.dist(self.position, obj.position)
            if dist <= self.vision_range:
                visible.append(obj)
        return visible

    def get_type(self):
        """Returns the type of this object for world scanning."""
        return "creature"



    def seek(self, world_objects, world_width, world_height):
        """
        Override in subclass to implement behavior.
        """
        raise NotImplementedError("Override seek() in subclass")



    def interact(self, world_object):
        """Generic interact - override in subclass."""
        dist = math.dist(self.position, world_object.position)
        if dist <= self.speed + 1 and world_object.has_resource():
            if world_object.get_type() == "food":
                self.eat(world_object.get_eaten())
            elif world_object.get_type() == "water":
                self.drink(world_object.get_drunk())

    def eat(self, amount):
        """Replenishes food_level by amount."""
        if self.alive:
            self.food_level = min(self.food_level + amount, self.food_capacity)
            print(f"{self.name} ate! food_level: {self.food_level}")

    def drink(self, amount):
        """Replenishes water_level by amount."""
        if self.alive:
            self.water_level = min(self.water_level + amount, self.water_capacity)
            print(f"{self.name} drank! water_level: {self.water_level}")

    def wander(self, world_width, world_height):
        """Random wander direction."""
        self.direction += random.uniform(-20, 20)
        self.move(world_width, world_height)


    # reproduction:
    def assign_sex(self):
        """Override in subclass."""
        raise NotImplementedError("Override in subclass")

    @property
    def ready_to_reproduce(self):
        """Override in subclass."""
        return False

    def reproduce(self, nearby_creatures):
        """Override in subclass."""
        return None

    def die(self):
        """Marks creature as dead."""
        self.alive = False
        print(f"{self.name} [{self.id[:6]}] died at age {self.age}.")

    def __str__(self):
        return (f"{self.name} | Age: {self.age} | "
                f"food_level: {self.food_level}/{self.food_capacity} | "
                f"water_level: {self.water_level}/{self.water_capacity} | "
                f"Position: ({self.position[0]:.1f}, {self.position[1]:.1f}) | "
                f"Alive: {self.alive}")