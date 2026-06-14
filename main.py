import argparse
import os

from compare_results import run_comparison_test
from statistical_analysis import statistical_analysis
from multi_agent_pathfinding import (
    entire_friend_day_path,
    entire_agent_day_path,
    total_time_together,
    total_time_together_naive,
)
from graph import build_campus_network
from visualization import visualize_path_segments, visualize_path
from config import PLACE_NAME


def run_pipeline(
    num_schedules=50,
    num_visualizations=3,
    output_csv="results/comparison_results.csv",
):
    run_comparison_test(
        num_schedules=num_schedules,
        output_csv=output_csv,
        num_visualizations=num_visualizations,
    )
    statistical_analysis(output_csv)


def demo():
    os.makedirs("results/demo", exist_ok=True)

    G, building_centroids = build_campus_network(PLACE_NAME)
    friend_path = "schedules/demo/friend.json"
    agent_path = "schedules/demo/agent.json"
    temperature = 20
    precipitation = 0

    friend_day_path = entire_friend_day_path(G, friend_path, precipitation, temperature)
    agent_day_path = entire_agent_day_path(
        G, agent_path, friend_path, friend_day_path, precipitation, temperature
    )

    visualize_path(
        G,
        building_centroids,
        friend_day_path[0]["path"],
        "Friend Day Path",
        filename="results/demo/friend_day_path.png",
    )
    visualize_path_segments(
        G,
        building_centroids,
        agent_day_path,
        "Agent Day Path",
        filename="results/demo/agent_day_path.png",
    )

    intelligent_time = total_time_together(agent_day_path)
    naive_time = total_time_together_naive(G, friend_day_path, agent_day_path)

    print("Time together using intelligent pathfinding:", intelligent_time)
    print("Time together using naive pathfinding:", naive_time)
    print("Saved demo visualizations to results/demo/")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Carleton multi-agent pathfinding simulation."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="generate visualizations for the checked-in demo schedules",
    )
    parser.add_argument(
        "--num-schedules",
        type=int,
        default=50,
        help="number of generated schedule pairs to compare",
    )
    parser.add_argument(
        "--num-visualizations",
        type=int,
        default=3,
        help="number of simulations to visualize during comparison runs",
    )
    parser.add_argument(
        "--output-csv",
        default="results/comparison_results.csv",
        help="path for comparison CSV output",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="generate comparison CSV without running statistical analysis",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.demo:
        demo()
        return

    run_comparison_test(
        num_schedules=args.num_schedules,
        output_csv=args.output_csv,
        num_visualizations=args.num_visualizations,
    )

    if not args.skip_analysis:
        statistical_analysis(args.output_csv)


if __name__ == "__main__":
    main()
