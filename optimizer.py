import boto3
import pandas as pd
from datetime import datetime, timedelta

def get_cpu_metrics(cloudwatch, instance_id, start_time, end_time):
    """Fetch average CPU utilization per day for the last N days."""
    metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name':'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=86400,  # 1 day
        Statistics=['Average']
    )
    datapoints = metrics.get('Datapoints', [])
    # Sort datapoints by timestamp ascending
    datapoints = sorted(datapoints, key=lambda x: x['Timestamp'])
    # Extract average CPU values per day
    cpu_avgs = [point['Average'] for point in datapoints]
    return cpu_avgs

def get_idle_instances(region, idle_threshold, min_days):
    """Returns a DataFrame of EC2 instances idle according to threshold and days."""
    ec2 = boto3.client('ec2', region_name=region)
    cloudwatch = boto3.client('cloudwatch', region_name=region)

    # Describe all running instances
    response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )

    instances_data = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)  # Check last 7 days

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            state = instance['State']['Name']

            cpu_avgs = get_cpu_metrics(cloudwatch, instance_id, start_time, end_time)
            low_usage_days = sum(cpu < idle_threshold for cpu in cpu_avgs)

            is_idle = low_usage_days >= min_days

            instances_data.append({
                "InstanceId": instance_id,
                "InstanceType": instance_type,
                "State": state,
                "LowUsageDays": low_usage_days,
                "Idle": "Yes" if is_idle else "No"
            })

    df = pd.DataFrame(instances_data)

    if df.empty:
        # Return empty DataFrame with expected columns to avoid KeyError
        return pd.DataFrame(columns=["InstanceId", "InstanceType", "State", "LowUsageDays", "Idle"])

    # Debug: print columns to help debug issues
    print("Columns in DataFrame:", df.columns.tolist())

    # Filter only idle instances
    return df[df['Idle'] == "Yes"]

def stop_instances(instance_ids, region):
    """Stop the given list of EC2 instance IDs and return logs."""
    ec2 = boto3.client('ec2', region_name=region)
    logs = []

    if not instance_ids:
        logs.append("[INFO] No instances to stop.")
        return logs

    try:
        ec2.stop_instances(InstanceIds=instance_ids)
        for iid in instance_ids:
            logs.append(f"[ACTION] Stopped instance {iid}")
    except Exception as e:
        logs.append(f"[ERROR] Failed to stop instances: {str(e)}")

    return logs
