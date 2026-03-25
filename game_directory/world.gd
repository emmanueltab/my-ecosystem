extends Node2D

const ErfdrrtksScene = preload("res://erfdrrtks.tscn")

var ws : WebSocketPeer = WebSocketPeer.new()
var scale_factor = 8.0
var creature_dots = {}
var resource_dots = {}
var previous_positions = {}

func _ready():
	ws.connect_to_url("ws://localhost:8000/ws")

func _process(delta):
	ws.poll()
	var state = ws.get_ready_state()
	
	if state == WebSocketPeer.STATE_OPEN:
		while ws.get_available_packet_count() > 0:
			var packet = ws.get_packet()
			var raw_data = packet.get_string_from_utf8()
			
			# FIX: Proper Godot 4 JSON parsing
			var data = JSON.parse_string(raw_data)
			if typeof(data) != TYPE_DICTIONARY:
				continue
				
			if data.has("creatures"):
				_update_creatures(data["creatures"])
			if data.has("resources"):
				_update_resources(data["resources"])

func _update_creatures(creatures_data: Array):
	var current_ids = []
	for c in creatures_data:
		var id = str(c["id"])
		current_ids.append(id)
		var pos = Vector2(c["pos"][0], c["pos"][1]) * scale_factor
		
		if not creature_dots.has(id):
			var erf = ErfdrrtksScene.instantiate()
			add_child(erf)
			creature_dots[id] = erf
			erf.get_node("AnimatedSprite2D").play("ird")
		
		# Animation Logic
		var old_pos = creature_dots[id].position
		var dx = pos.x - old_pos.x
		var sprite = creature_dots[id].get_node("AnimatedSprite2D")
		
		if dx > 0.5: sprite.play("right")
		elif dx < -0.5: sprite.play("left")
		else: sprite.play("ird")
		
		creature_dots[id].position = pos

	# Cleanup dead creatures
	for id in creature_dots.keys():
		if not id in current_ids:
			creature_dots[id].queue_free()
			creature_dots.erase(id)

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
		
		resource_dots[id].position = pos

	for id in resource_dots.keys():
		if not id in current_ids:
			resource_dots[id].queue_free()
			resource_dots.erase(id)