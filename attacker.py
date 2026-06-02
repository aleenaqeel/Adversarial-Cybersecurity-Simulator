import heapq
import copy

def heuristic(node, target):
    """
    Admissible Heuristic: Estimates remaining hops using a very small 
    constant multiplier to ensure we never overestimate the true cost.
    """
    try:
        current_id = int(node.split('_')[1])
        target_id = int(target.split('_')[1])
        # Using 0.1 ensures that even if the path is very 'vulnerable/cheap',
        # our estimate remains below the actual cost.
        return abs(target_id - current_id) * 0.1 
    except:
        return 0

def get_astar_path(graph, start, target):
    """Calculates shortest path using true A* logic with a heuristic."""
    queue = [(0 + heuristic(start, target), 0, start, [start])]
    visited = set()

    while queue:
        f_cost, g_cost, current, path = heapq.heappop(queue)

        if current == target:
            return path, g_cost 
        
        if current in visited:
            continue
        visited.add(current)

        for neighbor, weight in graph.get(current, {}).items():
            if neighbor not in visited and weight < 900: 
                new_g_cost = g_cost + weight
                new_f_cost = new_g_cost + heuristic(neighbor, target)
                heapq.heappush(queue, (new_f_cost, new_g_cost, neighbor, path + [neighbor]))
            
    return [], float('inf')

# ==========================================
# TRUE MINIMAX WITH ALPHA-BETA PRUNING
# ==========================================
def minimax_alpha_beta(graph, current_node, target, depth, alpha, beta, is_attacker_turn):
    """
    Recursive Minimax search with Alpha-Beta pruning.
    Attacker wants to MINIMIZE cost. Defender wants to MAXIMIZE cost.
    """
    # 1. Base Cases: Hit target or hit depth limit
    if current_node == target:
        return 0 
    if depth == 0:
        # Evaluate board state using A* heuristic
        _, estimated_cost = get_astar_path(graph, current_node, target)
        return estimated_cost

    valid_moves = [n for n, w in graph.get(current_node, {}).items() if w < 900]
    if not valid_moves:
        return float('inf') if is_attacker_turn else float('-inf')

    # 2. Minimizer (Attacker's turn to pick a node)
    if is_attacker_turn:
        min_eval = float('inf')
        for neighbor in valid_moves:
            edge_cost = graph[current_node][neighbor]
            
            # Attacker moves, next ply is Defender's turn (False)
            eval_cost = edge_cost + minimax_alpha_beta(graph, neighbor, target, depth - 1, alpha, beta, False)
            
            min_eval = min(min_eval, eval_cost)
            beta = min(beta, eval_cost)
            
            # Alpha-Beta Pruning
            if beta <= alpha:
                break 
                
        return min_eval

    # 3. Maximizer (Defender's turn to simulate blocking a path)
    else:
        max_eval = float('-inf')
        
        for blocked_target in valid_moves:
            # Simulate placing a firewall
            temp_graph = copy.deepcopy(graph)
            temp_graph[current_node][blocked_target] = 999
            
            # Defender blocked, now Attacker must evaluate next move (True)
            eval_cost = minimax_alpha_beta(temp_graph, current_node, target, depth - 1, alpha, beta, True)
            
            max_eval = max(max_eval, eval_cost)
            alpha = max(alpha, eval_cost)
            
            # Alpha-Beta Pruning
            if beta <= alpha:
                break 
                
        return max_eval

def get_minimax_move(graph, current_node, target, depth=2):
    """Calculates the best move for the attacker using Alpha-Beta Pruning."""
    best_score = float('inf')
    best_move = None
    
    # Standard starting bounds for Alpha (-inf) and Beta (+inf)
    alpha = float('-inf')
    beta = float('inf')

    valid_moves = [n for n, w in graph.get(current_node, {}).items() if w < 900]

    for neighbor in valid_moves:
        edge_cost = graph[current_node][neighbor]
        
        # Root is Attacker (Minimizer) making a move. Next ply is Defender's response.
        score = edge_cost + minimax_alpha_beta(graph, neighbor, target, depth, alpha, beta, False)

        if score < best_score:
            best_score = score
            best_move = neighbor

        # Update Beta for the root node
        beta = min(beta, best_score)

    return best_move if best_move else current_node