# Visualization functions for the building network

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D


def get_edge_style(edge_data, source_node_type, target_node_type):
    # determine the visual style for an edge based on its properties
    if edge_data.get("is_tunnel_connection"):
        return "#E67E22", 1.0  # orange for building-to-tunnel connections
    elif edge_data.get("is_tunnel"):
        return "#E74C3C", 2.0  # red for tunnels
    elif edge_data.get("connection_type") == "building_to_path":
        return "#3498DB", 1.0  # blue for building-to-path connections
    elif source_node_type == "building" or target_node_type == "building":
        return "#FF69B4", 0.5  # pink for self-loops (do not appear in visualization)
    else:
        return "#BDC3C7", 0.5  # light gray for path-to-path connections


def create_visualization(G_buildings, building_centroids, show_labels=True):
    # create a visualization of the building network
    _, ax = plt.subplots(figsize=(16, 12))

    # draw edges
    for source_node, target_node, data in G_buildings.edges(data=True):
        source_node_data = G_buildings.nodes[source_node]
        target_node_data = G_buildings.nodes[target_node]
        source_node_type = source_node_data.get("node_type")
        target_node_type = target_node_data.get("node_type")

        color, linewidth = get_edge_style(data, source_node_type, target_node_type)

        ax.plot(
            [source_node_data["x"], target_node_data["x"]],
            [source_node_data["y"], target_node_data["y"]],
            color=color,
            linewidth=linewidth,
            alpha=0.7,
            zorder=1,
        )

    # draw nodes
    for _, data in G_buildings.nodes(data=True):
        if data.get("node_type") == "building":
            ax.scatter(
                data["x"],
                data["y"],
                c="#FFD93D",
                s=100,
                alpha=0.8,
                edgecolors="black",
                linewidth=1,
                zorder=2,
            )

            if show_labels:
                ax.annotate(
                    data.get("name"),
                    (data["x"], data["y"]),
                    fontsize=6,
                    ha="center",
                    va="bottom",
                    color="#2C3E50",
                    bbox=dict(
                        boxstyle="round,pad=0.3",
                        facecolor="white",
                        alpha=0.7,
                        edgecolor="none",
                    ),
                    zorder=3,
                )
        else:
            ax.scatter(data["x"], data["y"], c="#2D3436", s=5, alpha=0.8, zorder=2)

    # add title and labels
    tunnel_edges = sum(
        1
        for _, _, edge_data in G_buildings.edges(data=True)
        if edge_data.get("is_tunnel")
    )
    ax.set_title(
        f"Carleton University - Building Network with Tunnels\n"
        f"{len(building_centroids)} Buildings, {tunnel_edges} Tunnel Edges",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="box")

    # add legend
    legend_elements = [
        plt.scatter(
            [],
            [],
            c="#FFD93D",
            s=100,
            edgecolors="black",
            label=f"Buildings ({len(building_centroids)})",
        ),
        plt.scatter([], [], c="#2D3436", s=5, label="Path Nodes"),
        Patch(facecolor="#E74C3C", label="Tunnels"),
        Patch(facecolor="#E67E22", label="Building-to-Tunnel Connections"),
        Patch(facecolor="#3498DB", label="Building-to-Path Connections"),
        Patch(facecolor="#BDC3C7", label="Path-to-Path Connections"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=9)

    plt.tight_layout()
    filename = (
        "carleton_building_network.png"
        if show_labels
        else "carleton_building_network_no_labels.png"
    )
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"Saved: {filename}")
    plt.close()


# visualizes a path on the building network map
def visualize_path(
    G_buildings,
    building_centroids,
    path,
    path_name,
    path_width=3.0,
    filename=None,
):
    # create a visualization of the building network with highlighted path
    _, ax = plt.subplots(figsize=(16, 12))

    # draw all edges (background)
    for source_node, target_node, data in G_buildings.edges(data=True):
        source_node_data = G_buildings.nodes[source_node]
        target_node_data = G_buildings.nodes[target_node]
        source_node_type = source_node_data.get("node_type")
        target_node_type = target_node_data.get("node_type")

        color, linewidth = get_edge_style(data, source_node_type, target_node_type)

        ax.plot(
            [source_node_data["x"], target_node_data["x"]],
            [source_node_data["y"], target_node_data["y"]],
            color=color,
            linewidth=linewidth,
            alpha=0.3,
            zorder=1,
        )

    # draw the path with different colors for tunnel vs outdoor edges
    if path and len(path) > 1:
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]
            current_data = G_buildings.nodes[current_node]
            next_data = G_buildings.nodes[next_node]

            # get edge data to determine if it's a tunnel
            edge_data = G_buildings[current_node][next_node]
            is_tunnel_edge = edge_data.get("is_tunnel", False)

            # color tunnel edges red, outdoor edges blue
            edge_color = "#E74C3C" if is_tunnel_edge else "#3498DB"

            ax.plot(
                [current_data["x"], next_data["x"]],
                [current_data["y"], next_data["y"]],
                color=edge_color,
                linewidth=path_width,
                alpha=0.9,
                zorder=3,
            )

    # draw nodes
    for node_id, data in G_buildings.nodes(data=True):
        if data.get("node_type") == "building":
            # highlight start and end nodes if they're in the path
            if path and (node_id == path[0] or node_id == path[-1]):
                ax.scatter(
                    data["x"],
                    data["y"],
                    c="#E74C3C",
                    s=200,
                    alpha=1.0,
                    edgecolors="black",
                    linewidth=2,
                    zorder=4,
                    marker="*",
                )
            else:
                ax.scatter(
                    data["x"],
                    data["y"],
                    c="#FFD93D",
                    s=100,
                    alpha=0.8,
                    edgecolors="black",
                    linewidth=1,
                    zorder=2,
                )

            # label buildings
            ax.annotate(
                data.get("name", ""),
                (data["x"], data["y"]),
                fontsize=6,
                ha="center",
                va="bottom",
                color="#2C3E50",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor="white",
                    alpha=0.7,
                    edgecolor="none",
                ),
                zorder=3,
            )
        else:
            # highlight path nodes with default color
            if path and node_id in path:
                ax.scatter(data["x"], data["y"], c="#9B59B6", s=15, alpha=0.8, zorder=2)
            else:
                ax.scatter(data["x"], data["y"], c="#2D3436", s=5, alpha=0.8, zorder=2)

    # add title
    tunnel_edges = sum(
        1
        for _, _, edge_data in G_buildings.edges(data=True)
        if edge_data.get("is_tunnel")
    )
    ax.set_title(
        f"Carleton University - {path_name}\n"
        f"{len(building_centroids)} Buildings, {tunnel_edges} Tunnel Edges",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="box")

    # add legend
    legend_elements = [
        plt.scatter(
            [],
            [],
            c="#E74C3C",
            s=200,
            edgecolors="black",
            marker="*",
            label="Start/End Buildings",
        ),
        plt.scatter(
            [],
            [],
            c="#FFD93D",
            s=100,
            edgecolors="black",
            label=f"Buildings ({len(building_centroids)})",
        ),
        plt.scatter([], [], c="#2D3436", s=5, label="Path Nodes"),
        Patch(facecolor="#E74C3C", label="Path: Tunnel Segments"),
        Patch(facecolor="#3498DB", label="Path: Outdoor Segments"),
        Patch(facecolor="#E74C3C", label="Tunnels"),
        Patch(facecolor="#E67E22", label="Building-to-Tunnel Connections"),
        Patch(facecolor="#3498DB", label="Building-to-Path Connections"),
        Patch(facecolor="#BDC3C7", label="Path-to-Path Connections"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=9)

    plt.tight_layout()
    if filename is None:
        filename = f"path_{path_name.lower().replace(' ', '_')}.png"
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"Saved: {filename}")
    plt.close()


def visualize_path_segments(
    G_buildings, building_centroids, path_segments, agent_name, filename=None
):
    # visualize multiple path segments with meeting/leaving annotations
    _, ax = plt.subplots(figsize=(16, 12))

    # draw all edges (background)
    for source_node, target_node, data in G_buildings.edges(data=True):
        source_node_data = G_buildings.nodes[source_node]
        target_node_data = G_buildings.nodes[target_node]
        source_node_type = source_node_data.get("node_type")
        target_node_type = target_node_data.get("node_type")

        color, linewidth = get_edge_style(data, source_node_type, target_node_type)

        ax.plot(
            [source_node_data["x"], target_node_data["x"]],
            [source_node_data["y"], target_node_data["y"]],
            color=color,
            linewidth=linewidth,
            alpha=0.3,
            zorder=1,
        )

    # draw each path segment
    for segment_idx, segment in enumerate(path_segments):
        path = segment["path"]
        with_friend = segment.get("with_friend", False)

        # use thicker lines when with friend
        line_width = 4.0 if with_friend else 2.5

        if path and len(path) > 1:
            for i in range(len(path) - 1):
                current_node = path[i]
                next_node = path[i + 1]
                current_data = G_buildings.nodes[current_node]
                next_data = G_buildings.nodes[next_node]

                # get edge data to determine if it's a tunnel
                edge_data = G_buildings[current_node][next_node]
                is_tunnel_edge = edge_data.get("is_tunnel") or edge_data.get(
                    "is_tunnel_connection"
                )

                # color tunnel edges red, outdoor edges blue (darker shades when with friend)
                if with_friend:
                    edge_color = (
                        "#C0392B" if is_tunnel_edge else "#21618C"
                    )  # dark red/blue
                else:
                    edge_color = (
                        "#E74C3C" if is_tunnel_edge else "#3498DB"
                    )  # bright red/blue

                ax.plot(
                    [current_data["x"], next_data["x"]],
                    [current_data["y"], next_data["y"]],
                    color=edge_color,
                    linewidth=line_width,
                    alpha=0.9,
                    zorder=3,
                )

    # add start and end building markers
    if path_segments:
        # mark start building
        first_segment = path_segments[0]
        if first_segment["path"]:
            start_node = first_segment["path"][0]
            start_building = first_segment.get("start_building", "")
            node_data = G_buildings.nodes[start_node]
            ax.scatter(
                node_data["x"],
                node_data["y"],
                c="#9B59B6",
                s=400,
                alpha=1.0,
                edgecolors="black",
                linewidth=3,
                zorder=5,
                marker="*",
            )
            ax.annotate(
                f"START: {start_building}",
                (node_data["x"], node_data["y"]),
                fontsize=10,
                ha="center",
                va="bottom",
                color="white",
                fontweight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    facecolor="#9B59B6",
                    alpha=0.9,
                    edgecolor="black",
                    linewidth=2,
                ),
                zorder=6,
                xytext=(0, 20),
                textcoords="offset points",
            )

        # mark end building
        last_segment = path_segments[-1]
        if last_segment["path"]:
            end_node = last_segment["path"][-1]
            end_building = last_segment.get("end_building", "")
            node_data = G_buildings.nodes[end_node]
            ax.scatter(
                node_data["x"],
                node_data["y"],
                c="#8E44AD",
                s=400,
                alpha=1.0,
                edgecolors="black",
                linewidth=3,
                zorder=5,
                marker="*",
            )
            ax.annotate(
                f"END: {end_building}",
                (node_data["x"], node_data["y"]),
                fontsize=10,
                ha="center",
                va="top",
                color="white",
                fontweight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    facecolor="#8E44AD",
                    alpha=0.9,
                    edgecolor="black",
                    linewidth=2,
                ),
                zorder=6,
                xytext=(0, -20),
                textcoords="offset points",
            )

    # add meeting/leaving annotations
    for segment_idx, segment in enumerate(path_segments):
        with_friend = segment.get("with_friend", False)
        start_time = segment.get("start_time", "")
        end_time = segment.get("end_time", "")
        path = segment["path"]

        if not path:
            continue

        # check if this is the start of a meeting (with_friend becomes True)
        if with_friend:
            # check if previous segment was not with_friend
            is_meeting_start = segment_idx == 0 or not path_segments[
                segment_idx - 1
            ].get("with_friend", False)

            if is_meeting_start:
                # annotate start node
                start_node = path[0]
                node_data = G_buildings.nodes[start_node]
                ax.scatter(
                    node_data["x"],
                    node_data["y"],
                    c="#2ECC71",
                    s=300,
                    alpha=1.0,
                    edgecolors="black",
                    linewidth=3,
                    zorder=5,
                    marker="o",
                )
                ax.annotate(
                    f"meeting friend @ {start_time}",
                    (node_data["x"], node_data["y"]),
                    fontsize=9,
                    ha="center",
                    va="top",
                    color="white",
                    fontweight="bold",
                    bbox=dict(
                        boxstyle="round,pad=0.5",
                        facecolor="#2ECC71",
                        alpha=0.9,
                        edgecolor="black",
                        linewidth=2,
                    ),
                    zorder=6,
                    xytext=(0, -15),
                    textcoords="offset points",
                )

            # check if this is the end of a meeting (next segment is not with_friend)
            is_meeting_end = segment_idx == len(path_segments) - 1 or not path_segments[
                segment_idx + 1
            ].get("with_friend", False)

            if is_meeting_end:
                # annotate end node
                end_node = path[-1]
                node_data = G_buildings.nodes[end_node]
                ax.scatter(
                    node_data["x"],
                    node_data["y"],
                    c="#E67E22",
                    s=300,
                    alpha=1.0,
                    edgecolors="black",
                    linewidth=3,
                    zorder=5,
                    marker="o",
                )
                ax.annotate(
                    f"leaving friend @ {end_time}",
                    (node_data["x"], node_data["y"]),
                    fontsize=9,
                    ha="center",
                    va="bottom",
                    color="white",
                    fontweight="bold",
                    bbox=dict(
                        boxstyle="round,pad=0.5",
                        facecolor="#E67E22",
                        alpha=0.9,
                        edgecolor="black",
                        linewidth=2,
                    ),
                    zorder=6,
                    xytext=(0, 15),
                    textcoords="offset points",
                )

    # draw all nodes
    for node_id, data in G_buildings.nodes(data=True):
        if data.get("node_type") == "building":
            ax.scatter(
                data["x"],
                data["y"],
                c="#FFD93D",
                s=100,
                alpha=0.8,
                edgecolors="black",
                linewidth=1,
                zorder=2,
            )

            # label buildings
            ax.annotate(
                data.get("name", ""),
                (data["x"], data["y"]),
                fontsize=6,
                ha="center",
                va="bottom",
                color="#2C3E50",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor="white",
                    alpha=0.7,
                    edgecolor="none",
                ),
                zorder=3,
            )
        else:
            ax.scatter(data["x"], data["y"], c="#2D3436", s=5, alpha=0.8, zorder=2)

    # add title
    tunnel_edges = sum(
        1
        for _, _, edge_data in G_buildings.edges(data=True)
        if edge_data.get("is_tunnel")
    )
    ax.set_title(
        f"Carleton University - {agent_name} Path with Friend Meetup\n"
        f"{len(building_centroids)} Buildings, {tunnel_edges} Tunnel Edges",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="box")

    # add legend
    legend_elements = [
        Line2D([0], [0], color="#E74C3C", linewidth=2.5, label="Tunnel (alone)"),
        Line2D([0], [0], color="#3498DB", linewidth=2.5, label="Outdoor (alone)"),
        Line2D([0], [0], color="#C0392B", linewidth=4.0, label="Tunnel (with friend)"),
        Line2D([0], [0], color="#21618C", linewidth=4.0, label="Outdoor (with friend)"),
        plt.scatter(
            [],
            [],
            c="#9B59B6",
            s=400,
            edgecolors="black",
            marker="*",
            label="Start Building",
        ),
        plt.scatter(
            [],
            [],
            c="#8E44AD",
            s=400,
            edgecolors="black",
            marker="*",
            label="End Building",
        ),
        plt.scatter(
            [],
            [],
            c="#2ECC71",
            s=300,
            edgecolors="black",
            marker="o",
            label="Meeting Point",
        ),
        plt.scatter(
            [],
            [],
            c="#E67E22",
            s=300,
            edgecolors="black",
            marker="o",
            label="Leaving Point",
        ),
        plt.scatter(
            [],
            [],
            c="#FFD93D",
            s=100,
            edgecolors="black",
            label=f"Buildings ({len(building_centroids)})",
        ),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=8)

    plt.tight_layout()

    if filename is None:
        filename = f"path_segments_{agent_name.lower().replace(' ', '_')}.png"

    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"Saved: {filename}")
    plt.close()
