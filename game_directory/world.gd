extends Node2D

# ── Preload creature scene ─────────────────────────
const ErfdrrtksScene = preload("res://erfdrrtks.tscn")

# ── Variables ─────────────────────────────────────
var ws : WebSocketPeer = null
var scale_factor = 8.0

var creature_dots = {}
var resource_dots = {}
var previous_positions = {}

# ── Ready ────────────────────────────────────────
func _ready():
	# Create WebSocket client
	ws = WebSocketPeer.new()
	
	# Connect to FastAPI WebSocket server
	var err = ws.connect_to_url("ws://localhost:8000/ws")
	if err != OK:
		print("WebSocket connection failed:", err)

# ── Poll WebSocket each frame ────────────────────
func _process(delta):
	if not ws:
		return

	ws.poll() # Required to process incoming/outgoing packets

	var state = ws.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		# Process all available packets
		while ws.get_available_packet_count() > 0:
			var packet = ws.get_packet()
			var data = JSON.parse_string(packet.get_string_from_utf8())
			if data.has("creatures"):
				_update_creatures(data["creatures"])
			if data.has("resources"):
				_update_resources(data["resources"])

# ── Update Creatures ─────────────────────────────
func _update_creatures(creatures):
	var alive_ids = {}
	for c in creatures:
		alive_ids[c["id"]] = true

	# Remove dead creatures
	for id in creature_dots.keys():
		if not alive_ids.has(id):
			creature_dots[id].queue_free()
			creature_dots.erase(id)
			previous_positions.erase(id)

	# Update or spawn creatures
	for c in creatures:
		var id = c["id"]
		var new_pos = Vector2(c["position"][0], c["position"][1]) * scale_factor

		if creature_dots.has(id):
			var old_pos = previous_positions.get(id, new_pos)
			var dx = new_pos.x - old_pos.x

			if dx > 0.5:
				creature_dots[id].get_node("AnimatedSprite2D").play("right")
			elif dx < -0.5:
				creature_dots[id].get_node("AnimatedSprite2D").play("left")
			else:
				creature_dots[id].get_node("AnimatedSprite2D").play("ird")

			creature_dots[id].position = new_pos
		else:
			var erf = ErfdrrtksScene.instantiate()
			erf.position = new_pos
			erf.get_node("AnimatedSprite2D").play("ird")
			add_child(erf)
			creature_dots[id] = erf

		previous_positions[id] = new_pos

# ── Update Resources ─────────────────────────────
func _update_resources(resources):
	var current_ids = {}
	for r in resources:
		current_ids[r["id"]] = true

	# Remove missing resources
	for id in resource_dots.keys():
		if not current_ids.has(id):
			resource_dots[id].queue_free()
			resource_dots.erase(id)

	# Update or spawn resources
	for r in resources:
		var id = r["id"]
		var pos = Vector2(r["position"][0], r["position"][1]) * scale_factor

		if resource_dots.has(id):
			resource_dots[id].position = pos
		else:
			var dot = ColorRect.new()
			dot.color = Color(0.2, 0.8, 0.2) if r["type"] == "food" else Color(0.2, 0.4, 1.0)
			dot.size = Vector2(10, 10)
			dot.position = pos
			add_child(dot)
			resource_dots[id] = dot
