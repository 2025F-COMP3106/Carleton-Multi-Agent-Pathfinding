import json
import random
import os
from utils import format_minutes_to_time


def load_buildings():
    with open("building_names.json", "r") as f:
        all_buildings = json.load(f)

    # filter out buildings containing "House"
    filtered = [b for b in all_buildings if "house" not in b.lower()]
    return filtered


def round_to_next_valid_start_time(time_minutes):
    hours = int(time_minutes // 60)
    minutes = int(time_minutes % 60)

    if minutes <= 5:
        return hours * 60 + 5
    elif minutes <= 35:
        return hours * 60 + 35
    else:
        # next hour at :05
        return (hours + 1) * 60 + 5


def random_start_time_before_1pm():
    hour = random.randint(8, 12)  # 8am to 12pm
    minute = random.choice([5, 35])
    return hour * 60 + minute


def generate_single_schedule():
    # load and filter buildings
    buildings = load_buildings()

    # choose random number of classes (at least 2)
    num_classes = random.randint(2, 5)

    # disciplines for class names
    disciplines = ["COMP", "MATH", "PSYC", "ECON", "BUSI", "HIST", "PHYS", "CHEM"]

    schedule = []
    # first class must start before 1pm
    current_time = random_start_time_before_1pm()
    classes_scheduled = 0

    # generate classes sequentially
    while (
        classes_scheduled < num_classes and current_time + 80 <= 1200
    ):  # 8pm = 1200 minutes
        # generate class details
        building = random.choice(buildings)
        discipline = random.choice(disciplines)
        level = random.randint(3, 4)
        suffix = random.randint(0, 999)
        class_name = f"{discipline}{level}{suffix}"

        # calculate end time (80 minutes after start)
        end_time = current_time + 80

        # add class to schedule
        schedule.append(
            {
                "class_name": class_name,
                "building": building,
                "start_time": format_minutes_to_time(current_time),
                "end_time": format_minutes_to_time(end_time),
            }
        )

        classes_scheduled += 1

        # if more classes to schedule, add break time
        if classes_scheduled < num_classes:
            break_duration = random.randint(0, 60)  # 0-60 minute break
            current_time = end_time + break_duration

            # round to next valid start time
            current_time = round_to_next_valid_start_time(current_time)

            # check if we can fit another class
            if current_time + 80 > 1200:  # can't fit another class before 8pm
                break

    return schedule


def generate_schedule_pairs(num_pairs=15, output_dir="schedules/generated"):
    # create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    buildings = load_buildings()

    schedule_pairs = []

    for pair_id in range(1, num_pairs + 1):
        # generate agent schedule
        agent_schedule = generate_single_schedule()

        # generate friend schedule
        friend_schedule = generate_single_schedule()

        # save to files
        agent_filename = os.path.join(output_dir, f"agent_{pair_id}.json")
        friend_filename = os.path.join(output_dir, f"friend_{pair_id}.json")

        # write agent schedule
        with open(agent_filename, "w") as f:
            json.dump({"schedule": agent_schedule}, f, indent=2)

        # write friend schedule
        with open(friend_filename, "w") as f:
            json.dump({"schedule": friend_schedule}, f, indent=2)

        schedule_pairs.append((agent_filename, friend_filename))

    return schedule_pairs


def main():
    generate_schedule_pairs(num_pairs=5)


if __name__ == "__main__":
    main()
