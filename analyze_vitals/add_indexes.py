import sqlite3

# Connect to the database
DB_PATH = "/Users/yutong/Documents/code/git_test/health-metrics-pipeline/realistic_mock_data_v1/v1-t1d_mock.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Building indexes to speed up the database. This should only take a second.")

# Create indexes on the time columns used in joins
cursor.execute("CREATE INDEX IF NOT EXISTS idx_cgm_time ON cgm_data(Timestamp);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_meal_time ON meal_log(Timestamp);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercise_time ON exercise_log(Workout_Start);")

conn.commit()
conn.close()

print("Indexes created successfully.")