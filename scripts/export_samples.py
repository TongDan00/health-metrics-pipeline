import pandas as pd
import sqlite3
import os

# Create a folder 
os.makedirs('sample_data', exist_ok=True)

# Connect to the database
DB_PATH = "realistic_mock_data_v1/v1-t1d_mock.db"
conn = sqlite3.connect(DB_PATH)

# List the 5 tables
tables = ['cgm_data', 'daily_summary', 'exercise_log', 'insulin_log', 'meal_log']

print("Exporting small samples for the portfolio...")

# Loop through each table, retrieve 50 rows, and save them as CSV files.
for table in tables:
    query = f"SELECT * FROM {table} LIMIT 50;"
    df = pd.read_sql_query(query, conn)
    
    # Save into the new sample_data folder
    file_name = f"sample_data/sample_{table}.csv"
    df.to_csv(file_name, index=False)
    print(f"Created successfully {file_name}")

conn.close()
print("\nAll samples were exported successfully.")