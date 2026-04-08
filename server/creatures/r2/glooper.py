import random
import math
from creatures.base_creature import BaseCreature
from creatures.r2.erf import erf # Needed to identify prey

class Glooper(BaseCreature):
    def __init__(self, position):
        super().__init__(
            name           = "Glooper",
            dimension      = "2D",
            position       = position,
            speed          = 1.2,        
            vision_range   = 15,       
            food_capacity  = 200,      
            water_capacity = 150
        )
        self.max_age = 500
        self.reproduction_threshold = 140
        
        # Gestation logic aligned with Erf pattern
        self.pregnant = False
        self.gestation_timer = 0
        self.gestation_duration = 50
        self.birth_pending = False

    @property
    def ready_to_reproduce(self):
        """Females cannot reproduce while pregnant."""
        if self.sex and self.pregnant:
            return False
        return (self.alive
                and self.age >= self.reproduction_age_threshold
                and self.reproduction_cooldown == 0
                and self.food_level >= self.reproduction_threshold
                and self.water_level >= self.reproduction_threshold)

    def update(self):
        """Handles aging, metabolic costs, and pregnancy timers."""
        if not self.alive:
            return

        # Higher metabolic cost when pregnant
        if self.pregnant:
            self.food_level -= 0.3
            self.water_level -= 0.3

        super().update() 

        if self.pregnant and self.alive:
            self.gestation_timer -= 1
            if self.gestation_timer <= 0:
                self.pregnant = False
                self.birth_pending = True

    def reproduce(self, nearby_creatures):
        """The actual birth and mating logic."""
        if not self.sex: # Only females handle the birth logic
            return None

        # 1. Handle Birth
        if self.birth_pending:
            self.birth_pending = False
            self.reproduction_cooldown = self.reproduction_cooldown_duration
            print(f"✨ {self.name} gave birth to a new Glooper!")
            return Glooper(self.position)

        if self.pregnant:
            return None

        # 2. Handle Mating (Finding a partner)
        mate = self.mate_target if self._is_valid_mate(self.mate_target) else None
        if mate is None:
            # Look for a male Glooper
            mate = next((c for c in nearby_creatures
                         if isinstance(c, Glooper)
                         and c.sex != self.sex
                         and c.alive
                         and c.ready_to_reproduce
                         and (c.mate_target is None or c.mate_target is self)), None)
            if mate is not None:
                self.mate_target = mate
                mate.mate_target = self

        # 3. Trigger Pregnancy
        if mate and self.ready_to_reproduce and mate.ready_to_reproduce:
            self.food_level -= 40 # Mating is taxing
            self.water_level -= 40
            self.pregnant = True
            self.gestation_timer = self.gestation_duration
            self.reproduction_cooldown = self.reproduction_cooldown_duration
            mate.reproduction_cooldown = self.reproduction_cooldown_duration
            self.clear_mate_target()
            mate.clear_mate_target()
        
        return None

    def seek(self, world_objects, world_width, world_height):
        """Predator Decision Tree: Water -> Mating -> Hunting -> Wandering."""
        visible = self.look(world_objects)
        
        # 1. Critical Thirst
        if (self.water_level / self.water_capacity) < 0.4:
            water = [o for o in visible if o.get_type() == "water"]
            if water:
                target = min(water, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target.position, world_width, world_height)
                self.interact(target)
                return

        # 2. Reproduction (Movement toward mate)
        if self.ready_to_reproduce:
            # We use the BaseCreature's seek logic for mate-finding movement
            # because it is already optimized to find and move toward mates.
            super().seek(world_objects, world_width, world_height)
            return

        # 3. Hunting (The Carnivore Part)
        if self.food_level < (self.food_capacity * 0.8):
            # Target Erfs specifically
            prey_list = [o for o in visible 
                         if isinstance(o, erf) and o.alive]
            
            if prey_list:
                target_prey = min(prey_list, key=lambda o: math.dist(self.position, o.position))
                self.move_toward(target_prey.position, world_width, world_height)
                self._attack(target_prey)
                return

        # 4. Default: Wander
        self.wander(world_width, world_height)

    def _attack(self, prey):
        """Kill the prey and regain food."""
        dist = math.dist(self.position, prey.position)
        if dist <= self.speed + 2: 
            prey.die()
            self.food_level = min(self.food_level + 80, self.food_capacity)
            print(f"🍴 {self.name} hunted an Erf! Food Level: {self.food_level}")

    def __str__(self):
        """Displays the current status and vitals of the Glooper."""
        # Identify sex for the label
        sex_label = "F" if self.sex else "M"
        
        # Check pregnancy status for the display string
        status = " [PREGNANT]" if self.pregnant else ""
        
        return (f"Glooper [{sex_label}]{status} | Age: {self.age} | "
                f"Food: {self.food_level:.1f}/{self.food_capacity} | "
                f"Water: {self.water_level:.1f}/{self.water_capacity} | "
                f"Pos: ({self.position[0]:.1f}, {self.position[1]:.1f}) | "
                f"Alive: {self.alive}")