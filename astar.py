# A* path-finding algorithm

import heapq
import math


# heuristic is the Euclidean distance between the current and goal nodes
def heuristic(G, current_node, goal_node):
    current_data = G.nodes[current_node]
    goal_data = G.nodes[goal_node]
    x1, y1 = current_data["x"], current_data["y"]
    x2, y2 = goal_data["x"], goal_data["y"]
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# checks if a node is part of any tunnel edge (includes buildings)
def is_tunnel_node(G, node):
    for neighbor in G.neighbors(node):
        edge_data = G[node][neighbor]
        if edge_data.get("is_tunnel", False):
            return True
    return False


# validates tunnel constraints for a node (buildings are always allowed)
def validate_tunnel_constraint(G, node, tunnel_only):
    node_data = G.nodes[node]
    is_building = node_data.get("node_type") == "building"

    # buildings are always allowed, skip tunnel check for them
    if is_building:
        return

    is_tunnel = is_tunnel_node(G, node)

    if tunnel_only:
        # tunnel-only: non-building nodes must be tunnel nodes
        if not is_tunnel:
            raise ValueError("Expected tunnel node, got non-tunnel node")
    else:
        # outdoor-only: non-building nodes must NOT be tunnel nodes
        if is_tunnel:
            raise ValueError("Expected non-tunnel node, got tunnel node")


# finds shortest path from start to goal using A* search
# tunnel_only: None (all edges), True (only tunnels), False (only non-tunnels)
# returns (path, path_time, num_states_explored)
def astar_pathfinding(G, start_node, goal_node, tunnel_only=None):
    # check if nodes exist in graph
    if start_node not in G or goal_node not in G:
        raise ValueError("Start or goal node not found in graph")

    # check tunnel constraints for start and goal nodes (buildings are always allowed)
    if tunnel_only is not None:
        validate_tunnel_constraint(G, start_node, tunnel_only)
        validate_tunnel_constraint(G, goal_node, tunnel_only)

    # if start and goal are the same
    if start_node == goal_node:
        return [start_node], 0, 1

    # frontier is a priority queue: (f(n), node)
    # f(n) = g(n) + h(n) where g(n) is cost from start, h(n) is heuristic to goal
    frontier = [(0.0, start_node)]

    # maps a node to the node that came before it in the optimal path
    # start node points to itself
    node_to_prev_node = {start_node: start_node}

    # maps a node to the lowest cost found so far to reach it (g(n))
    costs_to_reach = {start_node: 0}

    # track nodes that have been fully explored (popped from frontier)
    explored = set()

    num_states_explored = 0

    while frontier:
        _, current_node = heapq.heappop(frontier)

        # skip if already explored
        if current_node in explored:
            continue

        explored.add(current_node)
        num_states_explored += 1

        # found the goal
        if current_node == goal_node:
            path = reconstruct_path(node_to_prev_node, current_node, start_node)
            path_time = costs_to_reach[current_node]
            return path, path_time, num_states_explored

        # explore neighbors
        for neighbor_node in G.neighbors(current_node):
            # skip if already explored
            if neighbor_node in explored:
                continue

            # get edge data
            edge_data = G[current_node][neighbor_node]

            # filter by tunnel status if specified (edge type must match constraint)
            if tunnel_only is not None:
                is_tunnel_edge = edge_data.get("is_tunnel", False)

                if tunnel_only:
                    # tunnel-only: must use tunnel edges
                    if not is_tunnel_edge:
                        continue
                else:
                    # outdoor-only: must use non-tunnel edges
                    if is_tunnel_edge:
                        continue

            edge_cost = edge_data.get("time", float("inf"))

            # calculate new cost to reach neighbor
            new_cost = costs_to_reach[current_node] + edge_cost

            # if we've seen this node before, only update if we found a better path
            if neighbor_node in costs_to_reach:
                if new_cost >= costs_to_reach[neighbor_node]:
                    continue
                # found a better path, update it
                costs_to_reach[neighbor_node] = new_cost
                node_to_prev_node[neighbor_node] = current_node

                # add to frontier with new priority
                h_value = heuristic(G, neighbor_node, goal_node)
                f_value = new_cost + h_value
                heapq.heappush(frontier, (f_value, neighbor_node))
            else:
                # new node, add to costs and frontier
                costs_to_reach[neighbor_node] = new_cost
                node_to_prev_node[neighbor_node] = current_node

                h_value = heuristic(G, neighbor_node, goal_node)
                f_value = new_cost + h_value
                heapq.heappush(frontier, (f_value, neighbor_node))

    # no path found after searching
    raise RuntimeError("No path found")


# reconstructs path from start to goal
def reconstruct_path(node_to_prev_node, current_node, start_node):
    path = []
    while current_node != start_node:
        path.append(current_node)
        current_node = node_to_prev_node[current_node]
    path.append(start_node)
    return path[::-1]  # reverse to get path from start to goal
