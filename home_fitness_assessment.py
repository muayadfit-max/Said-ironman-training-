#!/usr/bin/env python3
"""
Home Fitness Assessment + Starter Program  (Muayad Fit)
=======================================================

One-file coaching tool for a client with NO gym and NO equipment.
Built for a 16-year-old student (170 cm, ~85-90 kg) training in a bedroom,
hallway, or nearby outdoor space.

What it does
------------
1. Estimates VO2 max from a single 9-minute run (distance or average pace).
2. Rates muscle endurance / fatigue from three bodyweight tests.
3. Combines both into a starting level and prints a 3-week home plan
   plus coach notes you can copy straight into a message.

Run it:  python3 home_fitness_assessment.py

Everything is an ESTIMATE from a field test, not a lab measurement.
Youth-safe by design: no max lifting, no 1RM language, no training to
failure on every set.
"""


# ---------------------------------------------------------------------------
# 1. VO2 MAX FROM A 9-MINUTE RUN
# ---------------------------------------------------------------------------
#
# Published base formula - Cooper 12-minute run test (Cooper, 1968):
#
#     VO2max (ml/kg/min) = (distance_in_metres_in_12_min - 504.9) / 44.73
#
# We only run 9 minutes, so the 9-min distance must be converted to a
# 12-minute equivalent before the formula is applied.
#
# How the adaptation works (and why it is conservative):
#   - Naive scaling would be 12/9 = 1.333, i.e. assume he holds the exact
#     same pace for three extra minutes. Nobody does; pace fades as the
#     effort goes on, so 1.333 flatters the score.
#   - We use a fade-adjusted factor of 1.28. That is roughly the ratio seen
#     between 9-min and 12-min all-out distances in field running, and it
#     deliberately sits BELOW the naive 1.333.
#   - We then subtract 1.0 ml/kg/min as a youth/pacing safety margin. A
#     16-year-old doing his first timed run almost always paces it badly
#     (too fast early, walk breaks late), which inflates nothing but our
#     confidence. Better to under-promise and let him beat the number.
#
# Analogy: it's like reading a fuel gauge on a bumpy road - we round down,
# because running out of fuel is worse than arriving with some left.
#
# The 9-min run is the ONE hard effort. Every other run in the plan is
# conversational pace (he can speak a full sentence while running).

TWELVE_MIN_EQUIV_FACTOR = 1.28   # 9-min distance -> 12-min equivalent
YOUTH_SAFETY_MARGIN = 1.0        # ml/kg/min subtracted, keeps estimate low


def vo2max_from_9min_distance(metres_in_9_min):
    """Return an estimated VO2 max (ml/kg/min) from a 9-minute run distance."""
    twelve_min_equivalent = metres_in_9_min * TWELVE_MIN_EQUIV_FACTOR
    vo2 = (twelve_min_equivalent - 504.9) / 44.73
    vo2 -= YOUTH_SAFETY_MARGIN
    return max(vo2, 0.0)


def metres_from_pace(pace_min_per_km):
    """Convert an average pace (min/km) held for 9 minutes into metres."""
    # 9 minutes at X min/km covers 9 / X kilometres.
    return (9.0 / pace_min_per_km) * 1000.0


# Age-appropriate VO2 max categories.
# Reference: FITNESSGRAM Healthy Fitness Zone (HFZ) aerobic capacity standards
# for 16-year-old boys - HFZ starts around 41.8 ml/kg/min, with a
# "Needs Improvement" band below that and a lower "health risk" band
# below ~38.9. Wording here is kept encouraging and non-clinical.
def vo2_category_16yo_male(vo2):
    if vo2 >= 48:
        return "Strong for his age", 4
    if vo2 >= 44:
        return "Good - above the healthy zone", 3
    if vo2 >= 41.8:
        return "Healthy Fitness Zone (just inside)", 3
    if vo2 >= 38.9:
        return "Needs improvement - close to the zone", 2
    return "Needs improvement - build the base first", 1


# ---------------------------------------------------------------------------
# 2. MUSCLE ENDURANCE / FATIGUE TESTS  (no equipment)
# ---------------------------------------------------------------------------
#
# Rules for all three: stop the set when FORM BREAKS, not when it hurts.
# Near-failure, never true failure. Rest 2-3 minutes between tests.
# Each test scores 1-4 points. Bands are set for an untrained 16-year-old
# carrying extra bodyweight, so they are achievable, not elite charts.

def score_pushups(reps, on_knees):
    """Push-ups to near-failure. Knees are allowed and scored separately."""
    bands = [(25, 4), (15, 3), (8, 2)] if on_knees else [(20, 4), (10, 3), (5, 2)]
    for threshold, points in bands:
        if reps >= threshold:
            return points
    return 1


CORE_BANDS = {
    # test key: (label, unit, [(threshold, points), ...])
    "hollow": ("Hollow hold", "seconds", [(45, 4), (30, 3), (15, 2)]),
    "curlup": ("Curl-ups / sit-ups", "reps", [(40, 4), (25, 3), (15, 2)]),
    "deadbug": ("Dead bugs (per side)", "reps", [(25, 4), (15, 3), (8, 2)]),
}

EXTRA_BANDS = {
    "wallsit": ("Wall sit", "seconds", [(75, 4), (45, 3), (20, 2)]),
    "bridge": ("Glute bridge hold", "seconds", [(75, 4), (45, 3), (20, 2)]),
    "lunges": ("Walking lunges in place", "total reps", [(35, 4), (20, 3), (10, 2)]),
}


def score_from_bands(value, bands):
    for threshold, points in bands:
        if value >= threshold:
            return points
    return 1


def endurance_rating(total_points):
    """total_points is 3-12 (three tests, 1-4 each)."""
    if total_points >= 10:
        return "Strong muscular endurance - fatigues late"
    if total_points >= 8:
        return "Solid - good base to build on"
    if total_points >= 5:
        return "Developing - fatigues in the middle of a set"
    return "Building base - fatigues early, keep sets short"


# ---------------------------------------------------------------------------
# 3. COMBINED STARTING LEVEL
# ---------------------------------------------------------------------------
#
# Aerobic score (1-4) and average muscle score (1-4) are averaged.
# Level 1 = Foundation, Level 2 = Build, Level 3 = Progress.

def combined_level(aerobic_points, muscle_points_total):
    muscle_avg = muscle_points_total / 3.0
    overall = (aerobic_points + muscle_avg) / 2.0
    if overall >= 3.0:
        return 3, "Level 3 - Progress", overall
    if overall >= 2.0:
        return 2, "Level 2 - Build", overall
    return 1, "Level 1 - Foundation", overall


# ---------------------------------------------------------------------------
# 4. THE 3-WEEK HOME PLAN
# ---------------------------------------------------------------------------
#
# Built from the SAME movements he was tested on, so progress is obvious.
# Working sets are capped well below his test score - roughly 50-60% of
# near-failure reps - so he finishes sessions feeling able, not wrecked.
# Progression is small and boring on purpose: +1-2 reps, +5s holds,
# +10-20 m of running. No sudden intensity jumps.

LEVEL_SETTINGS = {
    1: {"strength_days": 2, "run_days": 2, "sets": 2, "work_fraction": 0.50},
    2: {"strength_days": 3, "run_days": 2, "sets": 3, "work_fraction": 0.55},
    3: {"strength_days": 3, "run_days": 3, "sets": 3, "work_fraction": 0.60},
}

WEEKLY_SCHEDULE = {
    1: "Mon: Strength | Tue: rest/walk | Wed: Easy run | Thu: rest "
       "| Fri: Strength | Sat: Easy run | Sun: full rest",
    2: "Mon: Strength | Tue: Easy run | Wed: Strength | Thu: rest/walk "
       "| Fri: Strength | Sat: Easy run | Sun: full rest",
    3: "Mon: Strength | Tue: Easy run | Wed: Strength | Thu: Easy run "
       "| Fri: Strength | Sat: Easy run | Sun: full rest",
}


def working_reps(test_result, fraction, week, step, minimum=3):
    """Working dose for a given week: a fraction of his test score, then
    a small weekly step up."""
    base = max(int(test_result * fraction), minimum)
    return base + step * (week - 1)


def build_plan(level, pushup_reps, on_knees, core_key, core_value,
               extra_key, extra_value, run_metres):
    s = LEVEL_SETTINGS[level]
    core_label, core_unit, _ = CORE_BANDS[core_key]
    extra_label, extra_unit, _ = EXTRA_BANDS[extra_key]

    lines = []
    lines.append("WEEKLY SHAPE (repeat for 3 weeks)")
    lines.append("  " + WEEKLY_SCHEDULE[level])
    lines.append("  Strength days: %d/week   Runs: %d/week   "
                 "Full rest: at least 1 day, never 2 hard days back to back"
                 % (s["strength_days"], s["run_days"]))
    lines.append("")

    for week in (1, 2, 3):
        push = working_reps(pushup_reps, s["work_fraction"], week, step=1)
        # Time-based holds step 5s/week; rep-based core steps 2 reps/week.
        core_step = 5 if core_unit == "seconds" else 2
        core = working_reps(core_value, s["work_fraction"], week, step=core_step)
        extra_step = 5 if extra_unit == "seconds" else 2
        extra = working_reps(extra_value, s["work_fraction"], week, step=extra_step)
        run = int(run_metres + 100 * (week - 1))  # +100 m per week, easy pace

        lines.append("WEEK %d" % week)
        lines.append("  Strength session (do the circuit %d times, "
                     "90s rest between rounds):" % s["sets"])
        lines.append("    - Push-ups%s: %d reps" %
                     (" (knees)" if on_knees else "", push))
        lines.append("    - %s: %d %s" % (core_label, core, core_unit))
        lines.append("    - %s: %d %s" % (extra_label, extra, extra_unit))
        lines.append("    - Bodyweight squats: 10-12 reps (free add-on, no weight)")
        lines.append("  Run day: 9 minutes EASY-to-MODERATE, target ~%d m." % run)
        lines.append("    Talking pace. Walk 30-60s whenever he needs it - "
                     "that still counts.")
        lines.append("")

    lines.append("HOW TO PROGRESS AFTER WEEK 3")
    lines.append("  If every session finished with clean form and no soreness")
    lines.append("  lasting past 48h: add 1-2 reps (or 5 seconds) per exercise,")
    lines.append("  and 10-20 m to the run target. Nothing bigger than that.")
    lines.append("  If a session felt rough: repeat the same week again.")
    lines.append("  Re-test everything at the end of week 4, not sooner.")
    return "\n".join(lines)


COACH_NOTES = """COACH NOTES (copy/paste to him)

Warm-up at home - 5 minutes, every session:
  - 1 min march or walk on the spot
  - 10 arm circles each direction, 10 shoulder rolls
  - 10 slow bodyweight squats (no weight, just movement)
  - 10 hip swings each leg, 20s easy jog on the spot
Before a run day, add 1 minute of easy jogging before you start the clock.

When to stop - not optional:
  - Stop the SET the moment your form breaks (hips sagging, neck straining,
    back arching). A clean set of 8 beats a messy set of 15.
  - Stop the SESSION if you feel chest pain, dizziness, a sharp joint pain,
    or you cannot catch your breath at all. Tell me the same day.
  - Sore for a day or two = normal. Sore for 3+ days = we did too much,
    message me and we cut the next session back.

About these numbers:
  - The VO2 max figure is an ESTIMATE from a running test, not a lab result.
    It is deliberately calculated on the low side, so it is a starting line
    to beat, not a grade.
  - Bodyweight scores are compared to YOUR last test, not to anybody else.
  - Do the 9-minute all-out run ONCE at the start. Every other run is easy
    conversational pace - if you cannot say a full sentence, slow down.
  - Sleep and food move these numbers more than any extra set will."""


# ---------------------------------------------------------------------------
# 5. INPUT HELPERS
# ---------------------------------------------------------------------------

def ask_float(prompt, low, high):
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            print("  Please enter a number.")
            continue
        if not (low <= value <= high):
            print("  Please enter a value between %g and %g." % (low, high))
            continue
        return value


def ask_choice(prompt, options):
    """options: dict of key -> label"""
    print(prompt)
    for key, label in options.items():
        print("   [%s] %s" % (key, label))
    while True:
        choice = input("  > ").strip().lower()
        if choice in options:
            return choice
        print("  Please type one of: %s" % ", ".join(options))


def ask_yes_no(prompt):
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please answer y or n.")


def ask_run_distance():
    """Three ways to report the 9-minute run, all ending in metres."""
    mode = ask_choice(
        "\nHow did he record the 9-minute run?",
        {"1": "Total distance in km (watch/phone)",
         "2": "Laps + lap length (track, pitch, or a measured path)",
         "3": "Average pace in min/km (phone app)"})

    if mode == "1":
        km = ask_float("  Distance covered in 9 minutes (km): ", 0.3, 4.0)
        return km * 1000.0
    if mode == "2":
        laps = ask_float("  Number of laps (decimals ok, e.g. 4.5): ", 0.5, 60)
        lap_m = ask_float("  Estimated lap length (metres): ", 20, 1000)
        return laps * lap_m
    pace = ask_float("  Average pace over the 9 minutes (min/km, e.g. 7.5): ",
                     3.0, 15.0)
    return metres_from_pace(pace)


# ---------------------------------------------------------------------------
# 6. MAIN
# ---------------------------------------------------------------------------

def main():
    print("=" * 68)
    print("HOME FITNESS ASSESSMENT + STARTER PROGRAM")
    print("No gym, no equipment. Bedroom / hallway / outdoors.")
    print("=" * 68)
    print("\nBefore you start: rest 2-3 minutes between every test,")
    print("and stop any set the moment form breaks.\n")

    # --- Basics ---
    age = ask_float("Age (years): ", 10, 19)
    height_cm = ask_float("Height (cm): ", 120, 210)
    weight_kg = ask_float("Weight (kg): ", 30, 200)

    # --- Test 1: 9-minute run ---
    run_metres = ask_run_distance()
    vo2 = vo2max_from_9min_distance(run_metres)
    vo2_label, aerobic_points = vo2_category_16yo_male(vo2)

    # --- Test 2: push-ups ---
    print("\nPush-ups to NEAR-failure (stop when form breaks). Knees allowed.")
    on_knees = ask_yes_no("  Were they done on the knees? (y/n): ")
    pushup_reps = ask_float("  Reps completed with good form: ", 0, 200)
    pushup_points = score_pushups(pushup_reps, on_knees)

    # --- Test 3: core ---
    core_key = ask_choice(
        "\nCore test used (pick one - no bench needed):",
        {"hollow": "Hollow hold (time in seconds)",
         "curlup": "Curl-ups / sit-ups (reps)",
         "deadbug": "Dead bugs (reps per side)"})
    core_label, core_unit, core_bands = CORE_BANDS[core_key]
    core_value = ask_float("  %s - result in %s: " % (core_label, core_unit),
                           0, 600)
    core_points = score_from_bands(core_value, core_bands)

    # --- Test 4: extra fatigue test ---
    extra_key = ask_choice(
        "\nExtra fatigue test (pick one):",
        {"wallsit": "Wall sit (time in seconds)",
         "bridge": "Glute bridge hold (time in seconds)",
         "lunges": "Walking lunges in place (total reps)"})
    extra_label, extra_unit, extra_bands = EXTRA_BANDS[extra_key]
    extra_value = ask_float("  %s - result in %s: " % (extra_label, extra_unit),
                            0, 600)
    extra_points = score_from_bands(extra_value, extra_bands)

    # --- Report ---
    muscle_total = pushup_points + core_points + extra_points
    level, level_label, overall = combined_level(aerobic_points, muscle_total)
    bmi = weight_kg / (height_cm / 100.0) ** 2

    print("\n" + "=" * 68)
    print("ASSESSMENT REPORT")
    print("=" * 68)
    print("Age %.0f | Height %.0f cm | Weight %.0f kg | BMI %.1f"
          % (age, height_cm, weight_kg, bmi))
    print("\nAEROBIC (9-minute run)")
    print("  Distance covered      : %d m" % round(run_metres))
    print("  Estimated VO2 max     : %.1f ml/kg/min" % vo2)
    print("  Category (16yo male)  : %s" % vo2_label)
    print("  Method: Cooper 12-min formula, applied to the 9-min distance")
    print("          scaled by %.2f, minus %.1f ml/kg/min youth margin."
          % (TWELVE_MIN_EQUIV_FACTOR, YOUTH_SAFETY_MARGIN))
    if age > 17:
        print("  Note: categories are calibrated for a 16-year-old male.")

    print("\nMUSCLE ENDURANCE / FATIGUE  (each test scored 1-4)")
    print("  Push-ups%-13s: %d reps  -> %d/4"
          % (" (knees)" if on_knees else "", pushup_reps, pushup_points))
    print("  %-21s: %g %s -> %d/4"
          % (core_label, core_value, core_unit, core_points))
    print("  %-21s: %g %s -> %d/4"
          % (extra_label, extra_value, extra_unit, extra_points))
    print("  Total                 : %d/12" % muscle_total)
    print("  Rating                : %s" % endurance_rating(muscle_total))

    print("\nCOMBINED STARTING LEVEL")
    print("  Aerobic %d/4 + muscle avg %.1f/4  ->  score %.1f"
          % (aerobic_points, muscle_total / 3.0, overall))
    print("  %s" % level_label)

    print("\n" + "=" * 68)
    print("3-WEEK HOME PLAN  (%s)" % level_label)
    print("=" * 68)
    print(build_plan(level, pushup_reps, on_knees, core_key, core_value,
                     extra_key, extra_value, run_metres))

    print("=" * 68)
    print(COACH_NOTES)
    print("=" * 68)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
