import json
from astar import astar_pathfinding
from fuzzy_decision import will_take_tunnel
from utils import parse_time, find_building_node, format_minutes_to_time


# load schedule from json file
def load_schedule(schedule_path):
    with open(schedule_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["schedule"]


def time_intervals_when_not_in_class(schedule_path):
    schedule = load_schedule(schedule_path)
    free_time_intervals = []
    for i in range(len(schedule) - 1):
        class_end_time = parse_time(schedule[i]["end_time"])
        next_class_start_time = parse_time(schedule[i + 1]["start_time"])
        free_time_intervals.append((class_end_time, next_class_start_time))

    return free_time_intervals


def possible_to_meetup(start_time, end_time, free_time_intervals):
    start_time_minutes = parse_time(start_time)
    end_time_minutes = parse_time(end_time)

    for free_time_interval in free_time_intervals:
        if (
            start_time_minutes < free_time_interval[1]
            and end_time_minutes > free_time_interval[0]
        ):
            return True
    return False


def build_node_arrival_times(G, path, start_time_minutes):
    node_times = []
    current_time = start_time_minutes

    # first node is at start time
    if path:
        node_times.append((path[0], current_time))

    # traverse path, accumulating edge costs
    for i in range(len(path) - 1):
        current_node = path[i]
        next_node = path[i + 1]
        edge_time = G[current_node][next_node].get("time", 0.0)
        current_time += edge_time
        node_times.append((next_node, current_time))

    return node_times


# returns the node and time of departure when the agent must leave for next class (or their friend has class)
def maximize_time_together(
    G,
    rendezvous_node,
    friend_node_times,
    friend_next_class_start_time,
    next_class_node,
    next_class_start_time,
):
    # calculate time together until must leave for next class
    current_time = None
    node_index = None
    for i, (node, time) in enumerate(friend_node_times):
        if node == rendezvous_node:
            current_time = time
            node_index = i
            break
    if current_time is None:
        raise ValueError(
            f"Rendezvous node {rendezvous_node} not found in friend's path"
        )

    # calculate time together until must leave for next class
    current_departure_node, time_of_departure = friend_node_times[i]
    for i in range(node_index, len(friend_node_times) - 1):
        time_to_next_class = astar_pathfinding(
            G, current_departure_node, next_class_node, tunnel_only=None
        )[1]

        if time_of_departure + time_to_next_class <= next_class_start_time:
            current_departure_node, time_of_departure = friend_node_times[i + 1]
        else:
            return friend_node_times[i - 1]

    # reached the friend's next class, can wait with them until we must leave
    time_to_next_class = astar_pathfinding(
        G, current_departure_node, next_class_node, tunnel_only=None
    )[1]

    time_until_friend_class = friend_next_class_start_time - time_of_departure
    time_until_agent_leaves = (
        next_class_start_time - time_to_next_class - time_of_departure
    )

    time_together = min(time_until_friend_class, time_until_agent_leaves)

    return (friend_node_times[-1][0], friend_node_times[-1][1] + time_together)


def find_rendezvous_point(
    G, friend_day_path, current_class_node, next_class_node, start_time, end_time
):
    # find friend's path that overlaps during time window
    trip = None
    start_time_minutes = parse_time(start_time)
    end_time_minutes = parse_time(end_time)

    for trip_info in friend_day_path:
        trip_start = parse_time(trip_info["start_time"])
        trip_end = parse_time(trip_info["end_time"])

        # check if start_time falls within this trip's time window
        if start_time_minutes < trip_end and end_time_minutes > trip_start:
            trip = trip_info
            break

    if trip is None:
        return None, None, None, None

    # build node arrival times for friend's path
    trip_start_minutes = parse_time(trip["start_time"])

    friend_node_times = build_node_arrival_times(G, trip["path"], trip_start_minutes)

    earliest_rendezvous_node = None
    for node, time in friend_node_times:
        if (
            start_time_minutes
            + astar_pathfinding(G, current_class_node, node, tunnel_only=None)[1]
            <= time
        ):
            earliest_rendezvous_node = node
            break

    if earliest_rendezvous_node is None:
        return None, None, None, None

    last_node, time_of_departure = maximize_time_together(
        G,
        earliest_rendezvous_node,
        friend_node_times,
        parse_time(trip["end_time"]),
        next_class_node,
        parse_time(end_time),
    )
    return earliest_rendezvous_node, last_node, time_of_departure, trip["tunnel_only"]


# calculate absolute shortest path
def entire_shortest_day_path(G, schedule_path):
    schedule = load_schedule(schedule_path)
    day_path = []

    for i in range(len(schedule) - 1):
        current_class = schedule[i]
        next_class = schedule[i + 1]

        from_node = find_building_node(G, current_class["building"])
        to_node = find_building_node(G, next_class["building"])

        if from_node is None or to_node is None:
            raise ValueError(
                f"Building not found: {current_class['building']} or {next_class['building']}"
            )

        # unrestricted shortest path (can mix tunnel and outdoor)
        path, cost, _ = astar_pathfinding(G, from_node, to_node, tunnel_only=None)

        day_path.append(
            {
                "start_node": from_node,
                "end_node": to_node,
                "path": path,
                "tunnel_only": None,
                "cost": cost,
                "start_time": current_class["end_time"],
                "end_time": next_class["start_time"],
                "start_building": current_class["building"],
                "end_building": next_class["building"],
            }
        )
    return day_path


def entire_friend_day_path(G, schedule_path, precipitation, temperature):
    schedule = load_schedule(schedule_path)
    day_path = []

    for i in range(len(schedule) - 1):
        current_class = schedule[i]
        next_class = schedule[i + 1]

        from_node = find_building_node(G, current_class["building"])
        to_node = find_building_node(G, next_class["building"])

        if from_node is None or to_node is None:
            raise ValueError(
                f"Building not found: {current_class['building']} or {next_class['building']}"
            )

        tunnel_only = will_take_tunnel(
            temperature,
            precipitation,
            astar_pathfinding(G, from_node, to_node, tunnel_only=False)[1],
            astar_pathfinding(G, from_node, to_node, tunnel_only=True)[1],
        )

        path, cost, _ = astar_pathfinding(
            G, from_node, to_node, tunnel_only=tunnel_only
        )

        day_path.append(
            {
                "start_node": from_node,
                "end_node": to_node,
                "path": path,
                "tunnel_only": tunnel_only,
                "cost": cost,
                "start_time": current_class["end_time"],
                "end_time": next_class["start_time"],
                "start_building": current_class["building"],
                "end_building": next_class["building"],
            }
        )
    return day_path


def entire_agent_day_path(
    G, schedule_path, friend_schedule_path, friend_day_path, precipitation, temperature
):
    schedule = load_schedule(schedule_path)

    day_path = []
    for i in range(len(schedule) - 1):
        current_class = schedule[i]
        next_class = schedule[i + 1]

        from_node = find_building_node(G, current_class["building"])
        to_node = find_building_node(G, next_class["building"])

        earliest_rendezvous_node, last_node, time_of_departure, meet_in_tunnel = (
            find_rendezvous_point(
                G,
                friend_day_path,
                from_node,
                to_node,
                current_class["end_time"],
                next_class["start_time"],
            )
        )

        if (
            possible_to_meetup(
                current_class["end_time"],
                next_class["start_time"],
                time_intervals_when_not_in_class(friend_schedule_path),
            )
            and earliest_rendezvous_node is not None
        ):
            path_to_rendezvous, cost_to_rendezvous, _ = astar_pathfinding(
                G, from_node, earliest_rendezvous_node, tunnel_only=None
            )

            time_at_rendezvous = (
                parse_time(current_class["end_time"]) + cost_to_rendezvous
            )

            path_with_friend, cost_with_friend, _ = astar_pathfinding(
                G,
                earliest_rendezvous_node,
                last_node,
                tunnel_only=meet_in_tunnel,
            )

            path_to_next_class, cost_to_next_class, _ = astar_pathfinding(
                G, last_node, to_node, tunnel_only=None
            )

            day_path.extend(
                [
                    {
                        "start_node": from_node,
                        "end_node": earliest_rendezvous_node,
                        "path": path_to_rendezvous,
                        "tunnel_only": None,
                        "cost": cost_to_rendezvous,
                        "with_friend": False,
                        "start_time": current_class["end_time"],
                        "end_time": format_minutes_to_time(time_at_rendezvous),
                        "start_building": current_class["building"],
                    },
                    {
                        "start_node": earliest_rendezvous_node,
                        "end_node": last_node,
                        "path": path_with_friend,
                        "tunnel_only": meet_in_tunnel,
                        "cost": cost_with_friend,
                        "with_friend": True,
                        "start_time": format_minutes_to_time(time_at_rendezvous),
                        "end_time": format_minutes_to_time(time_of_departure),
                    },
                    {
                        "start_node": last_node,
                        "end_node": to_node,
                        "path": path_to_next_class,
                        "tunnel_only": None,
                        "cost": cost_to_next_class,
                        "with_friend": False,
                        "start_time": format_minutes_to_time(time_of_departure),
                        "end_time": next_class["start_time"],
                        "end_building": next_class["building"],
                    },
                ]
            )

        else:
            # take direct path to next class
            tunnel_only = will_take_tunnel(
                temperature,
                precipitation,
                astar_pathfinding(G, from_node, to_node, tunnel_only=False)[1],
                astar_pathfinding(G, from_node, to_node, tunnel_only=True)[1],
            )

            path, cost, _ = astar_pathfinding(
                G, from_node, to_node, tunnel_only=tunnel_only
            )

            day_path.append(
                {
                    "start_node": from_node,
                    "end_node": to_node,
                    "path": path,
                    "tunnel_only": tunnel_only,
                    "cost": cost,
                    "with_friend": False,
                    "start_time": current_class["end_time"],
                    "end_time": next_class["start_time"],
                    "start_building": current_class["building"],
                    "end_building": next_class["building"],
                }
            )

    return day_path


def total_travel_cost(agent_day_path):
    total_cost = 0
    for path in agent_day_path:
        total_cost += path["cost"]
    return total_cost


def total_time_together(agent_day_path):
    total_time = 0
    for path in agent_day_path:
        if path["with_friend"]:
            total_time += parse_time(path["end_time"]) - parse_time(path["start_time"])
    return total_time


def total_time_together_naive(G, direct_day_path_1, direct_day_path_2):
    total_time = 0
    paths_with_times_1 = []
    for segment in direct_day_path_1:
        paths_with_times_1.extend(
            build_node_arrival_times(
                G, segment["path"], parse_time(segment["start_time"])
            )
        )

    paths_with_times_2 = []
    for segment in direct_day_path_2:
        paths_with_times_2.extend(
            build_node_arrival_times(
                G, segment["path"], parse_time(segment["start_time"])
            )
        )

    # find intersections
    times_together = []
    for coordinate in paths_with_times_1:
        if coordinate in paths_with_times_2:
            times_together.append(coordinate)

    # calculate time together
    for i in range(len(times_together) - 1):
        time = times_together[i + 1][1] - times_together[i][1]
        if time > 0 and time < 5:
            total_time += time

    return total_time
