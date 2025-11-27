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


def main():
    run_comparison_test(num_schedules=50, num_visualizations=3)
    statistical_analysis()


def demo():
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

    print("Time together using intelligent pathfinding: ", intelligent_time)
    print("Time together using naive pathfinding: ", naive_time)


if __name__ == "__main__":
    main()
    # demo()
