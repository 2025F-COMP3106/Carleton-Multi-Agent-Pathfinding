# Builds a graph network connecting buildings at Carleton University to the pedestrian network

import osmnx as ox
import networkx as nx
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

from config import (
    WALKING_SPEED_M_PER_MIN,
    TUNNEL_CONNECTION_THRESHOLD_M,
    TUNNEL_TAGS,
    COVERED_WALKWAY_INDICATORS,
)


def setup_osmnx_settings():
    # we need to preserve some additional attributes for tunnel reclassification
    ox.settings.useful_tags_way = ox.settings.useful_tags_way + [
        "surface",
        "sidewalk",
        "bicycle",
        "footway",
    ]


def download_pedestrian_network(place_name):
    # download pedestrian network from OSM and ensures only underground tunnels are classified as tunnels
    # returns the pedestrian network graph
    print("Downloading pedestrian network...")

    setup_osmnx_settings()

    G = ox.graph_from_place(
        place_name,
        network_type="walk",
        simplify=True,
        custom_filter='["highway"~"^(footway|steps|cycleway|path|pedestrian)$"]',  # only fetches pedestrian paths
    )

    for _, _, data in G.edges(data=True):
        # add travel time attribute to edge
        data["time"] = data["length"] / WALKING_SPEED_M_PER_MIN

        # classify tunnels
        is_tunnel_tagged = data.get("tunnel") in TUNNEL_TAGS

        if is_tunnel_tagged:
            # check if it's actually a covered walkway, not an underground tunnel
            has_sidewalk = (
                data.get("sidewalk") is not None or data.get("footway") == "sidewalk"
            )
            is_cycleway = data.get("highway") in COVERED_WALKWAY_INDICATORS["highways"]
            has_asphalt = data.get("surface") in COVERED_WALKWAY_INDICATORS["surfaces"]

            if has_sidewalk or is_cycleway or has_asphalt:
                data["is_tunnel"] = False
            else:
                data["is_tunnel"] = True
        else:
            data["is_tunnel"] = False

    print(f"Downloaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")

    return G


def extract_buildings(place_name):
    # extract buildings from OSM and compute their centroids for attaching them to the pedestrian network
    # returns list of dictionaries with building information
    print("Extracting buildings...")
    buildings = ox.features_from_place(place_name, tags={"building": True})

    building_centroids = []
    for building_index, building in buildings.iterrows():
        if building.geometry is not None:
            building_name = building.get("name")
            if pd.notna(building_name) and building_name:
                centroid = building.geometry.centroid
                building_centroids.append(
                    {
                        "id": building_index,
                        "name": building_name,
                        "x": centroid.x,
                        "y": centroid.y,
                    }
                )

    print(f"Found {len(building_centroids)} buildings\n")
    return building_centroids


def get_tunnel_nodes(G):
    # extract all nodes that are part of tunnel edges
    tunnel_nodes = set()
    for source_node, target_node, data in G.edges(data=True):
        if data.get("is_tunnel"):
            tunnel_nodes.add(source_node)
            tunnel_nodes.add(target_node)
    return tunnel_nodes


def connect_buildings_to_tunnels(G_buildings, G, building_centroids, tunnel_nodes):
    # connect buildings to nearest tunnel nodes if within threshold distance
    # returns the number of connections made
    building_coords = np.array(
        [[building["x"], building["y"]] for building in building_centroids]
    )

    tunnel_node_ids = [node for node in tunnel_nodes if node in G.nodes]
    if not tunnel_node_ids:
        return 0

    tunnel_coords = np.array(
        [[G.nodes[node]["x"], G.nodes[node]["y"]] for node in tunnel_node_ids]
    )

    distances_to_tunnels = cdist(building_coords, tunnel_coords)

    connections_made = 0
    for building_index, building in enumerate(building_centroids):
        min_distance = distances_to_tunnels[building_index].min()
        if min_distance < TUNNEL_CONNECTION_THRESHOLD_M:
            nearest_tunnel_index = np.argmin(distances_to_tunnels[building_index])
            nearest_tunnel_node = tunnel_node_ids[nearest_tunnel_index]
            distance = distances_to_tunnels[building_index, nearest_tunnel_index]

            G_buildings.add_edge(
                building["id"],
                nearest_tunnel_node,
                length=distance,
                time=distance / WALKING_SPEED_M_PER_MIN,
                highway="tunnel_connection",
                connection_type="building_to_tunnel",
                is_tunnel_connection=True,
                is_tunnel=True,
            )
            connections_made += 1

    return connections_made


def connect_buildings_to_paths(G_buildings, G, building_centroids, tunnel_nodes):
    # connect buildings to nearest non-tunnel path nodes
    # returns the number of connections made
    building_coords = np.array(
        [[building["x"], building["y"]] for building in building_centroids]
    )
    pedestrian_nodes = {
        node: (data["x"], data["y"]) for node, data in G.nodes(data=True)
    }
    pedestrian_node_ids = list(pedestrian_nodes.keys())

    non_tunnel_node_ids = [
        node for node in pedestrian_node_ids if node not in tunnel_nodes
    ]
    if not non_tunnel_node_ids:
        return 0

    non_tunnel_coords = np.array(
        [[G.nodes[node]["x"], G.nodes[node]["y"]] for node in non_tunnel_node_ids]
    )

    distances_to_pedestrian = cdist(building_coords, non_tunnel_coords)

    connections_made = 0
    for building_index, building in enumerate(building_centroids):
        nearest_pedestrian_index = np.argmin(distances_to_pedestrian[building_index])
        nearest_pedestrian_node = non_tunnel_node_ids[nearest_pedestrian_index]
        distance = distances_to_pedestrian[building_index, nearest_pedestrian_index]

        # only add if not already connected to this node
        if not G_buildings.has_edge(building["id"], nearest_pedestrian_node):
            G_buildings.add_edge(
                building["id"],
                nearest_pedestrian_node,
                length=distance,
                time=distance / WALKING_SPEED_M_PER_MIN,
                highway="building_connection",
                connection_type="building_to_path",
                is_tunnel_connection=False,
            )
            connections_made += 1

    return connections_made


def create_building_network(G, building_centroids):
    # create a graph connecting buildings to the pedestrian network
    # returns the pedestrian network graph with buildings attached
    print("Creating pedestrian network with buildings...")
    G_buildings = nx.Graph()

    # add building nodes
    for building in building_centroids:
        G_buildings.add_node(
            building["id"],
            x=building["x"],
            y=building["y"],
            name=building["name"],
            node_type="building",
        )

    # add pedestrian nodes and edges from original network
    pedestrian_nodes = {
        node: (data["x"], data["y"]) for node, data in G.nodes(data=True)
    }

    for node, (x, y) in pedestrian_nodes.items():
        G_buildings.add_node(node, x=x, y=y, node_type="path")

    # copy all pedestrian network edges (paths connecting path nodes)
    for source_node, target_node, data in G.edges(data=True):
        G_buildings.add_edge(source_node, target_node, **data)

    # connect buildings to tunnel nodes
    tunnel_nodes = get_tunnel_nodes(G)
    tunnel_connections = connect_buildings_to_tunnels(
        G_buildings, G, building_centroids, tunnel_nodes
    )
    print(f"Made {tunnel_connections} building-to-tunnel connections")

    # connect buildings to non-tunnel path nodes
    path_connections = connect_buildings_to_paths(
        G_buildings, G, building_centroids, tunnel_nodes
    )
    print(f"Made {path_connections} building-to-path connections")

    print(
        f"Final network: {G_buildings.number_of_nodes()} nodes, "
        f"{G_buildings.number_of_edges()} edges\n"
    )

    return G_buildings


def build_campus_network(place_name):
    # builds the complete campus network with buildings and paths
    # returns (G_buildings, building_centroids)
    G = download_pedestrian_network(place_name)
    building_centroids = extract_buildings(place_name)
    G_buildings = create_building_network(G, building_centroids)
    return G_buildings, building_centroids
