extends Node2D

var http_creatures = HTTPRequest.new()
var http_resources = HTTPRequest.new()
var scale_factor = 8.0
var timer = Timer.new()

func _ready():
	# Set up HTTP nodes for creatures and resources separately
	# so they can make requests at the same time
	add_child(http_creatures)
	add_child(http_resources)
	http_creatures.request_completed.connect(_on_creatures_completed)
	http_resources.request_completed.connect(_on_resources_completed)

	# Set up a timer to fetch data every 0.5 seconds
	add_child(timer)
	timer.wait_time = 0.5
	timer.timeout.connect(_fetch_all)
	timer.start()

	# Fetch immediately on load
	_fetch_all()

func _fetch_all():
	# Only make a new request if the previous one is finished
	if http_creatures.get_http_client_status() == 0:
		http_creatures.request("http://localhost:8000/creatures")
	if http_resources.get_http_client_status() == 0:
		http_resources.request("http://localhost:8000/resources")

func _on_creatures_completed(result, response_code, headers, body):
	# Clear old creature dots
	for child in get_children():
		if child is ColorRect and child.name.begins_with("creature"):
			child.queue_free()

	var creatures = JSON.parse_string(body.get_string_from_utf8())
	for creature in creatures:
		var dot = ColorRect.new()
		dot.name = "creature_" + creature["id"]
		# White for female, light blue for male
		dot.color = Color.WHITE if creature["sex"] == "F" else Color(0.5, 0.8, 1.0)
		dot.size = Vector2(6, 6)
		var x = creature["position"][0] * scale_factor
		var y = creature["position"][1] * scale_factor
		dot.position = Vector2(x, y)
		add_child(dot)

func _on_resources_completed(result, response_code, headers, body):
	# Clear old resource dots
	for child in get_children():
		if child is ColorRect and child.name.begins_with("resource"):
			child.queue_free()

	var resources = JSON.parse_string(body.get_string_from_utf8())
	for resource in resources:
		var dot = ColorRect.new()
		dot.name = "resource_" + resource["id"]
		# Green for food, blue for water
		dot.color = Color(0.2, 0.8, 0.2) if resource["type"] == "food" else Color(0.2, 0.4, 1.0)
		dot.size = Vector2(10, 10)
		var x = resource["position"][0] * scale_factor
		var y = resource["position"][1] * scale_factor
		dot.position = Vector2(x, y)
		add_child(dot)
