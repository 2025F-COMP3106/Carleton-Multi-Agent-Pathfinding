# utility functions for time and building operations


def parse_time(time_str):
    # parse time string "HH:MM" to minutes since midnight
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes


def format_minutes_to_time(minutes, round_up=False):
    # convert minutes since midnight to "HH:MM" format
    # if round_up is True, rounds up fractional minutes
    if round_up:
        minutes = int(minutes) + (1 if minutes % 1 > 0 else 0)
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"


def find_building_node(G, building_name):
    # find building node by name in graph
    for node, data in G.nodes(data=True):
        if data.get("node_type") == "building":
            if data.get("name") == building_name:
                return node
    return None
