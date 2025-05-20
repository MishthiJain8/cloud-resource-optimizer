import boto3
import pandas as pd
from datetime import datetime, timedelta

# Create AWS clients with passed credentials
def create_clients(region, aws_access_key, aws_secret_key):
    try:
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        ec2 = session.client("ec2")
        cloudwatch = session.client("cloudwatch")
        return ec2, cloudwatch
    except Exception as e:
        raise RuntimeError(f"Error creating AWS clients: {e}")

# Fetch CPU metrics for an instance
def get_cpu_metrics(cloudwatch, instance_id, start_time, end_time):
    try:
        metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # 1 day
            Statistics=['Average']
        )
        datapoints = sorted(metrics.get('Datapoints', []), key=lambda x: x['Timestamp'])
        return [point['Average'] for point in datapoints]
    except Exception as e:
        print(f"[ERROR] Failed to get CPU metrics for {instance_id}: {e}")
        return []

# Find idle instances based on CPU threshold and min days idle
def get_idle_instances(region, idle_threshold=10.0, min_days=5, aws_access_key=None, aws_secret_key=None):
    ec2, cloudwatch = create_clients(region, aws_access_key, aws_secret_key)

    response = ec2.describe_instances(Filters=[
        {'Name': 'instance-state-name', 'Values': ['running']}
    ])

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)

    instances_data = []

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']

            cpu_avgs = get_cpu_metrics(cloudwatch, instance_id, start_time, end_time)
            low_usage_days = sum(cpu < idle_threshold for cpu in cpu_avgs)
            is_idle = low_usage_days >= min_days

            instances_data.append({
                "InstanceId": instance_id,
                "InstanceType": instance_type,
                "LowUsageDays": low_usage_days,
                "Idle": "Yes" if is_idle else "No"
            })

    df = pd.DataFrame(instances_data)
    if df.empty:
        return pd.DataFrame(columns=["InstanceId", "InstanceType", "LowUsageDays", "Idle"])

    return df[df["Idle"] == "Yes"]

# Stop given EC2 instances
def stop_instances(region, instance_ids, aws_access_key=None, aws_secret_key=None):
    ec2, _ = create_clients(region, aws_access_key, aws_secret_key)
    logs = []

    if not instance_ids:
        logs.append("[INFO] No idle instances to stop.")
        return logs

    try:
        ec2.stop_instances(InstanceIds=instance_ids)
        for iid in instance_ids:
            logs.append(f"[ACTION] Stopped instance: {iid}")
    except Exception as e:
        logs.append(f"[ERROR] Failed to stop instances: {e}")

    return logs
