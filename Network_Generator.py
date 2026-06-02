import json
import random

# --- Global Experiment Constants ---
W1_DIFFICULTY = 0.7
W2_IMPACT = 0.3
NUM_NODES = 15 # Default, gets updated by GUI slider

def load_vulnerability_data():
    """Loads CVE data from your provided JSON file."""
    try:
        with open("all_layer_samples.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"DUMMY-CVE": {"exploit_score": 5.0, "impact_score": 5.0}}

def calculate_edge_cost(exploit_score, impact_score):
    """Calculates the combined cost of an edge based on vulnerability metrics."""
    difficulty_component = 10.0 - exploit_score
    impact_component = 10.0 - impact_score
    cost = (W1_DIFFICULTY * difficulty_component) + (W2_IMPACT * impact_component)
    return round(cost, 2)

def generate_simulation_data():
    """Generates nodes and the weighted Adjacency List."""
    nodes = {}
    device_options = ['Laptop', 'Printer', 'Server', 'Router', 'Switch', 'Firewall']
    device_weights = [0.35, 0.1, 0.2, 0.15, 0.15, 0.05]
    
    cve_data = load_vulnerability_data()
    cve_keys = list(cve_data.keys())

    start_node = "Node_1"
    target_node = f"Node_{NUM_NODES}"

    # 1. Generate Nodes
    for i in range(1, NUM_NODES + 1):
        node_id = f"Node_{i}"
        
        if node_id == start_node:
            node_type = 'Start'
            # An attacker usually breaches the perimeter via a Phished Laptop, an exposed Router, or a vulnerable IoT device (Printer)
            device = random.choices(['Laptop', 'Router', 'Printer'], weights=[0.6, 0.2, 0.2])[0]
        elif node_id == target_node:
            node_type = 'Target'
            # The ultimate goal is usually a Database or an Executive's machine
            device = random.choices(['Server', 'Laptop'], weights=[0.8, 0.2])[0]
        else:
            node_type = 'Intermediate'
            device = random.choices(device_options, weights=device_weights)[0]

        random_cve = random.choice(cve_keys)
        cve_info = cve_data[random_cve]
        
        if isinstance(cve_info, dict):
            e_score = cve_info.get("exploit_score", random.uniform(2.0, 10.0))
            i_score = cve_info.get("impact_score", random.uniform(2.0, 10.0))
        else:
            e_score = random.uniform(2.0, 10.0)
            i_score = random.uniform(2.0, 10.0)

        nodes[node_id] = {
            "device_type": device,
            "node_type": node_type,
            "cve_id": random_cve, 
            "exploit_score": round(e_score, 1),
            "impact_score": round(i_score, 1),
            "status": "neutral"  
        }

    # 2. Build the Adjacency List
    adjacency_list = {node_id: {} for node_id in nodes}
    node_ids = list(nodes.keys())

    for source_id in node_ids:
        if nodes[source_id]['node_type'] == 'Target': continue
        
        valid_targets = [n for n in node_ids if n != source_id]
        source_number = int(source_id.split('_')[1])

        # Target Isolation
        deep_threshold = int(NUM_NODES * 0.7)
        if source_number < deep_threshold and target_node in valid_targets:
            valid_targets.remove(target_node)

        # Start Node Restriction
        dmz_threshold = int(NUM_NODES * 0.4)
        if source_id == start_node:
            valid_targets = [n for n in valid_targets if int(n.split('_')[1]) <= dmz_threshold]
            if target_node in valid_targets: 
                valid_targets.remove(target_node) 
            
        # Prevent massive forward jumps
        if source_id != start_node:
            valid_targets = [n for n in valid_targets if int(n.split('_')[1]) <= source_number + 4]

        forward_targets = [n for n in valid_targets if int(n.split('_')[1]) > source_number]
        num_connections = random.randint(2, 4)
        targets = []
        
        if forward_targets:
            targets.append(random.choice(forward_targets))
            
        remaining_slots = num_connections - len(targets)
        available = [n for n in valid_targets if n not in targets]
        remaining_slots = min(remaining_slots, len(available))
        
        if remaining_slots > 0:
            targets.extend(random.sample(available, remaining_slots))

        for target_id in targets:
            target_cost = calculate_edge_cost(nodes[target_id]['exploit_score'], nodes[target_id]['impact_score'])
            adjacency_list[source_id][target_id] = target_cost
            
            if nodes[source_id]['device_type'] == 'Laptop' and nodes[target_id]['device_type'] == 'Laptop':
                source_cost = calculate_edge_cost(nodes[source_id]['exploit_score'], nodes[source_id]['impact_score'])
                adjacency_list[target_id][source_id] = source_cost

    # 3. SANITY CHECK: Prevent Lonely Target Node
    target_has_incoming = any(target_node in connections for connections in adjacency_list.values())
    if not target_has_incoming:
        savior_idx = max(1, NUM_NODES - 1)
        savior_node = f"Node_{savior_idx}"
        if savior_node != target_node:
            forced_cost = calculate_edge_cost(nodes[target_node]['exploit_score'], nodes[target_node]['impact_score'])
            adjacency_list[savior_node][target_node] = forced_cost

    return nodes, adjacency_list