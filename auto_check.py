import json
import pandas as pd
from datetime import datetime
import os
from localstack_client import session

# Parameters
IDLE_THRESHOLD = 5.0
MIN_DAYS = 3
INPUT_FILE = "instances.json"

os.makedirs("reports", exist_ok=True)
os.makedirs("logs", exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M")
OUTPUT_FILE = f"reports/idle_report_{timestamp}.csv"
LOG_FILE = f"logs/actions_{timestamp}.log"

s3 = session.Session().client('s3')
BUCKET_NAME = "test-bucket"

def analyze_instances():
    with open(INPUT_FILE, "r") as f:
        instances = json.load(f)

    report = []
    log_lines = []

    for instance in instances:
        low_usage_days = sum(cpu < IDLE_THRESHOLD for cpu in instance["CPUHistory"])
        is_idle = low_usage_days >= MIN_DAYS

        report.append({
            "Instance ID": instance["InstanceId"],
            "Type": instance["InstanceType"],
            "State": instance["State"],
            "Low Usage Days": low_usage_days,
            "Idle?": "Yes" if is_idle else "No"
        })

        if is_idle:
            # Simulate stopping instance
            log_lines.append(f"[AUTO-ACTION] Instance {instance['InstanceId']} is idle. Simulated stop triggered.")
        else:
            log_lines.append(f"[INFO] Instance {instance['InstanceId']} is active. No action taken.")

    # Save report and log
    df = pd.DataFrame(report)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Idle report saved to {OUTPUT_FILE}")

    with open(LOG_FILE, "w") as log:
        log.write("\n".join(log_lines))

    print(f"📝 Actions log saved to {LOG_FILE}")

    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
    except s3.exceptions.NoSuchBucket:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"Created S3 bucket: {BUCKET_NAME}")

    s3.upload_file(OUTPUT_FILE, BUCKET_NAME, f"reports/{os.path.basename(OUTPUT_FILE)}")
    print(f"☁️ Report uploaded to S3 as 'reports/{os.path.basename(OUTPUT_FILE)}'")

if __name__ == "__main__":
    analyze_instances()
