"""
Hierarchical DRL Navigation Tester

Test trained hierarchical models (SA + MA) in Gazebo simulation.
Similar to test_agent for DDPG/TD3/DQN but for hierarchical architecture.

Usage:
    ros2 run turtlebot3_drl test_hierarchical_agent [ma_model_path] [sa_model_path]
    
Example:
    ros2 run turtlebot3_drl test_hierarchical_agent models/ma_converged.pth models/sa_best.pth
"""

import os
import sys
import time
import math
import numpy as np
from typing import Tuple, Dict, Any, Optional

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from turtlebot3_msgs.srv import Goal
from std_srvs.srv import Empty

import torch

# Handle imports for both standalone and installed package
try:
    from ..config import HierarchicalConfig
    from ..agents.subgoal_agent import SubgoalAgent
    from ..agents.motion_agent import MotionAgent
    from ..preprocessing.lidar_processor import LidarProcessor
    from ..planners.waypoint_manager import WaypointManager
    from ..planners.astar import AStarPlanner
    from ..environments.scenes import SceneType, SceneFactory
except ImportError:
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _hierarchical_dir = os.path.dirname(_current_dir)
    _turtlebot3_drl_dir = os.path.dirname(_hierarchical_dir)
    if _turtlebot3_drl_dir not in sys.path:
        sys.path.insert(0, _turtlebot3_drl_dir)
    
    from hierarchical.config import HierarchicalConfig
    from hierarchical.agents.subgoal_agent import SubgoalAgent
    from hierarchical.agents.motion_agent import MotionAgent
    from hierarchical.preprocessing.lidar_processor import LidarProcessor
    from hierarchical.planners.waypoint_manager import WaypointManager
    from hierarchical.planners.astar import AStarPlanner
    from hierarchical.environments.scenes import SceneType, SceneFactory


class HierarchicalTester(Node):
    """
    ROS2 Node for testing trained hierarchical navigation models.
    
    Integrates with Gazebo simulation environment and runs the hierarchical
    control loop: SA predicts subgoals -> MA executes motion.
    """
    
    def __init__(
        self,
        ma_model_path: str,
        sa_model_path: str,
        config: HierarchicalConfig = None,
        num_episodes: int = 10
    ):
        """
        Initialize hierarchical tester.
        
        Args:
            ma_model_path: Path to trained Motion Agent model
            sa_model_path: Path to trained Subgoal Agent model
            config: Configuration object
            num_episodes: Number of test episodes to run
        """
        super().__init__('hierarchical_tester')
        
        if config is None:
            config = HierarchicalConfig()
        self.config = config
        
        self.num_episodes = num_episodes
        self.episode_count = 0
        
        # Device
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.get_logger().info(f"Using device: {self.device}")
        
        # Load agents
        self.ma = MotionAgent(config, device=self.device)
        self.sa = SubgoalAgent(config, device=self.device)
        
        if os.path.exists(ma_model_path):
            self.ma.load(ma_model_path)
            self.get_logger().info(f"Loaded MA model from {ma_model_path}")
        else:
            self.get_logger().error(f"MA model not found: {ma_model_path}")
            raise FileNotFoundError(f"MA model not found: {ma_model_path}")
        
        if os.path.exists(sa_model_path):
            self.sa.load(sa_model_path)
            self.get_logger().info(f"Loaded SA model from {sa_model_path}")
        else:
            self.get_logger().error(f"SA model not found: {sa_model_path}")
            raise FileNotFoundError(f"SA model not found: {sa_model_path}")
        
        # Freeze agents (testing mode)
        self.ma.freeze()
        self.sa.freeze()
        
        # Components
        self.lidar_processor = LidarProcessor(
            input_rays=config.LIDAR_RAW_RAYS,
            output_rays=config.LIDAR_RAYS,
            max_range=config.LIDAR_MAX_RANGE,
            clip_range=config.LIDAR_CLIP_RANGE,
            num_sectors=config.LIDAR_SECTORS
        )
        
        self.waypoint_manager = WaypointManager(
            num_waypoints=config.NUM_WAYPOINTS,
            waypoint_spacing=config.WAYPOINT_SPACING
        )
        
        self.astar_planner = AStarPlanner(
            grid_resolution=config.ASTAR_RESOLUTION,
            robot_radius=config.ASTAR_ROBOT_RADIUS,
            inflation_radius=config.ASTAR_INFLATION_RADIUS
        )
        
        # State
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_theta = 0.0
        self.robot_v = 0.0
        self.robot_omega = 0.0
        
        self.goal_x = 0.0
        self.goal_y = 0.0
        
        self.lidar_scan: Optional[np.ndarray] = None
        self.global_path = []
        
        self.current_subgoal: Optional[Tuple[float, float]] = None
        self.sa_step_count = 0
        self.ma_step_count = 0
        self.total_step_count = 0
        
        # Episode metrics
        self.episode_reward = 0.0
        self.episode_success = False
        self.episode_start_time = None
        
        # Statistics
        self.success_count = 0
        self.collision_count = 0
        self.timeout_count = 0
        
        # ROS2 publishers and subscribers
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
        self.scan_sub = self.create_subscription(
            LaserScan, 'scan', self.scan_callback, 10
        )
        
        self.odom_sub = self.create_subscription(
            Odometry, 'odom', self.odom_callback, 10
        )
        
        # Service clients
        self.goal_client = self.create_client(Goal, 'goal_comm')
        self.pause_client = self.create_client(Empty, '/pause_physics')
        self.unpause_client = self.create_client(Empty, '/unpause_physics')
        
        # Wait for services
        while not self.goal_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for goal_comm service...')
        
        self.get_logger().info("Hierarchical tester initialized successfully")
    
    def scan_callback(self, msg: LaserScan):
        """Process LiDAR scan."""
        self.lidar_scan = np.array(msg.ranges)
    
    def odom_callback(self, msg: Odometry):
        """Process odometry."""
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        
        # Extract yaw from quaternion
        qx = msg.pose.pose.orientation.x
        qy = msg.pose.pose.orientation.y
        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w
        
        siny_cosp = 2 * (qw * qz + qx * qy)
        cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
        self.robot_theta = math.atan2(siny_cosp, cosy_cosp)
        
        self.robot_v = msg.twist.twist.linear.x
        self.robot_omega = msg.twist.twist.angular.z
    
    def pause_simulation(self):
        """Pause Gazebo simulation."""
        req = Empty.Request()
        self.pause_client.call_async(req)
    
    def unpause_simulation(self):
        """Unpause Gazebo simulation."""
        req = Empty.Request()
        self.unpause_client.call_async(req)
    
    def request_new_goal(self):
        """Request a new goal from the environment."""
        req = Goal.Request()
        future = self.goal_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        
        if future.result() is not None:
            result = future.result()
            self.goal_x = result.pose_x
            self.goal_y = result.pose_y
            self.get_logger().info(f"New goal: ({self.goal_x:.2f}, {self.goal_y:.2f})")
        else:
            self.get_logger().error("Failed to get new goal")
    
    def publish_velocity(self, v: float, omega: float):
        """Publish velocity command."""
        cmd = Twist()
        cmd.linear.x = float(v)
        cmd.angular.z = float(omega)
        self.cmd_vel_pub.publish(cmd)
    
    def stop_robot(self):
        """Stop the robot."""
        self.publish_velocity(0.0, 0.0)
    
    def check_termination(self) -> Tuple[bool, str]:
        """
        Check episode termination.
        
        Returns:
            (done, reason)
        """
        # Goal reached
        dist_to_goal = math.sqrt(
            (self.goal_x - self.robot_x)**2 +
            (self.goal_y - self.robot_y)**2
        )
        if dist_to_goal < self.config.GOAL_THRESHOLD:
            return True, 'goal_reached'
        
        # Collision (check minimum LiDAR reading)
        if self.lidar_scan is not None:
            min_dist = np.min(self.lidar_scan)
            if min_dist < self.config.COLLISION_DISTANCE:
                return True, 'collision'
        
        # Timeout
        if self.total_step_count >= self.config.EPISODE_TIMEOUT:
            return True, 'timeout'
        
        return False, 'none'
    
    def get_observation(self) -> Dict[str, Any]:
        """Get current observation for SA."""
        # Process LiDAR
        if self.lidar_scan is None:
            lidar = np.ones(self.config.LIDAR_RAYS) * self.config.LIDAR_MAX_RANGE
        else:
            lidar = self.lidar_processor.process_normalized(self.lidar_scan)
        
        # Get waypoints
        waypoints = self.waypoint_manager.get_waypoints_robot_frame(
            self.robot_x, self.robot_y, self.robot_theta
        )
        waypoints_flat = waypoints.flatten() if waypoints is not None else np.zeros(10)
        
        return {
            'lidar': lidar,
            'waypoints': waypoints_flat
        }
    
    def get_ma_state(self) -> np.ndarray:
        """Get MA state."""
        if self.current_subgoal is None:
            return np.zeros(5, dtype=np.float32)
        
        px, py = self.current_subgoal
        theta_diff = math.atan2(py, px)
        
        # Normalize to [-pi, pi]
        while theta_diff > math.pi:
            theta_diff -= 2 * math.pi
        while theta_diff < -math.pi:
            theta_diff += 2 * math.pi
        
        return np.array([
            self.robot_v,
            self.robot_omega,
            px,
            py,
            theta_diff
        ], dtype=np.float32)
    
    def update_subgoal_robot_frame(self, v: float, omega: float, dt: float):
        """Update subgoal in robot frame after robot moved."""
        if self.current_subgoal is None:
            return
        
        px, py = self.current_subgoal
        
        # Robot moved forward and rotated
        # Subgoal appears to move backward and rotate
        px -= v * dt
        
        # Rotate
        c = math.cos(-omega * dt)
        s = math.sin(-omega * dt)
        new_px = c * px - s * py
        new_py = s * px + c * py
        
        self.current_subgoal = (new_px, new_py)
    
    def run_episode(self) -> Dict[str, Any]:
        """
        Run one test episode.
        
        Returns:
            Episode metrics
        """
        self.episode_count += 1
        self.get_logger().info(f"\n{'='*60}")
        self.get_logger().info(f"Episode {self.episode_count}/{self.num_episodes}")
        self.get_logger().info(f"{'='*60}")
        
        # Reset episode state
        self.sa_step_count = 0
        self.ma_step_count = 0
        self.total_step_count = 0
        self.episode_reward = 0.0
        self.episode_success = False
        self.current_subgoal = None
        
        # Pause simulation
        self.pause_simulation()
        time.sleep(0.2)
        
        # Request new goal
        self.request_new_goal()
        time.sleep(0.5)
        
        # Wait for initial sensor data
        while self.lidar_scan is None:
            rclpy.spin_once(self, timeout_sec=0.1)
        
        # Plan initial A* path
        # For simplicity, we'll skip A* planning in test mode
        # and just use straight waypoints toward goal
        self.global_path = [(self.goal_x, self.goal_y)]
        self.waypoint_manager.set_path(self.global_path)
        
        # Unpause simulation
        self.unpause_simulation()
        time.sleep(0.5)
        
        self.episode_start_time = time.time()
        
        done = False
        termination_reason = 'none'
        
        # Main episode loop
        while not done:
            # SA step: predict subgoal
            obs = self.get_observation()
            lidar = obs['lidar']
            waypoints = obs['waypoints']
            
            sa_action, should_replan = self.sa.select_action(
                lidar, waypoints, add_noise=False
            )
            
            # Convert to subgoal
            l, theta = sa_action[0], sa_action[1]
            subgoal_x = l * math.cos(theta)
            subgoal_y = l * math.sin(theta)
            self.current_subgoal = (subgoal_x, subgoal_y)
            
            self.sa_step_count += 1
            
            # Execute MA steps to reach subgoal
            for _ in range(self.config.MA_STEPS_PER_SA):
                # Get MA state
                ma_state = self.get_ma_state()
                
                # MA predicts action
                ma_action = self.ma.select_action(ma_state, add_noise=False)
                
                # Apply velocity
                v, omega = ma_action[0], ma_action[1]
                self.publish_velocity(v, omega)
                
                # Wait for MA timestep
                time.sleep(self.config.MA_TIME_STEP)
                
                # Update subgoal in robot frame
                self.update_subgoal_robot_frame(v, omega, self.config.MA_TIME_STEP)
                
                # Check termination
                self.total_step_count += 1
                self.ma_step_count += 1
                
                rclpy.spin_once(self, timeout_sec=0.01)
                
                done, termination_reason = self.check_termination()
                if done:
                    break
            
            # Log progress
            if self.sa_step_count % 10 == 0:
                dist_to_goal = math.sqrt(
                    (self.goal_x - self.robot_x)**2 +
                    (self.goal_y - self.robot_y)**2
                )
                self.get_logger().info(
                    f"SA steps: {self.sa_step_count}, "
                    f"Dist to goal: {dist_to_goal:.2f}m"
                )
        
        # Stop robot
        self.stop_robot()
        
        # Episode complete
        episode_time = time.time() - self.episode_start_time
        
        success = termination_reason == 'goal_reached'
        if success:
            self.success_count += 1
        elif termination_reason == 'collision':
            self.collision_count += 1
        elif termination_reason == 'timeout':
            self.timeout_count += 1
        
        self.get_logger().info(f"\nEpisode {self.episode_count} complete:")
        self.get_logger().info(f"  Result: {termination_reason}")
        self.get_logger().info(f"  Time: {episode_time:.1f}s")
        self.get_logger().info(f"  SA steps: {self.sa_step_count}")
        self.get_logger().info(f"  MA steps: {self.ma_step_count}")
        
        return {
            'episode': self.episode_count,
            'success': success,
            'termination': termination_reason,
            'time': episode_time,
            'sa_steps': self.sa_step_count,
            'ma_steps': self.ma_step_count
        }
    
    def run(self):
        """Run all test episodes."""
        self.get_logger().info("\n" + "="*60)
        self.get_logger().info("HIERARCHICAL AGENT TESTING")
        self.get_logger().info("="*60)
        self.get_logger().info(f"Episodes: {self.num_episodes}")
        self.get_logger().info(f"Device: {self.device}")
        self.get_logger().info("")
        
        results = []
        
        for _ in range(self.num_episodes):
            result = self.run_episode()
            results.append(result)
            
            # Pause between episodes
            time.sleep(2.0)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print testing summary."""
        self.get_logger().info("\n" + "="*60)
        self.get_logger().info("TESTING SUMMARY")
        self.get_logger().info("="*60)
        self.get_logger().info(f"Total episodes: {self.episode_count}")
        self.get_logger().info(f"Successes: {self.success_count}")
        self.get_logger().info(f"Collisions: {self.collision_count}")
        self.get_logger().info(f"Timeouts: {self.timeout_count}")
        
        if self.episode_count > 0:
            success_rate = (self.success_count / self.episode_count) * 100
            self.get_logger().info(f"Success rate: {success_rate:.1f}%")
        
        self.get_logger().info("="*60)


def main(args=None):
    """Main entry point."""
    rclpy.init(args=args)
    
    # Parse arguments
    if len(sys.argv) < 3:
        print("Usage: ros2 run turtlebot3_drl test_hierarchical_agent [ma_model] [sa_model] [num_episodes]")
        print("Example: ros2 run turtlebot3_drl test_hierarchical_agent models/ma_converged.pth models/sa_best.pth 10")
        sys.exit(1)
    
    ma_model_path = sys.argv[1]
    sa_model_path = sys.argv[2]
    num_episodes = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    # Create tester
    try:
        tester = HierarchicalTester(
            ma_model_path=ma_model_path,
            sa_model_path=sa_model_path,
            num_episodes=num_episodes
        )
        
        # Run testing
        tester.run()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
