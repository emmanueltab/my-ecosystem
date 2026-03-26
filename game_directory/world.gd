extends Node2D

const ErfdrrtksScene = preload("res://erfdrrtks.tscn")

var ws : WebSocketPeer = WebSocketPeer.new()
var scale_factor = 8.0

# Dictionaries to store nodes and their intended targets
var creature_dots = {}
var creature_targets = {} # New: Stores the target Vector2 from server
var resource_dots = {}

# Smoothing speed: higher = snappier, lower = smoother/slower
# Since your TICK_RATE is 0.5, a weight around 5.0 - 10.0 usually looks good.
var lerp_weight = 10.0 

func _ready():
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

	# NEW: Smoothing Loop
	# This runs every frame (60+ times per second)
	_interpolate_entities(delta)

func _interpolate_entities(delta):
	for id in creature_dots.keys():
		var erf = creature_dots[id]
		var target = creature_targets.get(id, erf.position)
		
		# Linear Interpolation: Move a percentage of the distance to the target
		# We use lerp to smoothly transition the position
		erf.position = erf.position.lerp(target, lerp_weight * delta)
		
		# Update animations based on movement direction during interpolation
		var dx = target.x - erf.position.x
		var sprite = erf.get_node("AnimatedSprite2D")
		if abs(dx) > 0.1: # Only change if moving significantly
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
		current_ids.append(id)
		var target_pos = Vector2(c["pos"][0], c["pos"][1]) * scale_factor
		
		if not creature_dots.has(id):
			var erf = ErfdrrtksScene.instantiate()
			# Spawn exactly at position first time so they don't slide in from (0,0)
			erf.position = target_pos 
			add_child(erf)
			creature_dots[id] = erf
			erf.get_node("AnimatedSprite2D").play("ird")
		
		# Store the target instead of setting position directly
		creature_targets[id] = target_pos

	# Cleanup
	for id in creature_dots.keys():
		if not id in current_ids:
			creature_dots[id].queue_free()
			creature_dots.erase(id)
			creature_targets.erase(id)

func _update_resources(resources_data: Array):
	var current_ids = []
	for r in resources_data:
		var id = str(r["id"])
		current_ids.append(id)
		var pos = Vector2(r["pos"][0], r["pos"][1]) * scale_factor
		
		if not resource_dots.has(id):
			var dot = ColorRect.new()
			dot.size = Vector2(10, 10)
			dot.color = Color.GREEN if r["type"] == "food" else Color.BLUE
			add_child(dot)
			resource_dots[id] = dot
		
		# Resources can stay snappy since they don't "walk"
		resource_dots[id].position = pos

	for id in resource_dots.keys():
		if not id in current_ids:
			resource_dots[id].queue_free()
			resource_dots.erase(id)
