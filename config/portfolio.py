# config/portfolio.py

PORTFOLIO_CONTEXT = """
You are analyzing job listings for Binoy George, a PhD candidate in Electrical Engineering
at the University of Texas at Arlington (expected Spring 2027, CGPA 3.91/4.0).

=== BINOY'S PROJECTS (use these to match against job requirements) ===

PROJECT 1 — UWB Robot Localization
  What: Trilateration algorithm for robot localization in 2D and 3D space
  How: Python + ROS, Decawave UWB sensors (hardware), tested on stationary and moving robots
  Results: <20 cm indoor localization accuracy; potential for self-driving car nav
  Best for roles requiring: localization, UWB, indoor navigation, Python/ROS, sensor hardware

PROJECT 2 — Robot Localization via Unscented Kalman Filter (UKF)
  What: Sensor fusion fusing odometry + UWB using UKF to minimize individual sensor errors
  How: MATLAB/Simulink for UKF design; Python + ROS for robot + sensor control; turtlebot2i platform
  Results: 20% reduction in robot position error vs standalone UWB; significantly reduced odometry drift
  Best for roles requiring: UKF, EKF, sensor fusion, state estimation, SLAM-adjacent, MATLAB/Simulink, ROS

PROJECT 3 — Unmanned Vehicle System (Autonomous UGV)
  What: Autonomous ground vehicle with waypoint navigation and obstacle avoidance indoors and outdoors
  Sensors: LiDAR, Ultrasonic, GPS
  How: MATLAB/Simulink for Guidance-Navigation-Control (GNC); ROS for integration; Arduino for electrical
  Results: 100% outdoor waypoint success, 75% indoor waypoint success with obstacle avoidance
  Best for roles requiring: GNC, autonomous navigation, field robotics, UGV/UAS, sensor integration

PROJECT 4 — Jetson Xavier + Raspberry Pi Integrated System
  What: Edge robotics system combining computer vision (face detection) and motor control
  How: Jetson Xavier for CV/inference; Raspberry Pi for motor control; integrated into single system
  Best for roles requiring: edge ML, embedded robotics, Jetson, perception + actuation integration

PHD RESEARCH — Edge Resource Forecasting (Dell-sponsored)
  What: Hybrid predictive framework for edge compute resource usage forecasting
  How: Markov-based stochastic process + S4 neural networks + Predictive Confidence Modeling (PCM)
  Context: Graduate Research Assistant at UTA Research Institute
  Best for roles requiring: edge AI, S4/SSM models, predictive systems, ML for systems optimization

=== BINOY'S HARD SKILLS ===
Languages: Python (NumPy, Pandas), MATLAB/Simulink, C, JAX/FLAX, PyTorch, SimPy
Technologies: Control Theory (PID, LQR), System Dynamics, State Space Modeling,
              Sensor Fusion (Kalman Filter/UKF), Discrete Event Simulation, Queueing Theory
Hardware: Jetson Xavier, Raspberry Pi, Arduino, Decawave UWB sensors, turtlebot2i

=== WHAT BINOY IS TARGETING ===
- Robotics / Autonomous Systems / Drone / AV companies
- Research-forward startups (YC-backed, defense tech, space)
- Roles involving: state estimation, GNC, sensor fusion, edge ML, control systems
- NOT interested in: PLC, SCADA, DCS, manufacturing automation, industrial controls
"""
