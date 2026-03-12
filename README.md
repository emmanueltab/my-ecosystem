# 🌿 Ecosystem Simulation & Analytics Platform

A continuously running server-based simulation of a living ecosystem populated by autonomous, mathematically-themed entities. The simulation can be controlled in real time — run, paused, reset, and configured to adjust environmental settings or introduce new objects and entities at any time. A built-in creature builder allows new entity types to be designed and dropped into the ecosystem while the simulation is actively running. Creatures are mathematically inspired — exhibiting behaviors such as parametric movement, spiral navigation, exponential reproduction, and vector-based pathfinding. The simulation exists in a dual-dimension environment where 3D creatures navigate freely in XYZ space while 2D creatures are locked to a flat plane, producing unique cross-dimensional interactions and emergent behavior. All simulation data is continuously logged to a database, powering live analytics dashboards and serving as the foundation for ongoing data science experiments, statistical analysis, and research reports.

---

## 🌐 Live Demo

> 🔗 Coming soon — the simulation will be publicly accessible via browser once deployed.

Once live, you will be able to:
- Watch the simulation running in real time from any browser
- View live population charts and ecosystem analytics
- No installation required

---

## 🔓 Open Source

This project is free and open source. You are welcome to clone it, run your own simulation locally, modify the rules, introduce new creatures, and experiment with your own ecosystems.

```bash
git clone https://github.com/emmanueltab/my-ecosystem.git
cd my-ecosystem
```

See the **Local Setup** section below to get started.

---

## 🏗️ Architecture

```
┌──────────────────┐        ┌───────────────────┐
│  PYTHON SERVER   │◄──────►│     GODOT 4       │
│  FastAPI+SQLite  │        │  Visual World     │
│                  │        │  Agents moving    │
│  The Brain       │        │  in 2D/3D space   │
└────────┬─────────┘        └───────────────────┘
         │
         ▼
┌──────────────────┐
│  GRAFANA         │
│  Live Charts     │
│  Stats & Metrics │
└──────────────────┘
```

- **Python Server** — the single source of truth. Runs the simulation, stores all data in SQLite, and exposes API endpoints for control
- **Godot 4** — visual client that renders the ecosystem in real time via WebSocket connection to the server
- **Grafana** — reads directly from the SQLite database and renders live analytics panels accessible from any browser

---

## 🗂️ Repository Structure

```
my-ecosystem/
├── server/              # Python simulation engine and API
│   ├── main.py
│   ├── simulation.py
│   ├── database.py
│   ├── creatures/
│   │   ├── base_creature.py
│   │   ├── base_world_object.py
│   │   ├── r1/               # 1D creatures
│   │   ├── r2/               # 2D creatures
│   │   └── r3/               # 3D creatures
│   └── data/
│       └── ecosystem.db      # SQLite database
├── game_directory/      # Godot 4 visual world
├── dashboard/           # Grafana configuration
├── reports/             # Data analysis and experiment findings
├── README.md
└── .gitignore
```

---

## 🛠️ Tools & Libraries

**Tools:**
- **Python** — primary programming language
- **Godot 4** — game engine for the visual ecosystem
- **Grafana** — standalone dashboard for real-time monitoring

**Python Libraries:**
- **FastAPI** — API server
- **Uvicorn** — runs the FastAPI server
- **SQLite3** — database management, built into Python
- **Pandas** — data analysis and report generation
- **Matplotlib** — generating charts and visualizations

---

## 💻 Local Setup

**Requirements:**
- Python 3.11+
- Godot 4
- Grafana

**Install Python dependencies:**
```bash
pip install matplotlib pyqt5 fastapi uvicorn pandas --break-system-packages
```

**Run the simulation:**
```bash
cd server
python main.py
```

**Access Grafana dashboard:**
```
http://localhost:3000
```

---

## ☁️ Deployment

The simulation is designed to run continuously on a server and be accessible from anywhere:

- **Grafana dashboard** — accessible from any browser on the network
- **Godot visual world** — exported as a web app, viewable in any browser
- **FastAPI** — exposes control endpoints accessible via browser or SSH

**Recommended hosting:**
- Oracle Cloud (permanently free tier)
- DigitalOcean (~$4/month)
- Any Linux VPS

Once deployed, the simulation runs 24/7 in the background. Check in on it from anywhere throughout the week.

---

## 🚀 Build Phases

| Phase | What Gets Built | Difficulty | Est. Time |
|-------|----------------|------------|-----------|
| 1 | Python simulation engine | ⭐⭐ Medium | 1-2 weeks |
| 2 | SQLite persistence | ⭐ Easy | 2-3 days |
| 3 | FastAPI server | ⭐⭐ Medium | 1 week |
| 4 | Godot visual world | ⭐⭐⭐ Hard | 2-4 weeks |
| 5 | Grafana dashboard | ⭐⭐ Medium | 3-5 days |
| 6 | Cloud deployment | ⭐⭐ Medium | 3-5 days |
| 7 | Data analysis & reports | ⭐⭐ Medium | Ongoing |

**Total estimate:** 2-3 months working casually, or 4-6 weeks if focused.

---

## 📊 Skills Developed

**Programming**
- Python OOP (classes, methods, inheritance)
- GDScript (Godot's scripting language)
- API design and development (FastAPI)
- Client-server communication (HTTP, JSON, WebSockets)

**Data & Databases**
- SQL basics (SQLite)
- Data cleaning and analysis (Pandas)
- Data visualization (Matplotlib, Grafana)
- Time-series data interpretation

**Software Engineering**
- Version control (Git & GitHub)
- Cloud deployment and server management
- Project structure and organization
- Debugging and testing
- Documentation writing

**Simulation & Modeling**
- Agent-based modeling concepts
- Rule-based system design
- Emergent behavior analysis
- Experimental thinking (changing variables, measuring impact)

**Soft Skills**
- Analytical thinking
- Storytelling with data
- Technical documentation
- Project planning and phased execution

---

## 📈 Status
🔧 In development — Phase 2

---

## 📄 License
MIT License — free to use, modify, and distribute.
