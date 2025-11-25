import csv
import os
import random
from config import PLACE_NAME
from graph import build_campus_network
from schedule_generator import generate_schedule_pairs
from multi_agent_pathfinding import (
    entire_agent_day_path,
    entire_friend_day_path,
    entire_shortest_day_path,
    total_time_together,
    total_time_together_naive,
    total_travel_cost,
)
from visualization import visualize_path_segments, visualize_path


def run_comparison_test(
    num_schedules=20,
    output_csv="results/comparison_results.csv",
    num_visualizations=0,
):
    # build graph
    print("Building campus network...")
    G, building_centroids = build_campus_network(PLACE_NAME)

    # generate schedule pairs
    print(f"Generating {num_schedules} schedule pairs...")
    schedule_pairs = generate_schedule_pairs(num_pairs=num_schedules)

    # create output directories
    os.makedirs(
        os.path.dirname(output_csv) if os.path.dirname(output_csv) else ".",
        exist_ok=True,
    )

    if num_visualizations > 0:
        viz_dir = "results/visualizations"
        os.makedirs(viz_dir, exist_ok=True)

    # prepare CSV file
    results = []

    print(f"Running comparisons...")
    for i, (agent_path, friend_path) in enumerate(schedule_pairs, 1):
        try:
            # random weather conditions
            temperature = random.randint(-30, 40)  # Celsius
            precipitation = (
                0 if random.random() < 0.5 else random.uniform(0, 20)
            )  # 50% chance of no precipitation

            # run intelligent pathfinding
            friend_day_path = entire_friend_day_path(
                G, friend_path, precipitation, temperature
            )
            agent_day_path = entire_agent_day_path(
                G, agent_path, friend_path, friend_day_path, precipitation, temperature
            )
            intelligent_time = total_time_together(agent_day_path)

            # run naive pathfinding
            naive_time = total_time_together_naive(G, friend_day_path, agent_day_path)

            # calculate length of agent's path deviation from absolute shortest path
            shortest_path = entire_shortest_day_path(G, agent_path)
            shortest_path_cost = total_travel_cost(shortest_path)
            deviation_cost = total_travel_cost(agent_day_path) - shortest_path_cost

            results.append(
                {
                    "index": i,
                    "intelligent_time": round(intelligent_time, 2),
                    "naive_time": round(naive_time, 2),
                    "deviation_cost": round(deviation_cost, 2),
                }
            )

            # generate visualizations for first N simulations
            if i <= num_visualizations:
                try:
                    # visualize friend's path segments
                    for seg_idx, segment in enumerate(friend_day_path):
                        visualize_path(
                            G,
                            building_centroids,
                            segment["path"],
                            f"Sim {i} Friend Segment {seg_idx + 1}",
                            path_width=3.0,
                            filename=f"{viz_dir}/sim_{i:03d}_friend_seg_{seg_idx + 1}.png",
                        )

                    # group agent segments into windows (each window ends at a class building)
                    windows = []
                    current_window = []
                    for segment in agent_day_path:
                        current_window.append(segment)
                        # window ends when we reach destination building
                        if segment.get("end_building"):
                            windows.append(current_window)
                            current_window = []
                    # add any remaining segments
                    if current_window:
                        windows.append(current_window)

                    # visualize each window separately
                    for window_idx, window_segments in enumerate(windows, 1):
                        visualize_path_segments(
                            G,
                            building_centroids,
                            window_segments,
                            f"Simulation {i} Window {window_idx}",
                            filename=f"{viz_dir}/sim_{i:03d}_intelligent_window_{window_idx}.png",
                        )

                    print(
                        f"  Generated visualizations for simulation {i} ({len(windows)} windows)"
                    )
                except Exception as viz_error:
                    print(
                        f"  Warning: Could not generate visualization for simulation {i}: {viz_error}"
                    )

        except Exception as e:
            # skip this trial, don't add to results
            pass

    # write results to CSV
    if results:
        fieldnames = ["index", "intelligent_time", "naive_time", "deviation_cost"]

        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"\nResults saved to {output_csv}")

        # print summary statistics
        valid_results = [r for r in results if r["intelligent_time"] is not None]
        if valid_results:
            avg_intelligent = sum(r["intelligent_time"] for r in valid_results) / len(
                valid_results
            )
            avg_naive = sum(r["naive_time"] for r in valid_results) / len(valid_results)
            avg_improvement = avg_intelligent - avg_naive

            print(f"\nSummary Statistics:")
            print(f"  Average intelligent time: {avg_intelligent:.2f} minutes")
            print(f"  Average naive time: {avg_naive:.2f} minutes")
            if avg_naive > 0:
                print(
                    f"  Average improvement: {avg_improvement:.2f} minutes ({avg_improvement/avg_naive*100:.1f}%)"
                )
            else:
                print(f"  Average improvement: {avg_improvement:.2f} minutes (N/A%)")
    else:
        print("No results to save.")


if __name__ == "__main__":
    run_comparison_test(num_schedules=20, num_visualizations=5)
