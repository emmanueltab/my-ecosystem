extends Node2D

const ErfdrrtksScene = preload("res://erfdrrtks.tscn")
const FruitBushScene = preload("res://fruit_bush.tscn")

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
	"""
	Main loop running every frame. Polls the WebSocket for new data packets from Python,
	triggers entity updates if data is received, and handles frame-by-frame smoothing.
	"""
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

	# Run the visual smoothing every frame
	_interpolate_entities(delta)

func _interpolate_entities(delta):
	"""
	Calculates the smooth transition between a creature's current visual position 
	and its target position from the server. Also updates animations based on move direction.
	"""
	for id in creature_dots.keys():
		var erf = creature_dots[id]
		var target = creature_targets.get(id, erf.position)
		
		# Move a percentage of the distance to the target for smooth sliding
		erf.position = erf.position.lerp(target, lerp_weight * delta)
		
		var dx = target.x - erf.position.x
		var sprite = erf.get_node("AnimatedSprite2D")
		
		if abs(dx) > 0.1: 
			if dx > 0:
				sprite.play("right")
			else:
				sprite.play("left")
		else:
			sprite.play("idle")

func _update_creatures(creatures_data: Array):
	"""
	Handles the 'lifecycle' of Erfs: instantiates new nodes for births, 
	sets target positions for movement, assigns colors based on sex, 
	and removes nodes for creatures that have died.
	"""
	var current_ids = []
	for c in creatures_data:
		var id = str(c["id"])
		current_ids.append(id)
		var target_pos = Vector2(c["pos"][0], c["pos"][1]) * scale_factor
		
		if not creature_dots.has(id):
			var erf = ErfdrrtksScene.instantiate()
			erf.position = target_pos 
			add_child(erf)
			creature_dots[id] = erf
			
			# Visual distinction: Blue for Male, Pink/Rose for Female
			var sprite = erf.get_node("AnimatedSprite2D")
			if c.get("sex") == "M":
				sprite.self_modulate = Color(0.02, 0.0, 0.769, 1.0)
			else:
				sprite.self_modulate = Color(1.0, 0.414, 0.918, 1.0)
				
			sprite.play("idle")
		
		creature_targets[id] = target_pos

	# Cleanup dead creatures
	for id in creature_dots.keys():
		if not id in current_ids:
			var dead_erf = creature_dots[id]
			
			# Remove from tracking immediately
			creature_dots.erase(id)
			creature_targets.erase(id)
			
			# Play animation and auto-delete when done
			var sprite = dead_erf.get_node("AnimatedSprite2D")
			sprite.self_modulate = Color.WHITE # Clear sex-based tint
			sprite.play("explode")
			
			# This one line replaces the entire extra function:
			sprite.animation_finished.connect(func(): dead_erf.queue_free(), CONNECT_ONE_SHOT)

func _update_resources(resources_data: Array):
	"""
	Updates food and water sources. Handles dynamic scaling for water (lakes),
	colors resource types differently, and centers them on their simulation coordinates.
	"""
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
				var dot = ColorRect.new()
				add_child(dot)
				resource_dots[id] = dot
				dot.size = Vector2(40, 40)
				dot.color = Color(0.1, 0.3, 0.8, 0.7)
		
		var dot = resource_dots[id]
		if r["type"] == "water":
			# Lake shrinks as quantity depletes
			var lake_size = clamp(r.get("qty", 100) * 0.4, 15, 60)
			dot.size = Vector2(lake_size, lake_size)
			dot.position = pos - (dot.size / 2.0)
		else:
			dot.position = pos - Vector2(5, 5)

	# Cleanup depleted/removed resources
	for id in resource_dots.keys():
		if not id in current_ids:
			resource_dots[id].queue_free()
			resource_dots.erase(id)
