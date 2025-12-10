#!/usr/bin/env python3
#
# Launch file for testing hierarchical navigation agents
#
# This launch file starts the necessary nodes for testing trained hierarchical models.
# Similar to how other agents (DDPG, TD3, DQN) are tested but for hierarchical architecture.
#
# Usage:
#   ros2 launch turtlebot3_drl test_hierarchical.launch.py stage:=4
#
# Before running:
#   1. Launch Gazebo environment: ros2 launch turtlebot3_gazebo turtlebot3_drl_stage4.launch.py
#   2. Launch goal spawner: ros2 run turtlebot3_drl gazebo_goals
#   3. Then launch this file with model paths as parameters

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    """Generate launch description for hierarchical testing."""
    
    # Declare arguments
    ma_model_arg = DeclareLaunchArgument(
        'ma_model',
        default_value='models/hierarchical/ma_converged.pth',
        description='Path to trained Motion Agent model'
    )
    
    sa_model_arg = DeclareLaunchArgument(
        'sa_model',
        default_value='models/hierarchical/sa_best.pth',
        description='Path to trained Subgoal Agent model'
    )
    
    num_episodes_arg = DeclareLaunchArgument(
        'num_episodes',
        default_value='10',
        description='Number of test episodes'
    )
    
    # Get launch configurations
    ma_model = LaunchConfiguration('ma_model')
    sa_model = LaunchConfiguration('sa_model')
    num_episodes = LaunchConfiguration('num_episodes')
    
    # Hierarchical test agent node
    hierarchical_test_node = Node(
        package='turtlebot3_drl',
        executable='test_hierarchical_agent',
        name='hierarchical_tester',
        output='screen',
        arguments=[ma_model, sa_model, num_episodes],
        parameters=[{
            'use_sim_time': True
        }]
    )
    
    return LaunchDescription([
        ma_model_arg,
        sa_model_arg,
        num_episodes_arg,
        hierarchical_test_node
    ])
