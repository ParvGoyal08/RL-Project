# Hierarchical Agent Quick Start Guide

This guide provides a quick overview of testing hierarchical navigation models in Gazebo.

## What is Hierarchical Navigation?

The hierarchical navigation system uses two agents:
- **Subgoal Agent (SA)**: High-level planner that decides intermediate subgoals
- **Motion Agent (MA)**: Low-level controller that executes motion commands

This architecture enables more efficient navigation in complex environments.

## Quick Testing (3 Steps)

### Step 1: Launch Gazebo Simulation

Open a terminal and start the Gazebo environment:

```bash
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage4.launch.py
```

Wait for Gazebo to fully load (you should see the robot and environment).

### Step 2: Start Goal Spawner

In a new terminal:

```bash
ros2 run turtlebot3_drl gazebo_goals
```

This node will generate navigation goals for the robot.

### Step 3: Test Your Hierarchical Model

In a third terminal:

```bash
ros2 run turtlebot3_drl test_hierarchical_agent \
    path/to/ma_model.pth \
    path/to/sa_model.pth \
    10
```

Replace the paths with your actual model files. The last number (10) is the number of test episodes.

## Using the Convenience Script

Alternatively, use the provided shell script:

```bash
./test_hierarchical.sh models/ma.pth models/sa.pth 10 4
```

Arguments:
1. MA model path
2. SA model path
3. Number of episodes (default: 10)
4. Gazebo stage (default: 4)

## Model Locations

After training with `./run_hierarchical.sh train-full`, models are saved in:

```
src/turtlebot3_drl/model/hierarchical/session_[timestamp]/
├── ma/
│   └── ma_converged.pth    ← Use this for MA
└── sa/
    └── sa_best.pth         ← Use this for SA
```

## Example with Full Paths

```bash
# Terminal 1
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage4.launch.py

# Terminal 2
ros2 run turtlebot3_drl gazebo_goals

# Terminal 3
ros2 run turtlebot3_drl test_hierarchical_agent \
    src/turtlebot3_drl/model/hierarchical/session_20231201_120000/ma/ma_converged.pth \
    src/turtlebot3_drl/model/hierarchical/session_20231201_120000/sa/sa_best.pth \
    10
```

## Understanding the Output

You'll see output like this for each episode:

```
============================================================
Episode 1/10
============================================================
New goal: (2.50, 1.80)
SA steps: 10, Dist to goal: 1.45m
SA steps: 20, Dist to goal: 0.82m

Episode 1 complete:
  Result: goal_reached
  Time: 8.3s
  SA steps: 32
  MA steps: 128
```

### Possible Outcomes:
- **goal_reached**: Success! Robot reached the goal
- **collision**: Robot hit an obstacle
- **timeout**: Episode took too long

### Final Summary:
```
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

## Testing on Different Stages

Change the stage number in Step 1 to test in different environments:

```bash
# Easy environments
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage1.launch.py  # Stage 1
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage2.launch.py  # Stage 2

# Medium complexity
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage4.launch.py  # Stage 4
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage5.launch.py  # Stage 5

# Complex environments
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage9.launch.py  # Stage 9
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage10.launch.py # Stage 10
```

## Troubleshooting

### "Model not found" error
- Check that the file paths are correct
- Use `ls` to verify files exist
- Try using absolute paths

### "Waiting for goal_comm service..."
- Make sure the goal spawner is running (Step 2)
- Check: `ros2 service list | grep goal_comm`

### No sensor data
- Ensure Gazebo has fully loaded
- Check topics: `ros2 topic list`
- Verify: `ros2 topic echo /scan`

### Robot doesn't move
- Verify models are loaded correctly
- Check velocity topic: `ros2 topic echo /cmd_vel`
- Ensure simulation is not paused

## Comparing with Other Agents

To compare performance, test other agents on the same stage:

```bash
# Test DDPG agent
ros2 run turtlebot3_drl test_agent ddpg 'examples/ddpg_0' 8000

# Test TD3 agent
ros2 run turtlebot3_drl test_agent td3 'examples/td3_0' 7400

# Test hierarchical agent
ros2 run turtlebot3_drl test_hierarchical_agent models/ma.pth models/sa.pth 10
```

All agents use the same Gazebo environment and evaluation metrics.

## Next Steps

- **Detailed Documentation**: See [docs/HIERARCHICAL_TESTING.md](docs/HIERARCHICAL_TESTING.md)
- **Training Guide**: See [run_hierarchical.sh](run_hierarchical.sh)
- **Main README**: See [README.md](README.md)

## Common Commands Reference

```bash
# Launch Gazebo stage 4
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage4.launch.py

# Launch goal spawner
ros2 run turtlebot3_drl gazebo_goals

# Test hierarchical agent (10 episodes)
ros2 run turtlebot3_drl test_hierarchical_agent [MA] [SA] 10

# Quick test with script
./test_hierarchical.sh [MA] [SA] 10 4

# Check available services
ros2 service list

# Check available topics
ros2 topic list

# Monitor robot velocity
ros2 topic echo /cmd_vel

# Monitor LiDAR
ros2 topic echo /scan
```

---

**For more details, see the full documentation in [docs/HIERARCHICAL_TESTING.md](docs/HIERARCHICAL_TESTING.md)**
