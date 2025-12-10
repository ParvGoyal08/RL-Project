#!/bin/bash
# =============================================================================
# Hierarchical DRL Navigation Testing Script
# =============================================================================
# Quick script to test trained hierarchical navigation models in Gazebo.
#
# Usage:
#   ./test_hierarchical.sh [ma_model] [sa_model] [num_episodes] [stage]
#
# Examples:
#   ./test_hierarchical.sh models/ma.pth models/sa.pth 10 4
#   ./test_hierarchical.sh  # Uses defaults
# =============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "============================================================"
    echo "  Hierarchical DRL Navigation - Testing"
    echo "============================================================"
    echo -e "${NC}"
}

print_help() {
    print_header
    echo "Usage: $0 [ma_model] [sa_model] [num_episodes] [stage]"
    echo ""
    echo "Arguments:"
    echo "  ma_model       Path to trained Motion Agent model (.pth)"
    echo "  sa_model       Path to trained Subgoal Agent model (.pth)"
    echo "  num_episodes   Number of test episodes (default: 10)"
    echo "  stage          Gazebo stage (1-10, default: 4)"
    echo ""
    echo "Examples:"
    echo "  $0 models/ma_converged.pth models/sa_best.pth 10 4"
    echo "  $0 models/ma.pth models/sa.pth 5 9"
    echo ""
    echo "Before running:"
    echo "  1. Make sure workspace is built: colcon build"
    echo "  2. Source the workspace: source install/setup.bash"
    echo ""
}

# Parse arguments
MA_MODEL="${1:-models/hierarchical/ma_converged.pth}"
SA_MODEL="${2:-models/hierarchical/sa_best.pth}"
NUM_EPISODES="${3:-10}"
STAGE="${4:-4}"

# Check for help
if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    print_help
    exit 0
fi

print_header

# Validate models exist
if [ ! -f "$MA_MODEL" ]; then
    echo -e "${RED}ERROR: MA model not found: $MA_MODEL${NC}"
    echo "Please provide a valid path to the Motion Agent model."
    exit 1
fi

if [ ! -f "$SA_MODEL" ]; then
    echo -e "${RED}ERROR: SA model not found: $SA_MODEL${NC}"
    echo "Please provide a valid path to the Subgoal Agent model."
    exit 1
fi

echo -e "${GREEN}Configuration:${NC}"
echo "  MA Model:     $MA_MODEL"
echo "  SA Model:     $SA_MODEL"
echo "  Episodes:     $NUM_EPISODES"
echo "  Stage:        $STAGE"
echo ""

# Check if workspace is sourced
if [ -z "$AMENT_PREFIX_PATH" ]; then
    echo -e "${YELLOW}WARNING: ROS2 workspace not sourced!${NC}"
    echo "Run: source install/setup.bash"
    exit 1
fi

# Instructions
echo -e "${YELLOW}Setup Instructions:${NC}"
echo ""
echo "You need to run these commands in separate terminals:"
echo ""
echo -e "${GREEN}Terminal 1 - Gazebo Simulation:${NC}"
echo "  ros2 launch turtlebot3_gazebo turtlebot3_drl_stage${STAGE}.launch.py"
echo ""
echo -e "${GREEN}Terminal 2 - Goal Spawner:${NC}"
echo "  ros2 run turtlebot3_drl gazebo_goals"
echo ""
echo -e "${GREEN}Terminal 3 - Hierarchical Tester:${NC}"
echo "  ros2 run turtlebot3_drl test_hierarchical_agent \\"
echo "    $MA_MODEL \\"
echo "    $SA_MODEL \\"
echo "    $NUM_EPISODES"
echo ""
echo -e "${YELLOW}Or run the tester now if Gazebo and goals are already running:${NC}"
echo ""

# Ask user if they want to run the tester
read -p "Launch hierarchical tester now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Launching hierarchical tester...${NC}"
    ros2 run turtlebot3_drl test_hierarchical_agent "$MA_MODEL" "$SA_MODEL" "$NUM_EPISODES"
else
    echo -e "${YELLOW}Setup complete. Launch tester manually when ready.${NC}"
fi
