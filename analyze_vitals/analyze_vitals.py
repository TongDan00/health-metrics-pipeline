import sqlite3
import pandas as pd
from pathlib import Path

# Connect to the database
DB_PATH = "/Users/yutong/Documents/code/git_test/health-metrics-pipeline/realistic_mock_data_v1/v1-t1d_mock.db"
conn = sqlite3.connect(DB_PATH)

print("📊 Analyzing Type 1 Diabetes mock data...\n" + "="*50)

# ==========================================================================
# Question 1: How much does each meal raise blood glucose?
# ==========================================================================
print("\n🍽️ 🥗 Question 1: How does the average glucose spike vary by meal type?")
q1_sql = """
WITH MealSpikes AS (
    SELECT 
        m.Meal_ID,
        m.Meal_Type,
        c_start.Blood_Sugar AS Starting_BG,
        MAX(c_window.Blood_Sugar) AS Peak_BG
    FROM meal_log m
    -- Get the exact blood sugar at the time of the meal
    JOIN cgm_data c_start ON c_start.Timestamp = m.Timestamp
    -- Look at all CGM readings in the 2 hours AFTER the meal
    JOIN cgm_data c_window ON c_window.Timestamp BETWEEN m.Timestamp AND datetime(m.Timestamp, '+2 hours')
    GROUP BY m.Meal_ID
)
SELECT 
    Meal_Type, 
    COUNT(*) as Total_Meals,
    ROUND(AVG(Peak_BG - Starting_BG), 2) AS Avg_Spike_mmolL
FROM MealSpikes
GROUP BY Meal_Type
ORDER BY Avg_Spike_mmolL DESC;
"""
print(pd.read_sql_query(q1_sql, conn).to_string(index=False))


# ==========================================================================
# Question 2: Does walking or running after a meal reduce the glucose spike?
# ==========================================================================
print("\n🏃🧘 Question 2: Impact of post-meal cardio on glucose spikes")
q2_sql = """
WITH MealSpikes AS (
    SELECT 
        m.Meal_ID,
        m.Timestamp AS Meal_Time,
        c_start.Blood_Sugar AS Starting_BG,
        MAX(c_window.Blood_Sugar) AS Peak_BG
    FROM meal_log m
    JOIN cgm_data c_start ON c_start.Timestamp = m.Timestamp
    JOIN cgm_data c_window ON c_window.Timestamp BETWEEN m.Timestamp AND datetime(m.Timestamp, '+2 hours')
    GROUP BY m.Meal_ID
),
PostMealExercise AS (
    -- Find meals where a walk or run started within 2 hours after eating
    SELECT DISTINCT ms.Meal_ID, 'Yes' AS Did_Cardio
    FROM MealSpikes ms
    JOIN exercise_log e 
        ON e.Workout_Start BETWEEN ms.Meal_Time AND datetime(ms.Meal_Time, '+2 hours')
    WHERE e.Workout_Type IN ('Walk', 'Run')
)
SELECT 
    COALESCE(pme.Did_Cardio, 'No') AS Exercised_After_Meal,
    COUNT(*) as Meal_Count,
    ROUND(AVG(ms.Peak_BG - ms.Starting_BG), 2) AS Avg_Spike_mmolL
FROM MealSpikes ms
LEFT JOIN PostMealExercise pme ON ms.Meal_ID = pme.Meal_ID
GROUP BY Exercised_After_Meal;
"""
print(pd.read_sql_query(q2_sql, conn).to_string(index=False))


# ==========================================================================
# Question 3: Morning vs. evening exercise
# ==========================================================================
print("\n☀️ 🌠 Question 3: Does morning or evening exercise have a bigger impact?")
q3_sql = """
WITH ExerciseImpact AS (
    SELECT 
        e.Workout_Type,
        CAST(strftime('%H', e.Workout_Start) AS INTEGER) AS Start_Hour,
        c_start.Blood_Sugar AS Starting_BG,
        -- Get blood sugar exactly at the end of the active minutes
        c_end.Blood_Sugar AS Ending_BG
    FROM exercise_log e
    JOIN cgm_data c_start ON c_start.Timestamp = e.Workout_Start
    JOIN cgm_data c_end ON c_end.Timestamp = datetime(e.Workout_Start, '+' || e.Active_Minutes || ' minutes')
    WHERE e.Workout_Start IS NOT NULL
)
SELECT 
    CASE 
        WHEN Start_Hour < 12 THEN 'Morning'
        ELSE 'Evening'
    END AS Time_Of_Day,
    Workout_Type,
    ROUND(AVG(Ending_BG - Starting_BG), 2) AS Avg_BG_Change_mmolL
FROM ExerciseImpact
GROUP BY Time_Of_Day, Workout_Type
HAVING Workout_Type IN ('Run', 'Walk', 'Strength')
ORDER BY Workout_Type, Time_Of_Day;
"""
print(pd.read_sql_query(q3_sql, conn).to_string(index=False))


# ==========================================================================
# Question 4: Does bolus timing matter: late vs. early?
# ==========================================================================
print("\n⏱️ ⏳ Question 4: Does bolus timing affect meal spikes?")
q4_sql = """
WITH MealSpikes AS (
    SELECT 
        m.Meal_ID,
        i.Timing_Minutes_From_Meal,
        c_start.Blood_Sugar AS Starting_BG,
        MAX(c_window.Blood_Sugar) AS Peak_BG
    FROM meal_log m
    JOIN insulin_log i ON m.Meal_ID = i.Meal_ID
    JOIN cgm_data c_start ON c_start.Timestamp = m.Timestamp
    JOIN cgm_data c_window ON c_window.Timestamp BETWEEN m.Timestamp AND datetime(m.Timestamp, '+2 hours')
    GROUP BY m.Meal_ID
)
SELECT 
    CASE 
        WHEN Timing_Minutes_From_Meal < 0 THEN '1. Pre-bolus (Early)'
        WHEN Timing_Minutes_From_Meal == 0 THEN '2. Exact Time'
        ELSE '3. Late Bolus'
    END AS Bolus_Timing,
    ROUND(AVG(Timing_Minutes_From_Meal), 1) as Avg_Minutes_Offset,
    ROUND(AVG(Peak_BG - Starting_BG), 2) AS Avg_Spike_mmolL
FROM MealSpikes
GROUP BY Bolus_Timing
ORDER BY Bolus_Timing;
"""
print(pd.read_sql_query(q4_sql, conn).to_string(index=False))

conn.close()