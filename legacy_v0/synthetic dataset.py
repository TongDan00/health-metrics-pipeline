
import pandas as pd
import random
from datetime import datetime, timedelta

# Set up the last 180 days
start_date = datetime.now() - timedelta(days=180)
dates = [start_date + timedelta(days=i) for i in range(180)]

# Generate random, realistic fake data
data = {
    "Date": [d.strftime("%Y-%m-%d") for d in dates],
    "Calories": [random.randint(1978, 2500) for _ in range(180)],
    "Carbs_g": [random.randint(10, 50) for _ in range(180)],
    "Protein_g": [random.randint(50, 100) for _ in range(180)],
    "Insulin_Units": [random.randint(25, 35) for _ in range(180)],
    "Morning_Blood_Sugar": [round(random.uniform(5.0, 15.0), 1) for _ in range(180)], 
    "Sleep_Hours": [round(random.uniform(5.5, 10.0), 1) for _ in range(180)],
    "Stress_Level": [random.choice(["Low", "Medium", "High"]) for _ in range(180)]
}

# Create a table
df = pd.DataFrame(data)

# Save it as an Excel/CSV file
df.to_csv("mock_health_data.csv", index=False)
print("Success! Your fake dataset 'mock_health_data.csv' is ready.")