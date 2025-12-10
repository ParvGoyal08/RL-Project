# Hierarchical Agent Testing in Gazebo Simulation

This document explains how to test trained hierarchical navigation models (Subgoal Agent + Motion Agent) in the Gazebo simulation environment.

## Overview

The hierarchical agent testing framework allows you to evaluate trained hierarchical models in the same Gazebo simulation environments used for training other agents (DDPG, TD3, DQN). This provides a consistent evaluation platform for comparing different navigation approaches.

## Architecture

The hierarchical testing environment consists of:

1. **Subgoal Agent (SA)**: High-level planner that predicts intermediate subgoals
2. **Motion Agent (MA)**: Low-level controller that executes motion to reach subgoals
3. **ROS2 Integration**: Interfaces with Gazebo simulation via ROS2 topics and services
4. **Testing Node**: Coordinates the SA and MA, collects metrics, and manages episodes

## Prerequisites

Before testing, ensure you have:

1. Trained hierarchical models:
   - Motion Agent (MA) model file (`.pth`)
   - Subgoal Agent (SA) model file (`.pth`)

2. Built the workspace:
   ```bash
   colcon build
   source install/setup.bash
   ```

## Testing Process

### Method 1: Using ROS2 Run (Recommended)

This method provides the most control and is similar to how other agents are tested.

**Step 1: Launch Gazebo Simulation**

Open a terminal and launch your desired stage:

```bash
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage4.launch.py
```

Available stages: `stage1` through `stage10`

**Step 2: Launch Goal Spawner**

In a second terminal:

```bash
ros2 run turtlebot3_drl gazebo_goals
```

This node handles goal generation in the simulation.

**Step 3: Run Hierarchical Test Agent**

In a third terminal:

```bash
ros2 run turtlebot3_drl test_hierarchical_agent [MA_MODEL_PATH] [SA_MODEL_PATH] [NUM_EPISODES]
```

Example:

```bash
ros2 run turtlebot3_drl test_hierarchical_agent \
    models/hierarchical/session_20231201_120000/ma/ma_converged.pth \
    models/hierarchical/session_20231201_120000/sa/sa_best.pth \
    10
```

**Arguments:**
- `MA_MODEL_PATH`: Path to the trained Motion Agent model
- `SA_MODEL_PATH`: Path to the trained Subgoal Agent model
- `NUM_EPISODES`: Number of test episodes to run (default: 10)

### Method 2: Using Launch File

Alternatively, you can use the provided launch file:

```bash
ros2 launch turtlebot3_drl test_hierarchical.launch.py \
    ma_model:=models/hierarchical/ma_converged.pth \
    sa_model:=models/hierarchical/sa_best.pth \
    num_episodes:=10
```

**Note:** You still need to launch Gazebo and the goal spawner separately before using the launch file.

## Complete Testing Setup

Here's a complete example using 4 terminals:

**Terminal 1: Gazebo**
```bash
source install/setup.bash
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage4.launch.py
```

**Terminal 2: Goal Spawner**
```bash
source install/setup.bash
ros2 run turtlebot3_drl gazebo_goals
```

**Terminal 3: Hierarchical Tester**
```bash
source install/setup.bash
ros2 run turtlebot3_drl test_hierarchical_agent \
    src/turtlebot3_drl/model/hierarchical/session_latest/ma/ma_converged.pth \
    src/turtlebot3_drl/model/hierarchical/session_latest/sa/sa_best.pth \
    10
```

## Understanding the Output

During testing, you'll see output like:

```
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
```

### Episode Outcomes

- **goal_reached**: Robot successfully reached the goal
- **collision**: Robot collided with an obstacle or wall
- **timeout**: Episode exceeded maximum time/steps

### Final Summary

At the end of testing, you'll see a summary:

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

You can test your hierarchical models on different complexity stages:

- **Stage 1-3**: Simple environments (good for initial testing)
- **Stage 4-6**: Medium complexity with moving obstacles
- **Stage 7-9**: Complex environments with multiple obstacles
- **Stage 10**: Very complex scenario

Simply change the stage number in the Gazebo launch command:

```bash
ros2 launch turtlebot3_gazebo turtlebot3_drl_stage9.launch.py
```

## Comparing with Other Agents

To compare hierarchical performance with other agents (DDPG, TD3, DQN):

1. Test hierarchical agent as described above
2. Test other agents using:
   ```bash
   ros2 run turtlebot3_drl test_agent ddpg 'examples/ddpg_0' 8000
   ```

Both testing frameworks provide similar metrics, allowing for fair comparison.

## Troubleshooting

### Model Not Found Error

**Problem:** `MA model not found: [path]`

**Solution:** 
- Check that the model path is correct
- Use absolute paths or paths relative to where you run the command
- Verify the model file exists: `ls [path]`

### No Sensor Data

**Problem:** Tester hangs waiting for sensor data

**Solution:**
- Ensure Gazebo simulation is running and fully loaded
- Check that the robot is spawned: `ros2 topic echo /odom`
- Verify LiDAR is publishing: `ros2 topic echo /scan`

### Goal Service Not Available

**Problem:** `Waiting for goal_comm service...`

**Solution:**
- Ensure the goal spawner node is running
- Check service is available: `ros2 service list | grep goal_comm`

### Poor Performance

**Problem:** Agent performs poorly even with trained models

**Solution:**
- Verify you loaded the correct models (MA and SA paths not swapped)
- Check if models were trained for the current stage
- Ensure testing environment matches training environment

## Model Paths

After training with the hierarchical trainer, models are saved in:

```
src/turtlebot3_drl/model/hierarchical/session_[timestamp]/
├── ma/
│   ├── ma_converged.pth    # Use this for testing (converged MA)
│   ├── ma_ep500.pth
│   └── ma_final.pth
└── sa/
    ├── sa_best.pth         # Use this for testing (best SA)
    ├── sa_ep500.pth
    └── sa_final.pth
```

Recommended models for testing:
- **MA**: `ma_converged.pth` (achieved 50 consecutive successes)
- **SA**: `sa_best.pth` (highest success rate during training)

## Advanced Usage

### Custom Configuration

To test with custom configuration:

1. Modify `hierarchical/config.py`
2. Rebuild: `colcon build --packages-select turtlebot3_drl`
3. Source and test as usual

### Logging Test Results

Test results can be logged by redirecting output:

```bash
ros2 run turtlebot3_drl test_hierarchical_agent \
    models/ma.pth models/sa.pth 50 \
    2>&1 | tee test_results.log
```

## Integration with Training

The testing environment is designed to seamlessly work with models trained using:

```bash
# Training (from run_hierarchical.sh)
./run_hierarchical.sh train-full

# Testing (using trained models)
ros2 run turtlebot3_drl test_hierarchical_agent \
    src/turtlebot3_drl/model/hierarchical/session_latest/ma/ma_converged.pth \
    src/turtlebot3_drl/model/hierarchical/session_latest/sa/sa_best.pth
```

## See Also

- [Hierarchical Training Guide](../run_hierarchical.sh) - Training hierarchical models
- [Main README](../README.md) - Overall project documentation
- [Testing Other Agents](../README.md#loading-a-stored-model) - Testing DDPG/TD3/DQN models

## Support

For issues or questions about hierarchical testing:
1. Check that all prerequisites are met
2. Verify model files exist and are not corrupted
3. Ensure ROS2 environment is properly sourced
4. Review the hierarchical configuration in `hierarchical/config.py`
