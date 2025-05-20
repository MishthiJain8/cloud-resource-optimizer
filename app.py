import streamlit as st
from optimizer import get_idle_instances, stop_instances

st.title("🌥️ Cloud Resource Optimizer Dashboard (AWS Live)")

idle_threshold = st.slider("CPU Idle Threshold (%)", min_value=1, max_value=20, value=5)
min_days = st.slider("Minimum Idle Days", min_value=1, max_value=7, value=3)
region = st.text_input("AWS Region", value="us-east-1")

if st.button("🚀 Run Optimization"):
    # 1. Get idle instances based on criteria
    report_df = get_idle_instances(region, idle_threshold, min_days)
    
    if report_df.empty:
        st.success("✅ No idle instances found to stop.")
    else:
        st.subheader("Idle Instances Found")
        st.dataframe(report_df)
        
        # 2. Extract instance IDs to stop
        idle_instance_ids = report_df["InstanceId"].tolist()
        
        # 3. Automatically stop those instances
        logs = stop_instances(idle_instance_ids, region)
        
        # 4. Show logs of stopping action
        st.subheader("Action Logs")
        st.text("\n".join(logs))
