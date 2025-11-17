import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from config import TUNNEL_PREFERENCE_THRESHOLD


# variables in fuzzy rule-based system
temperature = ctrl.Antecedent(np.arange(-30, 41, 1), "temperature")  # °C
precipitation = ctrl.Antecedent(np.arange(0, 21, 0.5), "precipitation")  # mm/hr

# percentage increase in distance when taking the tunnels, max 100%
detour = ctrl.Antecedent(np.arange(0, 101, 1), "detour")

# 0-100 scale to represent preference for tunnel or outdoor
preference = ctrl.Consequent(np.arange(0, 101, 1), "preference")


# trapezoidal membership functions
temperature["freezing"] = fuzz.trapmf(temperature.universe, [-30, -30, -10, 0])
temperature["cold"] = fuzz.trapmf(temperature.universe, [-5, 0, 10, 15])
temperature["comfortable"] = fuzz.trapmf(temperature.universe, [10, 18, 24, 28])
temperature["hot"] = fuzz.trapmf(temperature.universe, [25, 30, 40, 40])


precipitation["none"] = fuzz.trapmf(precipitation.universe, [0, 0, 0.2, 0.5])
precipitation["light"] = fuzz.trapmf(precipitation.universe, [0.2, 1.0, 2.0, 3.0])
precipitation["moderate"] = fuzz.trapmf(precipitation.universe, [2.5, 4.0, 6.0, 8.0])
precipitation["heavy"] = fuzz.trapmf(precipitation.universe, [7.0, 10.0, 20.0, 20.0])


detour["negligible"] = fuzz.trapmf(detour.universe, [0, 0, 5, 15])
detour["moderate"] = fuzz.trapmf(detour.universe, [10, 25, 35, 50])
detour["significant"] = fuzz.trapmf(detour.universe, [40, 60, 100, 100])


# trapezoidal membership functions for preference (overlap at 50)
preference["outdoor"] = fuzz.trapmf(preference.universe, [0, 0, 40, 60])
preference["tunnel"] = fuzz.trapmf(preference.universe, [40, 60, 100, 100])


# fuzzy rules
# rule 1: heavy precipitation -> always tunnel
rule1 = ctrl.Rule(precipitation["heavy"], preference["tunnel"])

# rule 2: moderate rain (not freezing) -> tunnel
rule2 = ctrl.Rule(
    precipitation["moderate"] & ~temperature["freezing"], preference["tunnel"]
)

# rule 3: light rain + negligible detour -> tunnel
rule3 = ctrl.Rule(precipitation["light"] & detour["negligible"], preference["tunnel"])

# rule 4: light rain + significant detour -> outdoor
rule4 = ctrl.Rule(precipitation["light"] & detour["significant"], preference["outdoor"])

# rule 5: moderate snow (freezing) + significant detour -> outdoor
rule5 = ctrl.Rule(
    precipitation["moderate"] & temperature["freezing"] & detour["significant"],
    preference["outdoor"],
)

# rule 6: moderate snow (freezing) + negligible detour -> tunnel
rule6 = ctrl.Rule(
    precipitation["moderate"] & temperature["freezing"] & detour["negligible"],
    preference["tunnel"],
)

# rule 7: freezing + no precipitation + negligible detour -> tunnel
rule7 = ctrl.Rule(
    temperature["freezing"] & precipitation["none"] & detour["negligible"],
    preference["tunnel"],
)

# rule 8: freezing + no precipitation + significant detour -> outdoor
rule8 = ctrl.Rule(
    temperature["freezing"] & precipitation["none"] & detour["significant"],
    preference["outdoor"],
)

# rule 9: comfortable or hot + no rain -> outdoor
rule9 = ctrl.Rule(
    (temperature["comfortable"] | temperature["hot"]) & precipitation["none"],
    preference["outdoor"],
)

# rule 10: cold (not freezing) + negligible detour -> tunnel
rule10 = ctrl.Rule(temperature["cold"] & detour["negligible"], preference["tunnel"])

# rule 11: cold (not freezing) + significant detour -> outdoor
rule11 = ctrl.Rule(temperature["cold"] & detour["significant"], preference["outdoor"])

# control system
path_ctrl = ctrl.ControlSystem(
    [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11]
)
path_sim = ctrl.ControlSystemSimulation(path_ctrl)


def will_take_tunnel(temperature, precipitation, outdoor_path_time, tunnel_path_time):
    # returns True for tunnel, False for outdoor based on preference score
    temperature = max(-30, min(40, temperature))
    precipitation = max(0, min(20, precipitation))
    detour = calculate_detour_percentage(outdoor_path_time, tunnel_path_time)

    path_sim.input["temperature"] = temperature
    path_sim.input["precipitation"] = precipitation
    path_sim.input["detour"] = detour

    try:
        path_sim.compute()
        score = path_sim.output["preference"]
    except (KeyError, ValueError, AssertionError):
        # fuzzy computation failed, use default threshold
        score = TUNNEL_PREFERENCE_THRESHOLD

    return score >= TUNNEL_PREFERENCE_THRESHOLD


def calculate_detour_percentage(outdoor_path_time, tunnel_path_time):
    # returns 0-100 where 0 = no detour, 100 = double the distance or more
    if outdoor_path_time == 0:
        return 0.0
    if tunnel_path_time <= outdoor_path_time:
        return 0.0
    detour_ratio = (tunnel_path_time - outdoor_path_time) / outdoor_path_time
    return min(100, detour_ratio * 100)
