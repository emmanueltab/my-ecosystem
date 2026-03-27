import uuid
import random
import math

class BaseCreature:
    """
    https://www.geeksforgeeks.org/python/__init__-in-python/
    variables in the parameters may vary per creature.
    those declared with a hard value are univeral."""
    def __init__(self, name, dimension, position, speed, vision_range, 
                 food_capacity, water_capacity):
        # Identity
        self.id           = str(uuid.uuid4()) 
        self.name         = name 
        self.dimension    = dimension
        self.alive        = True
        self.age          = 0

        # Reproduction
        # value is hardcoded. same for every creature:
        self.sex                    = self.assign_sex()
        self.reproduction_threshold = 80
        self.reproduction_cooldown  = 0

        # Movement
        self.position     = position
        self.speed        = speed
        # direction is random when the creature ihe first created
        self.direction    = random.uniform(0, 360)

        # NEW: Idle/Wander Logic
        self.is_idling = False
        self.idle_timer = 0
        # Vision
        self.vision_range = vision_range

        # food_level & water_level
        # value comes from the parameter. might vary per creature:
        self.food_capacity   = food_capacity
        self.food_level      = food_capacity
        self.water_capacity  = water_capacity
        self.water_level     = water_capacity

    def update(self):
        """Called every tick. Creatures die if food_level is depleted or low age"""
        if self.alive:
            self.age    += 1
            self.food_level -= 0.5
            self.water_level -= 1
            if self.food_level <= 0 or self.water_level <= 0:
                self.die()
            if self.max_age is not None and self.age >= self.max_age:
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
        # if rabbit at x=10 and food at x= 40, dx = 30
        dx             = tx - x
        dy             = ty - y
        # atan2 the gap (dy, dx) and finds what angle points the rabbit to the target.
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
        """
        Decision Tree: 
        1. if ready to reproduce, find a mate.
        2. Otherwise, check if thirst or hunger is more urgent.
        """
        # --- 1. PRIORITY: REPRODUCTION ---

        # objects that are within the creatures vision_range. 
        visible = self.look(world_objects)

        # separate food and water
        food  = [o for o in visible if o.get_type() == "food" and o.has_resource()]
        water = [o for o in visible if o.get_type() == "water" and o.has_resource()]

        # determine priority based on which stat is lower
        hunger_percent = self.food_level / self.food_capacity
        thirst_percent = self.water_level / self.water_capacity


        if hunger_percent < thirst_percent:
            # food_level is more urgent
            if food:
                self.is_idling = False
                target = min(food, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
            elif water and thirst_percent < 0.5:
                # no food visible but water_level is also getting low
                target = min(water, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
            else:
                self.wander(world_width, world_height)

        elif thirst_percent < hunger_percent:
            # water_level is more urgent
            if water:
                target = min(water, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
            elif food and hunger_percent < 0.5:
                # no water visible but food_level is also getting low
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
        # checks the object type. 
        # get_type(),  has_resource(), and gets... are defined in base_world_object.py
        if dist <= self.speed + 1:
            if world_object.get_type() == "food" and world_object.has_resource():
                amount      = world_object.get_eaten()
                self.food_level = min(self.food_level + amount, self.food_capacity)
                print(f"{self.name} ate! food_level: {self.food_level}")

            elif world_object.get_type() == "water" and world_object.has_resource():
                amount      = world_object.get_drunk()
                self.water_level = min(self.water_level + amount, self.water_capacity)
                print(f"{self.name} drank! water_level: {self.water_level}")

    def eat(self, food):
        """Replenishes food_level from a food source."""
        if self.alive:
            self.food_level = min(self.food_level + food.energy_value, self.food_capacity)

    def drink(self, water):
        """Replenishes water_level from a water source."""
        if self.alive:
            self.water_level = min(self.water_level + water.thirst_value, self.water_capacity)

    def wander(self, world_width, world_height):
        """Randomly decides to move or stay still."""
        # If we are currently idling, count down
        if self.is_idling:
            self.idle_timer -= 1
            if self.idle_timer <= 0:
                self.is_idling = False
            return # Don't move while idling!

        # 10% chance to start idling for 2-5 ticks
        if random.random() < 0.10:
            self.is_idling = True
            self.idle_timer = random.randint(2, 5)
            return

        # Otherwise, move as normal
        # Suggestion: Only change direction slightly so they don't jitter
        self.direction += random.uniform(-20, 20) 
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
                and self.food_level >= self.reproduction_threshold
                and self.water_level >= self.reproduction_threshold)

    def reproduce(self, nearby_creatures):
        """Override in child class to define reproduction behavior."""
        pass

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