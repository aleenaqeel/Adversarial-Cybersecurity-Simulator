# Adversarial-Cybersecurity-Simulator
Red Team vs Blue Team AI — Minimax/A* Attacker vs Greedy Defender on a simulated network graph
---
# Adversarial Cybersecurity Simulator
### Red Team vs Blue Team AI — Introduction to AI Project

A simulation where two AI agents compete on a modeled computer network. 
The Attacker AI tries to find the most efficient path to a target node, 
while the Defender AI dynamically blocks its progress using firewalls.

---

## Group Members

| Name | ID | Role |
|---|---|---|
| Aleena Aqeel | 31635 | Network Graph & Data |
| Bareera Rehan | 30696 | Attacker AI (Minimax & A*) |
| Emaan Tariq | 31610 | Defender AI & Simulation Loop |
| Waniya Jabeen | 31624 | GUI & Evaluation |

Instructor: Dr. Syed Ali Raza

---

## Problem Statement

Traditional network security depends on manual penetration testing and 
static rule-based defenses, which are slow and unable to adapt in real time. 
This project explores whether intelligent AI agents can simulate both attack 
and defense more effectively, and compares two search strategies for the 
attacker to determine which better identifies critical network vulnerabilities.

---

## Algorithms

| Agent | Algorithm |
|---|---|
| Attacker (primary) | Minimax with Alpha-Beta Pruning |
| Attacker (comparison) | A* Search |
| Defender | Greedy Local Search |

---

## Project Structure

src/
├── network/       # Graph modeling and topology generation
├── attacker/      # Minimax and A* implementations
├── defender/      # Greedy defender logic
├── simulation/    # Turn-based game loop
└── gui/           # Visualization

---

## How to Run

```bash
pip install -r requirements.txt
python main.py
```

---

## Evaluation Metrics

- Attack success rate
- Average path length
- Number of nodes explored
- Defender response effectiveness

---

## Timeline

| Week | Task |
|---|---|
| 1-2 | Graph design and vulnerability scoring |
| 3-4 | Minimax with Alpha-Beta Pruning and Greedy Defender |
| 5 | A* integration and initial simulations |
| 6 | GUI and full integration |
| 7 | Experiments and metric collection |
| 8 | Final report and demo video |
