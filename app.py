import streamlit as st
from optimizer import get_idle_instances, stop_instances

st.title("🌥️ Cloud Resource Optimizer Dashboard (AWS Live)")

idle_threshold = st.slider("CPU Idle Threshold (%)", min_value=1, max_value=20, value=5)
min_days = st.slider("Minimum Idle Days", min_value=1, max_value=7, value=3)
region = st.text_input("AWS Region", value="us-east-1")

# Fetch AWS credentials securely from Streamlit secrets
aws_access_key = st.secrets["AWS"]["aws_access_key_id"]
aws_secret_key = st.secrets["AWS"]["aws_secret_access_key"]

if st.button("🚀 Run Optimization"):
    # 1. Get idle instances based on criteria, passing AWS keys
    report_df = get_idle_instances(region, idle_threshold, min_days, aws_access_key, aws_secret_key)
    
    if report_df.empty:
        st.success("✅ No idle instances found to stop.")
    else:
        st.subheader("Idle Instances Found")
        st.dataframe(report_df)
        
        # 2. Extract instance IDs to stop
        idle_instance_ids = report_df["InstanceId"].tolist()
        
        # 3. Automatically stop those instances, passing AWS keys
        logs = stop_instances(idle_instance_ids, region, aws_access_key, aws_secret_key)
        
        # 4. Show logs of stopping action
        st.subheader("Action Logs")
        st.text("\n".join(logs))
