# Carleton Multi-Agent Pathfinding

Multi-agent pathfinding system that maximizes time two students spend together between classes on Carleton's campus.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run Simulations

Generate comparison data between intelligent and naive agents:

```bash
python compare_results.py
```

This creates `results/comparison_results.csv` with columns: `index`, `intelligent_time`, `naive_time`

## Statistical Analysis

Run t-test and generate box plot:

```bash
python statistical_analysis.py
```

Outputs descriptive stats, paired t-test results, and saves `results/comparison_boxplot.png`

## File Overview

**Core:**
- `graph.py` - Build campus network from OpenStreetMap
- `astar.py` - A* pathfinding (tunnel/outdoor modes)
- `fuzzy_decision.py` - Weather-based path selection
- `multi_agent_pathfinding.py` - Find optimal rendezvous points, calculate social score

**Utilities:**
- `utils.py` - Time parsing, building lookup
- `config.py` - Configuration constants
- `visualization.py` - Network and path visualizations

**Simulation:**
- `compare_results.py` - Generate intelligent vs naive comparison data
- `statistical_analysis.py` - Analyze results with t-test and plots
