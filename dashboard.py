import streamlit as st
import json
import pandas as pd

# Load step-level results
with open("results/step_level_output.json", "r") as f:
    data = json.load(f)

# Flatten steps into a DataFrame
records = []
for case in data:
    for step in case["Steps"]:
        records.append({
            "Test Case ID": case["Test Case ID"],
            "Test Description": case["Test Description"],
            "Expected Result": case["Expected Result"],
            "Actual Result": case["Actual Result"],
            "Step": step["Step"],
            "Feasibility": step["Feasibility"],
            "Recommended Tool": step["Recommended Tool"],
            "Confidence Score": step["Confidence Score"],
            "Rationale": step["Rationale"]
        })

df = pd.DataFrame(records)

# Dashboard layout
st.title("🧪 Step-Level Automation Feasibility Dashboard")

# Filter by Test Case ID
test_ids = df["Test Case ID"].unique()
selected_id = st.selectbox("Select Test Case ID", options=test_ids)
filtered_df = df[df["Test Case ID"] == selected_id]

# Feasibility Distribution
st.subheader("Feasibility Classification")
feasibility_counts = filtered_df["Feasibility"].value_counts()
st.bar_chart(feasibility_counts)

# Confidence Scores
st.subheader("Confidence Scores by Step")
st.line_chart(filtered_df[["Step", "Confidence Score"]].set_index("Step"))

# Tool Recommendations
st.subheader("Recommended Tools")
tool_counts = filtered_df["Recommended Tool"].value_counts()
st.dataframe(tool_counts)

# Detailed Table
st.subheader("Detailed Step Analysis")
st.dataframe(filtered_df[[
    "Step", "Feasibility", "Recommended Tool", "Confidence Score", "Rationale"
]])
