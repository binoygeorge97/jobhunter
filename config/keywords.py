# config/keywords.py

# ─── PASS 1: KILL SWITCH ────────────────────────────────────────────────────
# Any listing containing these words (case-insensitive) is immediately discarded.
# Do NOT add "CNC", "embedded C", "motor control" — Binoy has legitimate
# projects in those areas and should NOT kill roles that involve them.

KILL_SWITCH_KEYWORDS = [
    # Classic industrial automation — always kill
    "PLC",
    "Allen-Bradley",
    "Ladder Logic",
    "SCADA",
    "DCS",                     # Distributed Control Systems (oil/gas)
    "HMI programming",         # Human-Machine Interface in factory context
    "P&ID",                    # Piping & Instrumentation Diagram (process eng.)
    "ISA-88",                  # Batch manufacturing standard
    # Manufacturing/factory operations — kill (not design)
    "plant floor",
    "shop floor",
    "Six Sigma",               # Manufacturing optimization
    "injection molding",
    "press operator",
    "machine operator",
    "production line",
]

# ─── PASS 2: MATCH SCORING ───────────────────────────────────────────────────
# Tier 1: Binoy has hardware results to back these up. Worth 3 pts each.
TIER_1_KEYWORDS = [
    "UKF",
    "Unscented Kalman",
    "Kalman Filter",
    "Sensor Fusion",
    "ROS",
    "ROS2",
    "JAX",
    "FLAX",
    "Jetson",
    "edge inference",
    "UWB",
    "Ultra-Wideband",
    "LiDAR",
    "point cloud",
    "State Space",
    "LQR",
    "MATLAB",
    "Simulink",
    "localization",
    "autonomous navigation",
]

# Tier 2: Overlapping or adjacent skills. Worth 1 pt each.
TIER_2_KEYWORDS = [
    "Python",
    "NumPy",
    "PyTorch",
    "SLAM",
    "path planning",
    "embedded systems",
    "control theory",
    "Reinforcement Learning",
    "C++",
    "EKF",
    "Extended Kalman",
    "odometry",
    "perception",
    "GNC",
    "guidance navigation control",
    "UAV",
    "UGV",
    "drone",
    "autonomous vehicle",
    "edge computing",
    "neural network",
    "S4",
    "state space model",
]

# Company bonus: add 5 pts if the company is one of these.
PRIORITY_COMPANIES = [
    "Y Combinator", "YC",
    "NASA", "JPL", "Jet Propulsion",
    "Skydio", "Shield AI", "Joby", "Joby Aviation",
    "Anduril", "Aurora", "Aurora Innovation",
    "Zipline", "Wisk", "Wisk Aero",
    "Sarcos", "Boston Dynamics",
    "Physical Intelligence", "Figure AI", "1X Technologies",
    "Reliable Robotics", "Joby", "Archer Aviation",
]

# Minimum score to include in final output
MATCH_SCORE_THRESHOLD = 6
