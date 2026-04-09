extends Node2D

const ErfdrrtksScene = preload("res://erfdrrtks.tscn")
const FruitBushScene = preload("res://fruit_bush.tscn")
const WaterSourceScene = preload("res://water_source.tscn")

var ws : WebSocketPeer = WebSocketPeer.new()
var scale_factor = 8.0

# Dictionaries to store nodes and their intended targets
var creature_dots = {}
var creature_targets = {} 
var resource_dots = {}

# Smoothing speed: higher = snappier, lower = smoother/slower
var lerp_weight = 10.0 

func _ready():
	"""Initializes the script by attempting to connect to the local Python WebSocket server."""
	ws.connect_to_url("ws://localhost:8000/ws")

func _process(delta):
	ws.poll()
	var state = ws.get_ready_state()
	
	if state == WebSocketPeer.STATE_OPEN:
		while ws.get_available_packet_count() > 0:
			var packet = ws.get_packet()
			var raw_data = packet.get_string_from_utf8()
			
			var data = JSON.parse_string(raw_data)
			if typeof(data) != TYPE_DICTIONARY:
				continue
				
			if data.has("creatures"):
				_update_creatures(data["creatures"])
			if data.has("resources"):
				_update_resources(data["resources"])
			
			$HUD.update_overlay(data)

	# Run the visual smoothing every frame
	_interpolate_entities(delta)

func _interpolate_entities(delta):
	for id in creature_dots.keys():
		var creature = creature_dots[id]
		var target = creature_targets.get(id, creature.position)
		
		creature.position = creature.position.lerp(target, lerp_weight * delta)
		
		var dx = target.x - creature.position.x
		var sprite = creature.get_node("AnimatedSprite2D")
		
		if abs(dx) > 0.1: 
			if dx > 0:
				sprite.play("right")
			else:
				sprite.play("left")
		else:
			sprite.play("idle")

func _update_creatures(creatures_data: Array):
	var current_ids = []
	for c in creatures_data:
		var id = str(c["id"])
		var species = c.get("species", "erf") # Default to erf if not specified
		current_ids.append(id)
		var target_pos = Vector2(c["pos"][0], c["pos"][1]) * scale_factor
		
		if not creature_dots.has(id):
			# Currently reusing Erf scene for both species as requested
			var creature = ErfdrrtksScene.instantiate()
			creature.position = target_pos 
			add_child(creature)
			creature_dots[id] = creature
			
			var sprite = creature.get_node("AnimatedSprite2D")
			var sex = c.get("sex")
			
			# Logic for Glooper Colors (Black/Green)
			if species == "Glooper" or species == "glooper":
				if sex == "M":
					sprite.self_modulate = Color(0.1, 0.1, 0.1, 1.0) # Black
				else:
					sprite.self_modulate = Color(0.0, 0.8, 0.0, 1.0) # Green
			
			# Logic for Erf Colors (Blue/Pink)
			else:
				if sex == "M":
					sprite.self_modulate = Color(0.02, 0.0, 0.769, 1.0) # Blue
				else:
					sprite.self_modulate = Color(1.0, 0.414, 0.918, 1.0) # Pink
					
			sprite.play("idle")
		
		creature_targets[id] = target_pos

	# Cleanup dead creatures
	for id in creature_dots.keys():
		if not id in current_ids:
			var dead_creature = creature_dots[id]
			creature_dots.erase(id)
			creature_targets.erase(id)
			
			var sprite = dead_creature.get_node("AnimatedSprite2D")
			sprite.self_modulate = Color.WHITE 
			sprite.play("explode")
			sprite.animation_finished.connect(func(): dead_creature.queue_free(), CONNECT_ONE_SHOT)

func _update_resources(resources_data: Array):
	var current_ids = []
	for r in resources_data:
		var id = str(r["id"])
		current_ids.append(id)
		var pos = Vector2(r["pos"][0], r["pos"][1]) * scale_factor
		
		if not resource_dots.has(id):
			if r["type"] == "food":
				var bush = FruitBushScene.instantiate()
				add_child(bush)
				resource_dots[id] = bush
			else:
				var water = WaterSourceScene.instantiate()
				add_child(water)
				resource_dots[id] = water
				
				# IMPLEMENTATION: Play the default animation
				# Check if the node exists before playing to avoid errors
				if water.has_node("AnimatedSprite2D"):
					water.get_node("AnimatedSprite2D").play("default")
		
		var node = resource_dots[id]
		if r["type"] == "water":
			node.position = pos 
		else:
			node.position = pos - Vector2(5, 5)

	# Cleanup
	for id in resource_dots.keys():
		if not id in current_ids:
			resource_dots[id].queue_free()
			resource_dots.erase(id)
