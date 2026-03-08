# 🌿 Ecosystem Simulation & Analytics Platform
---

A continuously running server-based simulation of a living ecosystem populated by autonomous, mathematically-themed entities. The simulation can be controlled in real time — run, paused, reset, and configured to adjust environmental settings or introduce new objects and entities at any time. A built-in creature builder allows new entity types to be designed and dropped into the ecosystem while the simulation is actively running. Creatures are mathematically inspired — exhibiting behaviors such as parametric movement, spiral navigation, exponential reproduction, and vector-based pathfinding. The simulation exists in a dual-dimension environment where 3D creatures navigate freely in XYZ space while 2D creatures are locked to a flat plane, producing unique cross-dimensional interactions and emergent behavior. All simulation data is continuously logged to a database, powering live analytics dashboards and serving as the foundation for ongoing data science experiments, statistical analysis, and research reports.

---

## 🏗️ Project Architecture

```
┌──────────────────┐        ┌───────────────────┐
│  PYTHON SERVER   │◄──────►│     GODOT 4       │
│  FastAPI+SQLite  │        │  Visual World     │
│                  │        │  Agents moving    │
│  The Brain       │        │  around a grid    │
└────────┬─────────┘        └───────────────────┘
         │
         ▼
┌──────────────────┐
│  GRAFANA         │
│  Live Charts     │
│  Stats & Metrics │
└──────────────────┘
```

- **Python Server** — the single source of truth. Runs the simulation, stores data, and exposes API endpoints
- **Godot 4** — client that visualizes the ecosystem in real time by polling the server
- **Grafana** — client that reads from the database and renders live analytics panels

---

## 🗂️ Repository Structure

```
ecosystem-simulation/
├── server/          # Python FastAPI simulation engine
├── simulation/      # Godot 4 project
├── dashboard/       # Grafana configuration files
├── data/            # Exported CSVs for analysis
├── reports/         # Data findings and experiment write-ups
└── README.md
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

## 🚀 Build Phases

| Phase | What Gets Built | Difficulty | Est. Time |
|-------|----------------|------------|-----------|
| 1 | Python simulation engine | ⭐⭐ Medium | 1-2 weeks |
| 2 | SQLite persistence | ⭐ Easy | 2-3 days |
| 3 | FastAPI server | ⭐⭐ Medium | 1 week |
| 4 | Godot visual world | ⭐⭐⭐ Hard | 2-4 weeks |
| 5 | Grafana dashboard | ⭐⭐ Medium | 3-5 days |
| 6 | Data analysis & reports | ⭐⭐ Medium | Ongoing |

**Total estimate:** 2-3 months working casually, or 4-6 weeks if focused.

---

## 📊 Skills Developed

**Programming**
- Python OOP (classes, methods, inheritance)
- GDScript (Godot's scripting language)
- API design and development (FastAPI)
- Client-server communication (HTTP, JSON)

**Data & Databases**
- SQL basics (SQLite)
- Data cleaning and analysis (Pandas)
- Data visualization (Matplotlib, Grafana)
- Time-series data interpretation

**Software Engineering**
- Version control (Git & GitHub)
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
🔧 In development — Phase 1
