import sys
import os
import time
import copy
import random
import numpy as np

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
import networkx as nx

# Import your existing backend logic
import network_generator
import attacker
import defender

# ==========================================
# QSS STYLING 
# ==========================================
DARK_THEME_QSS = """
QMainWindow, QWidget {
    background-color: #030810;
    color: #d0e8ff;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}
QFrame.Panel {
    background-color: #060d1a;
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 6px;
}
QLabel.Title {
    color: #00d4ff;
    font-weight: bold;
    font-size: 14px;
    border-bottom: 1px solid rgba(0,212,255,0.2);
    padding-bottom: 5px;
    margin-bottom: 5px;
}
QLabel.MainHeading {
    color: #00ff88;
    font-size: 16px;
    font-weight: bold;
    background-color: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 4px;
    padding: 6px;
    margin: 2px;
}
QPushButton {
    background-color: transparent;
    border: 1px solid rgba(0,212,255,0.2);
    color: #6a8faa;
    padding: 8px;
    border-radius: 4px;
    font-weight: bold;
}
QPushButton:hover {
    border-color: rgba(0,212,255,0.5);
    color: #d0e8ff;
}
QPushButton:checked {
    border-color: #00d4ff;
    color: #00d4ff;
    background-color: rgba(0,212,255,0.1);
}
QPushButton.LaunchBtn {
    background-color: rgba(0,212,255,0.1);
    color: #00d4ff;
    border: 1px solid #00d4ff;
}
QPushButton.LaunchBtn:hover { background-color: rgba(0,212,255,0.2); }
QPushButton.ResetBtn {
    background-color: rgba(255,34,68,0.1);
    color: #ff2244;
    border: 1px solid #ff2244;
}
QPushButton.ResetBtn:hover { background-color: rgba(255,34,68,0.2); }
QTextEdit {
    background-color: #0a1628;
    border: 1px solid rgba(0,212,255,0.2);
    color: #00ff88;
}
QSlider::groove:horizontal {
    border: 1px solid #999999;
    height: 4px;
    background: #0d1e35;
}
QSlider::handle:horizontal {
    background: #00d4ff;
    width: 12px;
    margin: -4px 0;
    border-radius: 6px;
}
"""

# ==========================================
# SIMULATION THREAD 
# ==========================================
class SimulationWorker(QThread):
    log_signal = pyqtSignal(str, str)
    update_metrics_signal = pyqtSignal(dict)
    draw_graph_signal = pyqtSignal(dict, dict, str, str, list, str)
    play_sound_signal = pyqtSignal(str) # <--- NEW AUDIO SIGNAL
    finished_signal = pyqtSignal()

    def __init__(self, algo, nodes, adj_list, max_turns, fw_rate):
        super().__init__()
        self.algo = algo
        self.nodes = nodes
        self.original_adj_list = adj_list
        self.max_turns = max_turns
        self.fw_rate = fw_rate
        self.speed = 0.8  # Hardcoded speed to 800ms
        self.running = True

    def run(self):
        adj_list = copy.deepcopy(self.original_adj_list)
        
        start_node = next(n for n, d in self.nodes.items() if d['node_type'] == 'Start')
        target_node = next(n for n, d in self.nodes.items() if d['node_type'] == 'Target')
        
        current_pos = start_node
        blocked_edges = []
        path_history = [start_node]
        firewalls = 0

        self.log_signal.emit(f"[{self.algo}] Simulation Started. Breach point: {start_node}", "#00d4ff")
        self.draw_graph_signal.emit(self.nodes, adj_list, current_pos, target_node, blocked_edges, "INIT")
        time.sleep(self.speed)

        for turn in range(1, self.max_turns + 1):
            if not self.running:
                break

            # 1. Attacker Move
            if self.algo == "A*":
                path, _ = attacker.get_astar_path(adj_list, current_pos, target_node)
                next_move = path[1] if len(path) > 1 else current_pos
            else:
                next_move = attacker.get_minimax_move(adj_list, current_pos, target_node)

            if next_move == current_pos:
                self.log_signal.emit(f"Turn {turn}: Defender Wins! ({self.algo} Trapped)", "#00ff88")
                self.update_metrics_signal.emit({"turn": turn, "pos": current_pos, "fw": firewalls, "outcome": "DEFENDER WINS"})
                self.play_sound_signal.emit("defender_win")
                break

            current_pos = next_move
            path_history.append(current_pos)
            self.log_signal.emit(f"Turn {turn}: Attacker -> {current_pos}", "#ff2244")

            if current_pos == target_node:
                self.log_signal.emit(f"*** TARGET COMPROMISED! {self.algo} WINS ***", "#ff2244")
                self.draw_graph_signal.emit(self.nodes, adj_list, current_pos, target_node, blocked_edges, "BREACH")
                self.update_metrics_signal.emit({"turn": turn, "pos": current_pos, "fw": firewalls, "outcome": "ATTACKER WINS"})
                self.play_sound_signal.emit("attacker_win")
                break

            self.draw_graph_signal.emit(self.nodes, adj_list, current_pos, target_node, blocked_edges, "ATTACKING")
            self.update_metrics_signal.emit({"turn": turn, "pos": current_pos, "fw": firewalls, "outcome": "IN PROGRESS"})
            time.sleep(self.speed)

            # 2. Defender Move
            if random.random() < self.fw_rate:
                blocked_node = defender.run_defender_turn(adj_list, current_pos, target_node)
                if blocked_node and blocked_node in adj_list.get(current_pos, {}):
                    adj_list[current_pos][blocked_node] = 999
                    blocked_edges.append((current_pos, blocked_node))
                    firewalls += 1
                    self.log_signal.emit(f"Turn {turn}: Defender blocks {current_pos} -> {blocked_node}", "#ffaa00")
                    self.draw_graph_signal.emit(self.nodes, adj_list, current_pos, target_node, blocked_edges, "DEFENDING")
                    self.update_metrics_signal.emit({"turn": turn, "pos": current_pos, "fw": firewalls, "outcome": "IN PROGRESS"})
                    self.play_sound_signal.emit("firewall")
                    time.sleep(self.speed)
            else:
                self.log_signal.emit(f"Turn {turn}: Defender failed to react.", "#6a8faa")
        else:
            self.log_signal.emit(f"Time Expired. Defender Wins!", "#00ff88")
            self.update_metrics_signal.emit({"turn": self.max_turns, "pos": current_pos, "fw": firewalls, "outcome": "DEFENDER WINS"})
            self.play_sound_signal.emit("defender_win")

        self.finished_signal.emit()

    def stop(self):
        self.running = False


# ==========================================
# EMBEDDED MATPLOTLIB CANVAS 
# ==========================================
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#030810')
        self.ax = fig.add_subplot(111)
        self.ax.set_facecolor('#030810')
        super(MplCanvas, self).__init__(fig)
        self.G = nx.DiGraph()
        self.pos = None

    def init_network(self, nodes, adj_list):
        self.G.clear()
        self.G.add_nodes_from(nodes.keys())
        for source, neighbors in adj_list.items():
            for target, cost in neighbors.items():
                self.G.add_edge(source, target, weight=cost)
                
        self.pos = {}
        node_ids = list(nodes.keys())
        num_nodes = len(node_ids)
        
        layers = {}
        for node_id in node_ids:
            try:
                n_idx = int(node_id.split('_')[1])
            except:
                n_idx = 2
                
            if n_idx == 1:
                layer = 0
            elif n_idx == num_nodes:
                layer = 5
            else:
                layer = 1 + int((n_idx - 2) / max(1, num_nodes - 2) * 3.99)
            
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(node_id)
            
        for layer, layer_nodes in layers.items():
            x = layer / 5.0
            y_step = 1.0 / (len(layer_nodes) + 1)
            for i, node_id in enumerate(layer_nodes):
                y = (i + 1) * y_step 
                self.pos[node_id] = (x, y)

    def draw_device(self, x, y, device_type, s, fill_color, stroke_color):
        if device_type == 'Laptop':
            w, h, base = s*1.4, s*0.9, s*0.3
            screen = patches.Rectangle((x - w/2, y - h/2 + base), w, h, facecolor=fill_color, edgecolor=stroke_color, lw=1.5, zorder=4)
            screen_in = patches.Rectangle((x - w/2 + s*0.1, y - h/2 + base + s*0.1), w - s*0.2, h - s*0.2, facecolor='#0a2040', zorder=5)
            base_rect = patches.Rectangle((x - w/2 - s*0.1, y - h/2), w + s*0.2, base, facecolor=fill_color, edgecolor=stroke_color, lw=1.5, zorder=4)
            self.ax.add_patch(screen)
            self.ax.add_patch(screen_in)
            self.ax.add_patch(base_rect)

        elif device_type == 'Server':
            w, h = s*1.2, s*1.6
            box = patches.Rectangle((x - w/2, y - h/2), w, h, facecolor=fill_color, edgecolor=stroke_color, lw=1.5, zorder=4)
            self.ax.add_patch(box)
            for i in range(3):
                slot_y = y - h/2 + s*0.2 + i*(h/3)
                self.ax.add_patch(patches.Rectangle((x - w/2 + s*0.1, slot_y), w - s*0.2, h/3 - s*0.3, facecolor='#0a2040', zorder=5))
                self.ax.add_patch(patches.Circle((x + w/2 - s*0.3, slot_y + s*0.1), s*0.08, facecolor='#00ff88' if i==0 else '#00d4ff', zorder=6))

        elif device_type == 'Router':
            angles = np.linspace(0, 2*np.pi, 7) + np.pi/6
            hex_x, hex_y = x + s * np.cos(angles), y + s * np.sin(angles)
            self.ax.add_patch(patches.Polygon(np.column_stack([hex_x, hex_y]), facecolor=fill_color, edgecolor=stroke_color, lw=1.5, zorder=4))
            self.ax.plot([x - s*0.4, x - s*0.4], [y + s*0.6, y + s*1.4], color=stroke_color, lw=1.5, zorder=3)
            self.ax.plot([x + s*0.4, x + s*0.4], [y + s*0.6, y + s*1.4], color=stroke_color, lw=1.5, zorder=3)

        elif device_type == 'Printer':
            w, h = s*1.3, s*1.0
            self.ax.add_patch(patches.Rectangle((x - w/2, y - h/2), w, h*0.7, facecolor=fill_color, edgecolor=stroke_color, lw=1.5, zorder=4))
            self.ax.add_patch(patches.Rectangle((x - w/3, y + h*0.2 - s*0.1), w*0.66, s*0.4, facecolor='#e8e8e8', edgecolor=stroke_color, lw=1, zorder=3))

        elif device_type == 'Switch':
            w, h = s*1.5, s*0.7
            self.ax.add_patch(patches.Rectangle((x - w/2, y - h/2), w, h, facecolor=fill_color, edgecolor=stroke_color, lw=1.5, zorder=4))
            for i in range(5):
                self.ax.add_patch(patches.Rectangle((x - w/2 + s*0.2 + i*(s*0.23), y - h/2 + s*0.1), s*0.15, s*0.15, facecolor='#00d4ff', zorder=5))

        elif device_type == 'Firewall':
            sx = [x, x+s*0.8, x+s*0.8, x, x-s*0.8, x-s*0.8]
            sy = [y-s*0.8, y-s*0.2, y+s*0.5, y+s*0.8, y+s*0.5, y-s*0.2]
            self.ax.add_patch(patches.Polygon(np.column_stack([sx, sy]), facecolor=fill_color, edgecolor=stroke_color, lw=1.5, zorder=4))

        else: # Generic Fallback
            self.ax.add_patch(patches.Circle((x, y), s, facecolor=fill_color, edgecolor=stroke_color, lw=1.5, zorder=4))

    def draw_network(self, nodes, adj_list, attacker_pos, target_node, blocked_edges, status_text=""):
        self.ax.clear()
        self.ax.set_facecolor('#030810')
        
        self.ax.set_aspect('equal', adjustable='datalim')
        self.ax.set_xlim(-0.1, 1.1)
        self.ax.set_ylim(-0.1, 1.1)
        
        curve_style = 'arc3,rad=0.15'
        
        num_nodes = len(self.G.nodes)
        scale_s = max(0.012, 0.04 - (num_nodes / 100.0) * 0.025)
        font_s = max(4, 9 - int(num_nodes / 15))

        # 1. Draw Normal Edges
        normal_edges = [(u, v) for u, v in self.G.edges() if (u, v) not in blocked_edges]
        nx.draw_networkx_edges(self.G, self.pos, edgelist=normal_edges, edge_color='#304560', 
                               arrows=True, arrowsize=8, node_size=800, ax=self.ax,
                               connectionstyle=curve_style)
        
        # 2. Draw Blocked Edges (Firewalls)
        if blocked_edges:
            nx.draw_networkx_edges(self.G, self.pos, edgelist=blocked_edges, edge_color='#ffaa00', 
                                   width=2, style='dashed', arrows=False, ax=self.ax,
                                   connectionstyle=curve_style)
                                   
        # 3. Draw Edge Weights
        if num_nodes <= 30:
            edge_labels = {(u, v): f"{d['weight']:.1f}" for u, v, d in self.G.edges(data=True) if d['weight'] < 900}
            nx.draw_networkx_edge_labels(self.G, self.pos, edge_labels=edge_labels, 
                                         font_color='#0099bb', font_size=5, ax=self.ax,
                                         bbox=dict(facecolor='#030810', edgecolor='none', alpha=0.8, pad=0))

        # 4. Draw Devices dynamically scaled
        for node in self.G.nodes:
            device = nodes[node].get('device_type', 'Unknown')
            x, y = self.pos[node]
            
            if node == attacker_pos:
                fill, stroke, text_color = '#1a0505', '#ff2244', '#ff8899'
            elif node == target_node:
                fill, stroke, text_color = '#051a0a', '#00ff88', '#88ffbb'
            else:
                fill, stroke, text_color = '#060d1a', '#00d4ff', '#d0e8ff'
            
            self.draw_device(x, y, device, s=scale_s, fill_color=fill, stroke_color=stroke)
            
            short_id = node.replace('Node_', 'N')
            label = f"{device}\n[{short_id}]"
            self.ax.text(x, y - (scale_s*2), label, ha="center", va="top", color=text_color, 
                         fontsize=font_s, fontfamily="Consolas", zorder=5)

        self.ax.axis('off')
        self.draw()

# ==========================================
# MAIN GUI WINDOW
# ==========================================
class SimulatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("REDBLUE.SIM - Adversarial AI Cybersecurity")
        self.setGeometry(100, 100, 1200, 800)
        
        self.nodes_data = {}
        self.adj_list_data = {}
        self.worker = None
        
        self.init_audio()
        self.initUI()
        self.reset_sim()

    def init_audio(self):
        """Loads and preps the background music and sound effects"""
        # Background Music (Loops continuously)
        self.playlist = QMediaPlaylist()
        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath("bg_music.mp3"))))
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.bg_music = QMediaPlayer()
        self.bg_music.setPlaylist(self.playlist)
        self.bg_music.setVolume(50) # Set background volume slightly lower

        # Sound Effects
        self.sfx_firewall = QMediaPlayer()
        self.sfx_firewall.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath("firewall.mp3"))))
        
        self.sfx_win = QMediaPlayer()
        self.sfx_win.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath("attacker_win.mp3"))))
        
        self.sfx_lose = QMediaPlayer()
        self.sfx_lose.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath("defender_win.mp3"))))

    def play_sound(self, event_type):
        """Triggers audio cues based on the worker signals"""
        if event_type == "firewall":
            self.sfx_firewall.setPosition(0)
            self.sfx_firewall.play()
        elif event_type == "attacker_win":
            self.bg_music.stop()
            self.sfx_win.setPosition(0)
            self.sfx_win.play()
        elif event_type == "defender_win":
            self.bg_music.stop()
            self.sfx_lose.setPosition(0)
            self.sfx_lose.play()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- LEFT PANEL (Controls) ---
        left_panel = QFrame()
        left_panel.setProperty("class", "Panel")
        left_panel.setFixedWidth(260)
        left_layout = QVBoxLayout(left_panel)

        # Algo Selection
        lbl_algo = QLabel("ALGORITHM SELECT")
        lbl_algo.setProperty("class", "Title")
        left_layout.addWidget(lbl_algo)
        
        self.btn_astar = QPushButton("A* Search")
        self.btn_astar.setCheckable(True)
        self.btn_astar.setChecked(True)
        self.btn_minimax = QPushButton("Minimax + Alpha-Beta")
        self.btn_minimax.setCheckable(True)
        
        self.btn_astar.clicked.connect(lambda: self.set_algo("A*"))
        self.btn_minimax.clicked.connect(lambda: self.set_algo("Minimax"))
        
        left_layout.addWidget(self.btn_astar)
        left_layout.addWidget(self.btn_minimax)

        # Config Sliders
        lbl_config = QLabel("\nNETWORK CONFIG")
        lbl_config.setProperty("class", "Title")
        left_layout.addWidget(lbl_config)

        self.lbl_node_val = QLabel("Nodes: 15")
        self.slider_nodes = QSlider(Qt.Horizontal)
        self.slider_nodes.setRange(5, 100)
        self.slider_nodes.setValue(15)
        self.slider_nodes.valueChanged.connect(self.update_node_label)
        left_layout.addWidget(self.lbl_node_val)
        left_layout.addWidget(self.slider_nodes)

        self.lbl_fw_val = QLabel("Firewall Rate: 40%")
        self.slider_fw = QSlider(Qt.Horizontal)
        self.slider_fw.setRange(0, 100)
        self.slider_fw.setValue(40)
        self.slider_fw.valueChanged.connect(lambda v: self.lbl_fw_val.setText(f"Firewall Rate: {v}%"))
        left_layout.addWidget(self.lbl_fw_val)
        left_layout.addWidget(self.slider_fw)
        
        left_layout.addStretch()

        # Run Controls
        self.btn_launch = QPushButton("▶ LAUNCH SIM")
        self.btn_launch.setProperty("class", "LaunchBtn")
        self.btn_launch.clicked.connect(self.launch_sim)
        
        self.btn_reset = QPushButton("■ RESET NETWORK")
        self.btn_reset.setProperty("class", "ResetBtn")
        self.btn_reset.clicked.connect(self.reset_sim)

        left_layout.addWidget(self.btn_launch)
        left_layout.addWidget(self.btn_reset)

        # --- CENTER PANEL (Canvas & Heading) ---
        center_panel = QFrame()
        center_panel.setProperty("class", "Panel")
        center_layout = QVBoxLayout(center_panel)

        # Dynamic Top Heading
        self.lbl_network_class = QLabel("ACTIVE TOPOLOGY: COMPUTER LAB")
        self.lbl_network_class.setProperty("class", "MainHeading")
        self.lbl_network_class.setAlignment(Qt.AlignCenter)
        self.lbl_network_class.setMaximumHeight(35) 
        center_layout.addWidget(self.lbl_network_class)

        self.canvas = MplCanvas(self, width=6, height=5, dpi=100)
        center_layout.addWidget(self.canvas, stretch=1)

        # --- RIGHT PANEL (Metrics & Logs) ---
        right_panel = QFrame()
        right_panel.setProperty("class", "Panel")
        right_panel.setFixedWidth(300)
        right_layout = QVBoxLayout(right_panel)

        lbl_metrics = QLabel("LIVE METRICS")
        lbl_metrics.setProperty("class", "Title")
        right_layout.addWidget(lbl_metrics)

        self.lbl_turn = QLabel("Current Turn: —")
        self.lbl_pos = QLabel("Attacker Pos: —")
        self.lbl_fw = QLabel("Firewalls Hit: 0")
        self.lbl_outcome = QLabel("Outcome: —")
        self.lbl_outcome.setStyleSheet("color: #ffaa00; font-weight: bold;")
        
        right_layout.addWidget(self.lbl_turn)
        right_layout.addWidget(self.lbl_pos)
        right_layout.addWidget(self.lbl_fw)
        right_layout.addWidget(self.lbl_outcome)

        lbl_log = QLabel("\nEVENT LOG")
        lbl_log.setProperty("class", "Title")
        right_layout.addWidget(lbl_log)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        right_layout.addWidget(self.log_box)

        # Add to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel, stretch=1)
        main_layout.addWidget(right_panel)

    def set_algo(self, algo):
        if algo == "A*":
            self.btn_astar.setChecked(True)
            self.btn_minimax.setChecked(False)
        else:
            self.btn_astar.setChecked(False)
            self.btn_minimax.setChecked(True)

    def log(self, message, color="#00ff88"):
        time_str = time.strftime("%H:%M:%S")
        self.log_box.append(f"<span style='color:#6a8faa;'>[{time_str}]</span> <span style='color:{color};'>{message}</span>")

    def update_node_label(self, val):
        self.lbl_node_val.setText(f"Nodes: {val}")
        
        if val <= 10:
            net_type = "ROOM / SMALL OFFICE"
        elif val <= 40:
            net_type = "COMPUTER LAB"
        elif val <= 80:
            net_type = "CORPORATE BRANCH"
        else:
            net_type = "ENTERPRISE DATACENTER"
            
        self.lbl_network_class.setText(f"ACTIVE TOPOLOGY: {net_type}")

    def reset_sim(self):
        self.bg_music.stop() # Stop music if it's currently playing
        
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        network_generator.NUM_NODES = self.slider_nodes.value()
        self.nodes_data, self.adj_list_data = network_generator.generate_simulation_data()
        
        start_node = next(n for n, d in self.nodes_data.items() if d['node_type'] == 'Start')
        target_node = next(n for n, d in self.nodes_data.items() if d['node_type'] == 'Target')
        
        self.canvas.init_network(self.nodes_data, self.adj_list_data)
        self.canvas.draw_network(self.nodes_data, self.adj_list_data, start_node, target_node, [])
        
        self.update_node_label(self.slider_nodes.value())
        
        self.log("System Reset. New Network Generated.", "#00d4ff")
        self.lbl_turn.setText("Current Turn: —")
        self.lbl_pos.setText(f"Attacker Pos: {start_node}")
        self.lbl_fw.setText("Firewalls Hit: 0")
        self.lbl_outcome.setText("Outcome: —")
        self.btn_launch.setEnabled(True)

    def launch_sim(self):
        self.btn_launch.setEnabled(False)
        self.log_box.clear()
        
        # Start playing background music
        self.bg_music.play()
        
        algo = "A*" if self.btn_astar.isChecked() else "Minimax"
        fw_rate = self.slider_fw.value() / 100.0
        dynamic_turns = len(self.nodes_data) + 15
        
        self.worker = SimulationWorker(algo, self.nodes_data, self.adj_list_data, max_turns=dynamic_turns, fw_rate=fw_rate)
        self.worker.log_signal.connect(self.log)
        self.worker.update_metrics_signal.connect(self.update_metrics)
        self.worker.draw_graph_signal.connect(self.canvas.draw_network)
        self.worker.play_sound_signal.connect(self.play_sound) # Connect audio signals
        self.worker.finished_signal.connect(lambda: self.btn_launch.setEnabled(True))
        
        self.worker.start()

    def update_metrics(self, data):
        self.lbl_turn.setText(f"Current Turn: {data['turn']}")
        self.lbl_pos.setText(f"Attacker Pos: {data['pos']}")
        self.lbl_fw.setText(f"Firewalls Hit: {data['fw']}")
        self.lbl_outcome.setText(f"Outcome: {data['outcome']}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    gui = SimulatorGUI()
    gui.show()
    sys.exit(app.exec_())