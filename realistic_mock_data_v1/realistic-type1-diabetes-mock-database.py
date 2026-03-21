"""
T1D Mock Data Generator
Description: Generates 360 days of simulated Type 1 diabetes data, including CGM readings,
             insulin doses, meals, exercise effects, and daily summaries for SQL practice
             and data analysis.
"""

import sqlite3
from pathlib import Path
import random
from datetime import datetime, timedelta
import pandas as pd
import math

SCRIPT_DIR = Path(__file__).parent.resolve()
DB_PATH = SCRIPT_DIR / "v1-t1d_mock.db"

random.seed(42)

start_date = datetime(2025, 6, 1)
num_days = 360

meal_rows = []
exercise_rows = []
insulin_rows = []
cgm_rows = []
daily_summary_rows = [] # Added to track sick days and daily metrics

for day_offset in range(num_days):
    day = start_date + timedelta(days=day_offset)
    day_str = day.strftime("%Y-%m-%d")

    # Simulate Dawn Phenomenon (morning blood sugar rise)
    dawn_effect = random.uniform(0.3, 1.2)   

    meals = [
        ("Breakfast", 8, 15, random.randint(25, 55)),
        ("Lunch", 12, 45, random.randint(40, 80)),
        ("Dinner", 18, 30, random.randint(35, 75)),
    ]

    if random.random() < 0.35:
        meals.append(("Snack", 15, 30, random.randint(10, 25)))

    workout_type = None
    workout_intensity = None
    workout_minutes = 0
    workout_start = None

    r = random.random()
    if r < 0.30:
        workout_type = "Rest"
        workout_intensity = "None"
        workout_minutes = 0
    elif r < 0.60:
        workout_type = "Walk"
        workout_intensity = "Light"
        workout_minutes = random.choice([20, 30, 40])
        workout_start = datetime(day.year, day.month, day.day, random.choice([13, 19]), random.choice([0, 15, 30]))
    elif r < 0.82:
        workout_type = "Run"
        workout_intensity = "Moderate"
        workout_minutes = random.choice([25, 30, 40, 45])
        workout_start = datetime(day.year, day.month, day.day, random.choice([7, 18]), random.choice([0, 15, 30]))
    else:
        workout_type = "Strength"
        workout_intensity = "High"
        workout_minutes = random.choice([30, 40, 50])
        workout_start = datetime(day.year, day.month, day.day, random.choice([17, 18, 19]), random.choice([0, 15, 30]))

    steps = random.randint(3000, 12000) if workout_type == "Rest" else random.randint(7000, 16000)

    exercise_rows.append({
        "Date": day_str,
        "Workout_Type": workout_type,
        "Intensity": workout_intensity,
        "Active_Minutes": workout_minutes,
        "Steps": steps,
        "Workout_Start": workout_start.strftime("%Y-%m-%d %H:%M:%S") if workout_start else None
    })

    meal_events = []
    for meal_type, h, m, carbs in meals:
        meal_time = datetime(day.year, day.month, day.day, h, m)

        # Insulin-to-carb ratio is roughly 1 unit per 10-14 g
        ratio = random.uniform(10, 14)
        bolus_units = round(carbs / ratio + random.uniform(-0.5, 0.8), 1)
        bolus_units = max(0, bolus_units)

        bolus_timing_min = random.choice([-15, -10, -5, 0, 10, 15])
        bolus_time = meal_time + timedelta(minutes=bolus_timing_min)

        meal_rows.append({
            "Meal_ID": f"{day_str}_{meal_type}",
            "Timestamp": meal_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Meal_Type": meal_type,
            "Carbs_g": carbs
        })

        insulin_rows.append({
            "Meal_ID": f"{day_str}_{meal_type}",
            "Timestamp": bolus_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Insulin_Type": "Bolus",
            "Units": bolus_units,
            "Timing_Minutes_From_Meal": bolus_timing_min
        })

        meal_events.append({
            "meal_time": meal_time,
            "meal_type": meal_type,
            "carbs": carbs,
            "bolus_units": bolus_units,
            "bolus_delay": bolus_timing_min
        })
        
    # Is the person sick today? (5% chance)
    is_sick = random.random() < 0.05
    
    # If sick, baseline glucose is higher and more resistant to insulin
    illness_bg_boost = random.uniform(1.5, 3.0) if is_sick else 0.0
    sensor_noise = 0.5 if is_sick else 0.25 # Simulates the Tylenol/medication sensor errors
    
    # Save daily context variables for later queries
    daily_summary_rows.append({
        "Date": day_str,
        "Is_Sick": int(is_sick), # 1 for True, 0 for False
        "Dawn_Effect_Intensity": round(dawn_effect, 2),
        "Illness_BG_Boost": round(illness_bg_boost, 2)
    })
    
    # Generate CGM readings every 5 minutes
    current_time = datetime(day.year, day.month, day.day, 0, 0)
    end_time = current_time + timedelta(days=1)

    while current_time < end_time:
        hour = current_time.hour + current_time.minute / 60.0

        # Combine baseline, circadian rhythm, and sick day boost
        bg = 5.6 + 0.3 * math.sin((hour - 3) / 24 * 2 * math.pi) + illness_bg_boost

        # Use the dawn_effect generated at the start of the day
        if 4 <= hour <= 8:
            bg += dawn_effect

        # Calculate how meals and insulin timing affect current BG
        for meal in meal_events:
            mins_after_meal = (current_time - meal["meal_time"]).total_seconds() / 60
            if 0 <= mins_after_meal <= 180:
                spike_height = meal["carbs"] / 18.0
                
                # Adjust spike based on bolus timing
                if meal["bolus_delay"] > 0:
                    spike_height += 0.6
                if meal["bolus_delay"] < 0:
                    spike_height -= 0.3

                meal_curve = spike_height * math.exp(-((mins_after_meal - 75) ** 2) / (2 * 35 ** 2))
                bg += max(0, meal_curve)

            mins_after_bolus = (current_time - (meal["meal_time"] + timedelta(minutes=meal["bolus_delay"]))).total_seconds() / 60
            if 20 <= mins_after_bolus <= 240:
                insulin_drop = (meal["bolus_units"] / 5.0) * math.exp(-((mins_after_bolus - 110) ** 2) / (2 * 55 ** 2))
                bg -= max(0, insulin_drop)

        # Calculate exercise impact
        if workout_start and workout_minutes > 0:
            mins_after_workout = (current_time - workout_start).total_seconds() / 60

            if 0 <= mins_after_workout <= workout_minutes + 90:
                if workout_type in ["Walk", "Run"]:
                    bg -= 0.4 if workout_type == "Walk" else 0.8
                elif workout_type == "Strength":
                    if mins_after_workout <= workout_minutes:
                        bg += 0.5
                    else:
                        bg -= 0.3

            # Delayed drop effect from aerobic exercise
            if workout_type in ["Walk", "Run"] and 60 <= mins_after_workout <= 360:
                bg -= 0.3

       # Add realistic sensor noise before saving
        bg += random.uniform(-sensor_noise, sensor_noise)
        bg = round(max(3.2, min(bg, 16.5)), 1)

        cgm_rows.append({
            "Timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Blood_Sugar": bg
        })

        # Move to the next 5-minute interval
        current_time += timedelta(minutes=5)

# Convert all lists to dataframes
meal_df = pd.DataFrame(meal_rows)
exercise_df = pd.DataFrame(exercise_rows)
insulin_df = pd.DataFrame(insulin_rows)
cgm_df = pd.DataFrame(cgm_rows)
daily_summary_df = pd.DataFrame(daily_summary_rows)

# Save mock data to a local SQLite database for later analysis
if DB_PATH.exists():
    DB_PATH.unlink()

# Connect and write dataframes to tables
conn = sqlite3.connect(DB_PATH)
meal_df.to_sql("meal_log", conn, index=False, if_exists="replace")
exercise_df.to_sql("exercise_log", conn, index=False, if_exists="replace")
insulin_df.to_sql("insulin_log", conn, index=False, if_exists="replace")
cgm_df.to_sql("cgm_data", conn, index=False, if_exists="replace")
daily_summary_df.to_sql("daily_summary", conn, index=False, if_exists="replace")

conn.close()

print(f"Mock database successfully created at: {DB_PATH}")

# Export all tables to CSV 
meal_df.to_csv(SCRIPT_DIR / "meal_log.csv", index=False)
exercise_df.to_csv(SCRIPT_DIR / "exercise_log.csv", index=False)
insulin_df.to_csv(SCRIPT_DIR / "insulin_log.csv", index=False)
cgm_df.to_csv(SCRIPT_DIR / "cgm_data.csv", index=False)
daily_summary_df.to_csv(SCRIPT_DIR / "daily_summary.csv", index=False)

print("All CSV files were generated successfully.")