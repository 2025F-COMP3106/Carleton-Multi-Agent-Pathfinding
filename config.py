# graph construction
PLACE_NAME = "Carleton University, Ottawa, Ontario, Canada"
WALKING_SPEED_M_PER_MIN = 75  # meters per minute
TUNNEL_CONNECTION_THRESHOLD_M = 50  # meters
TUNNEL_TAGS = ["yes", "building_passage", "covered"]
COVERED_WALKWAY_INDICATORS = {
    "surfaces": ["asphalt", "paved"],
    "highways": ["cycleway"],
}

# time intervals
WAITING_TIME_INTERVAL_MINUTES = 1.0  # interval for waiting at buildings
TIME_BUCKET_SIZE_MINUTES = 0.1  # bucket size for social score calculation (6 seconds)

# fuzzy logic
TUNNEL_PREFERENCE_THRESHOLD = 50  # score >= 50 means tunnel

# node types (used across multiple files)
NODE_TYPE_BUILDING = "building"
NODE_TYPE_PATH = "path"

# activity types for timeline representation
ACTIVITY_TYPE_CLASS = "in_class"
ACTIVITY_TYPE_WALK_ALONE = "walk_alone"
ACTIVITY_TYPE_WALK_TOGETHER = "walk_together"
ACTIVITY_TYPE_MEETING = "meeting"
ACTIVITY_TYPE_WAIT_ALONE = "wait_alone"
ACTIVITY_TYPE_WAIT_FOR_FRIEND = "wait_for_friend"

# duration thresholds for activity filtering
MIN_ACTIVITY_DURATION_MINUTES = 0.5  # 30 seconds minimum for activities
MIN_OVERLAP_DURATION_MINUTES = 0.2  # 12 seconds minimum for detecting overlaps
TINY_SEGMENT_THRESHOLD_MINUTES = 0.5  # threshold to avoid tiny segments
AGENT_PRESENCE_THRESHOLD = 0.5  # 50% presence threshold for overlap detection
