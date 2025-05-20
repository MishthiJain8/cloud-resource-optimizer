import json
import pandas as pd
from tabulate import tabulate

# Load instance data
with open("instances.json", "r") as f:
    instances = json.load(f)

idle_threshold = 5.0  # Percent CPU
min_days = 3  # Minimum number of low usage days to mark idle

report = []

for instance in instances:
    low_usage_days = sum(cpu < idle_threshold for cpu in instance["CPUHistory"])
    is_idle = low_usage_days >= min_days

    report.append({
        "InstanceId": instance["InstanceId"],
        "Type": instance["InstanceType"],
        "State": instance["State"],
        "Low Usage Days": low_usage_days,
        "Idle?": "Yes" if is_idle else "No"
    })

df = pd.DataFrame(report)
print(tabulate(df, headers="keys", tablefmt="grid"))

# Save report
df.to_csv("report.csv", index=False)
