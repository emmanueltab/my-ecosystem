extends CanvasLayer

# Nodes we want to update
@onready var run_label = $PanelContainer/VBoxContainer/RunName
@onready var pop_label = $PanelContainer/VBoxContainer/Population
@onready var tick_label = $PanelContainer/VBoxContainer/TickCount
@onready var fps_label = $PanelContainer/VBoxContainer/FPS
@onready var birth_rate_label = $PanelContainer/VBoxContainer/BirthRate
@onready var ratio_label = $PanelContainer/VBoxContainer/MaleFemaleRatio

func _ready():
	# Start hidden if you want the "F3" toggle feel
	$PanelContainer.visible = true 

func _input(event):
	# Toggle visibility with the 'F3' key (or any key you map)
	if event is InputEventKey and event.pressed and event.keycode == KEY_F3:
		$PanelContainer.visible = !$PanelContainer.visible

# This function gets called whenever a WebSocket packet arrives
func update_overlay(data: Dictionary):
	pop_label.text = "POP: " + str(data.get("population", 0))
	tick_label.text = "TICK: " + str(data.get("tick", 0))
	
	# Internal Godot stat
	fps_label.text = "FPS: " + str(Engine.get_frames_per_second())
	
	# Calculate male/female ratio
	var creatures = data.get("creatures", [])
	var males = 0
	var females = 0
	for c in creatures:
		if c.get("sex") == "M":
			males += 1
		elif c.get("sex") == "F":
			females += 1
	var ratio = "N/A"
	if females > 0 or males > 0:
		ratio = str(males) + ":" + str(females)
	ratio_label.text = "M:F Ratio: " + ratio
	
	# Birth rate: placeholder, as it requires tracking over time
	# You could add a birth counter in the simulation and send it
	birth_rate_label.text = "Birth Rate: TBD"
