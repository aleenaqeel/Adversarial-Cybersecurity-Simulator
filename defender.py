import attacker

def run_defender_turn(graph, attacker_pos, target):
    """Defender uses A* to guess the attacker's shortest path and blocks the next step."""
    path, _ = attacker.get_astar_path(graph, attacker_pos, target)
    
    # If the attacker has a valid path to the target, block the immediate next step
    if path and len(path) > 1:
        node_to_block = path[1]
        return node_to_block
        
    return None