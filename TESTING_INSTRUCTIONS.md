# Hierarchical Agent Testing Instructions

## Quick Summary

I've created a complete testing environment for the hierarchical DRL agent. Here's how to use it:

## Prerequisites

1. **Build the workspace:**
   ```bash
   cd /path/to/RL-Project
   colcon build --packages-select turtlebot3_drl
   source install/setup.bash
   ```

2. **Have trained models:**
   - Motion Agent (MA) model: `ma_converged.pth` or `ma_final.pth`
   - Subgoal Agent (SA) model: `sa_best.pth` or `sa_final.pth`

## Method 1: Using ROS2 Commands (Recommended)

### Terminal 1: Launch Gazebo Simulation
```bash
source install/setup.bash
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage4.launch.py
```

Wait for Gazebo to fully load (you should see the robot in the environment).

### Terminal 2: Start Goal Spawner
```bash
source install/setup.bash
ros2 run turtlebot3_drl gazebo_goals
```

This will generate random goals for the robot to navigate to.

### Terminal 3: Run Hierarchical Test Agent
```bash
source install/setup.bash
ros2 run turtlebot3_drl test_hierarchical_agent \
    path/to/ma_model.pth \
    path/to/sa_model.pth \
    10
```

**Example with actual paths:**
```bash
ros2 run turtlebot3_drl test_hierarchical_agent \
    src/turtlebot3_drl/model/hierarchical/session_20231201_120000/ma/ma_converged.pth \
    src/turtlebot3_drl/model/hierarchical/session_20231201_120000/sa/sa_best.pth \
    10
```

## Method 2: Using the Convenience Script

```bash
./test_hierarchical.sh path/to/ma_model.pth path/to/sa_model.pth 10 4
```

**Arguments:**
- Arg 1: Path to MA model
- Arg 2: Path to SA model
- Arg 3: Number of test episodes (default: 10)
- Arg 4: Gazebo stage (1-10, default: 4)

**Example:**
```bash
./test_hierarchical.sh \
    src/turtlebot3_drl/model/hierarchical/ma_converged.pth \
    src/turtlebot3_drl/model/hierarchical/sa_best.pth \
    10 \
    4
```

## Method 3: Using Launch File

```bash
ros2 launch turtlebot3_drl test_hierarchical.launch.py \
    ma_model:=path/to/ma_model.pth \
    sa_model:=path/to/sa_model.pth \
    num_episodes:=10
```

**Note:** You still need to launch Gazebo (Terminal 1) and goal spawner (Terminal 2) first.

## Expected Output

When running, you should see output like:

```
============================================================
HIERARCHICAL AGENT TESTING
============================================================
Episodes: 10
Device: cuda

============================================================
Episode 1/10
============================================================
New goal: (2.50, 1.80)
SA steps: 10, Dist to goal: 1.45m
SA steps: 20, Dist to goal: 0.82m
SA steps: 30, Dist to goal: 0.25m

Episode 1 complete:
  Result: goal_reached
  Time: 8.3s
  SA steps: 32
  MA steps: 128

============================================================
TESTING SUMMARY
============================================================
Total episodes: 10
Successes: 8
Collisions: 1
Timeouts: 1
Success rate: 80.0%
============================================================
```

## Testing Different Stages

You can test on different complexity levels by changing the stage:

**Easy environments:**
```bash
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage1.launch.py  # Stage 1
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage2.launch.py  # Stage 2
```

**Medium complexity:**
```bash
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage4.launch.py  # Stage 4
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage5.launch.py  # Stage 5
```

**Complex environments:**
```bash
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage9.launch.py   # Stage 9
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage10.launch.py  # Stage 10
```

## Training Models First

If you don't have trained models yet, train them first:

```bash
# Full hierarchical training (MA + SA)
./run_hierarchical.sh train-full

# Or train individually
./run_hierarchical.sh train-ma      # Train Motion Agent
./run_hierarchical.sh train-sa      # Train Subgoal Agent
```

Models will be saved in:
```
src/turtlebot3_drl/model/hierarchical/session_[timestamp]/
├── ma/
│   ├── ma_converged.pth    ← Use this
│   ├── ma_ep500.pth
│   └── ma_final.pth
└── sa/
    ├── sa_best.pth         ← Use this
    ├── sa_ep500.pth
    └── sa_final.pth
```

## Troubleshooting

### "Model not found" error
- Check the file path is correct
- Use absolute paths or paths relative to your workspace root
- Verify files exist: `ls path/to/model.pth`

### "Waiting for goal_comm service..."
- Ensure the goal spawner is running (Terminal 2)
- Check: `ros2 service list | grep goal_comm`

### Robot doesn't move
- Verify Gazebo has fully loaded
- Check simulation is not paused
- Monitor velocity: `ros2 topic echo /cmd_vel`

### No LiDAR data
- Check Gazebo is running properly
- Verify topic: `ros2 topic echo /scan`

## File Locations

**Testing code:**
- `src/turtlebot3_drl/turtlebot3_drl/hierarchical/testing/hierarchical_tester.py`

**Launch file:**
- `src/turtlebot3_drl/launch/test_hierarchical.launch.py`

**Documentation:**
- `docs/HIERARCHICAL_TESTING.md` - Comprehensive guide
- `HIERARCHICAL_QUICKSTART.md` - Quick reference
- `README.md` - Updated with hierarchical section

**Convenience script:**
- `test_hierarchical.sh` - Interactive testing script

## Comparing with Other Agents

To compare performance with DDPG/TD3/DQN:

```bash
# Test DDPG
ros2 run turtlebot3_drl test_agent ddpg 'examples/ddpg_0' 8000

# Test TD3
ros2 run turtlebot3_drl test_agent td3 'examples/td3_0' 7400

# Test Hierarchical
ros2 run turtlebot3_drl test_hierarchical_agent \
    models/ma_converged.pth models/sa_best.pth 10
```

All use the same testing framework and metrics.

## Summary

The hierarchical agent testing works exactly like DDPG/TD3/DQN testing:
1. Launch Gazebo environment
2. Start goal spawner
3. Run test agent with model paths
4. View results and metrics

For more details, see:
- Full guide: `docs/HIERARCHICAL_TESTING.md`
- Quick start: `HIERARCHICAL_QUICKSTART.md`
