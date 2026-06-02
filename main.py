import network_generator
import attacker
import defender
import visualizer
import time
import random
import copy

def run_simulation(algo_choice, nodes, original_adj_list):
    print(f"\n======================================")
    print(f"  STARTING RUN: {algo_choice} ALGORITHM")
    print(f"======================================")
    
    adj_list = copy.deepcopy(original_adj_list)
    start_node = "Node_1"
    target_node = f"Node_{network_generator.NUM_NODES}"
    current_pos = start_node
    blocked_edges = [] 
    
    metrics = {
        "algo": algo_choice,
        "outcome": "Unknown",
        "turns_taken": 0,
        "firewalls_encountered": 0,
        "path_history": [start_node]
    }
    
    visualizer.init_graph(nodes, adj_list)
    visualizer.draw_state(nodes, adj_list, current_pos, target_node, blocked_edges, f"Start! Attacker: {algo_choice}")

    for turn in range(1, 16): 
        metrics["turns_taken"] = turn
        print(f"\n[{algo_choice} - Turn {turn}] Attacker is at {current_pos}")
        
        # --- 1. Attacker Move ---
        if algo_choice == "A*":
            path, _ = attacker.get_astar_path(adj_list, current_pos, target_node)
            next_move = path[1] if len(path) > 1 else current_pos
        elif algo_choice == "Minimax":
            next_move = attacker.get_minimax_move(adj_list, current_pos, target_node)
            
        if next_move == current_pos:
            msg = f"Defender Wins! ({algo_choice} Trapped)"
            print(msg)
            metrics["outcome"] = "Defender Wins (Attacker Trapped)"
            visualizer.draw_state(nodes, adj_list, current_pos, target_node, blocked_edges, msg)
            return metrics

        print(f"-> Attacker moves to {next_move}")
        current_pos = next_move
        metrics["path_history"].append(current_pos)

        if current_pos == target_node:
            msg = f"Target Compromised! {algo_choice} Wins!"
            print(f"\n*** {msg} ***")
            metrics["outcome"] = f"Attacker Wins"
            visualizer.draw_state(nodes, adj_list, current_pos, target_node, blocked_edges, msg)
            return metrics

        visualizer.draw_state(nodes, adj_list, current_pos, target_node, blocked_edges, f"{algo_choice} Turn {turn}: Moved to {current_pos}")

        # --- 2. Defender Move ---
        if random.random() < 0.4:
            blocked_node = defender.run_defender_turn(adj_list, current_pos, target_node)
            if blocked_node and blocked_node in adj_list.get(current_pos, {}):
                adj_list[current_pos][blocked_node] = 999
                blocked_edges.append((current_pos, blocked_node)) 
                metrics["firewalls_encountered"] += 1
                
                print(f"-> Defender deployed firewall at {blocked_node}")
                visualizer.draw_state(nodes, adj_list, current_pos, target_node, blocked_edges, f"{algo_choice} Turn {turn}: Defender blocked {current_pos} -> {blocked_node}")
        else:
            print("-> Defender failed to react in time this turn.")

    visualizer.draw_state(nodes, adj_list, current_pos, target_node, blocked_edges, f"Defender Wins ({algo_choice} Time Expired)")
    metrics["outcome"] = "Defender Wins (Time Out)"
    return metrics

def export_report(astar_metrics, minimax_metrics):
    """Generates a text file comparing the two algorithms."""
    filename = "simulation_report.txt"
    with open(filename, "w") as f:
        f.write("====================================================\n")
        f.write("       ADVERSARIAL AI SIMULATION REPORT\n")
        f.write("====================================================\n\n")
        
        for data in [astar_metrics, minimax_metrics]:
            f.write(f"--- {data['algo']} Algorithm Results ---\n")
            f.write(f"Outcome:              {data['outcome']}\n")
            f.write(f"Total Turns Taken:    {data['turns_taken']}\n")
            f.write(f"Firewalls Triggered:  {data['firewalls_encountered']}\n")
            f.write(f"Path Traversed:       {' -> '.join(data['path_history'])}\n")
            f.write("-" * 52 + "\n\n")
            
        f.write("--- Analysis Summary ---\n")
        if astar_metrics['turns_taken'] < minimax_metrics['turns_taken'] and "Attacker Wins" in astar_metrics['outcome']:
            f.write("-> A* reached the target faster than Minimax.\n")
        elif minimax_metrics['turns_taken'] < astar_metrics['turns_taken'] and "Attacker Wins" in minimax_metrics['outcome']:
            f.write("-> Minimax reached the target faster than A*.\n")
            
        if astar_metrics['firewalls_encountered'] > minimax_metrics['firewalls_encountered']:
            f.write("-> Minimax successfully evaded more firewalls than A*.\n")
        elif minimax_metrics['firewalls_encountered'] > astar_metrics['firewalls_encountered']:
             f.write("-> A* successfully evaded more firewalls than Minimax.\n")
             
    print(f"\n[+] Detailed comparison report saved to: {filename}")


if __name__ == "__main__":
    print("--- Generating Shared Network Map ---")
    shared_nodes, shared_adj_list = network_generator.generate_simulation_data()
    
    astar_results = run_simulation("A*", shared_nodes, shared_adj_list)
    
    print("\n[!] A* Run complete. Pausing for 4 seconds before starting Minimax...")
    time.sleep(4)
    
    minimax_results = run_simulation("Minimax", shared_nodes, shared_adj_list)
    export_report(astar_results, minimax_results)
    
    print("\nClose the graph window to exit the program.")
    visualizer.keep_window_open()