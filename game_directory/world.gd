extends Node2D

const ErfdrrtksScene = preload("res://erfdrrtks.tscn")

var http_creatures = HTTPRequest.new()
var http_resources = HTTPRequest.new()
var scale_factor = 8.0
var timer = Timer.new()

# Track existing creatures and resources by id
var creature_dots = {}
var resource_dots = {}

# Track previous positions to determine movement direction
var previous_positions = {}

func _ready():
	add_child(http_creatures)
	add_child(http_resources)
	http_creatures.request_completed.connect(_on_creatures_completed)
	http_resources.request_completed.connect(_on_resources_completed)
	add_child(timer)
	timer.wait_time = 0.5
	timer.timeout.connect(_fetch_all)
	timer.start()
	_fetch_all()

func _fetch_all():
	if http_creatures.get_http_client_status() == 0:
		http_creatures.request("http://localhost:8000/creatures")
	if http_resources.get_http_client_status() == 0:
		http_resources.request("http://localhost:8000/resources")

func _on_creatures_completed(result, response_code, headers, body):
	var creatures = JSON.parse_string(body.get_string_from_utf8())

	# Track which ids are still alive this tick
	var alive_ids = {}
	for creature in creatures:
		alive_ids[creature["id"]] = true

	# Remove instances for creatures no longer in the response
	for id in creature_dots.keys():
		if not alive_ids.has(id):
			creature_dots[id].queue_free()
			creature_dots.erase(id)
			previous_positions.erase(id)

	# Update or create instances for current creatures
	for creature in creatures:
		var id = creature["id"]
		var x = creature["position"][0] * scale_factor
		var y = creature["position"][1] * scale_factor
		var new_pos = Vector2(x, y)

		if creature_dots.has(id):
			var old_pos = previous_positions.get(id, new_pos)
			var dx = new_pos.x - old_pos.x

			# Pick animation based on movement direction
			if dx > 0.5:
				creature_dots[id].get_node("AnimatedSprite2D").play("right")
			elif dx < -0.5:
				creature_dots[id].get_node("AnimatedSprite2D").play("left")
			else:
				creature_dots[id].get_node("AnimatedSprite2D").play("ird")

			creature_dots[id].position = new_pos
		else:
			# Spawn a new Erfdrrtks instance
			var erf = ErfdrrtksScene.instantiate()
			erf.position = new_pos
			erf.get_node("AnimatedSprite2D").play("ird")
			add_child(erf)
			creature_dots[id] = erf

		previous_positions[id] = new_pos

func _on_resources_completed(result, response_code, headers, body):
	var resources = JSON.parse_string(body.get_string_from_utf8())

	# Track which ids exist this tick
	var current_ids = {}
	for resource in resources:
		current_ids[resource["id"]] = true

	# Remove dots for resources no longer in response
	for id in resource_dots.keys():
		if not current_ids.has(id):
			resource_dots[id].queue_free()
			resource_dots.erase(id)

	# Update or create dots for current resources
	for resource in resources:
		var id = resource["id"]
		var x = resource["position"][0] * scale_factor
		var y = resource["position"][1] * scale_factor
		if resource_dots.has(id):
			resource_dots[id].position = Vector2(x, y)
		else:
			var dot = ColorRect.new()
			dot.color = Color(0.2, 0.8, 0.2) if resource["type"] == "food" else Color(0.2, 0.4, 1.0)
			dot.size = Vector2(10, 10)
			dot.position = Vector2(x, y)
			add_child(dot)
			resource_dots[id] = dot
