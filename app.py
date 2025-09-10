import streamlit as st
import pandas as pd
import json
from ollama import Client
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import plotly.graph_objects as go

client = Client()

# IBM-inspired styling
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #f4f6f9, #e6ecf3);
        font-family: 'Segoe UI', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #3C6DF0;
    }
    .footer {
        text-align: center;
        color: #3C6DF0;
        font-weight: bold;
        margin-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Prompt builder
def build_step_prompt(step_text):
    return [
        {'role': 'system', 'content': 'You are a QA automation expert. Respond ONLY in JSON format.'},
        {'role': 'user', 'content': f"""
Analyze the following test step and respond strictly in JSON format:

Step: "{step_text}"

Respond with:
{{
  "Feasibility": "Automatable / Partially Automatable / Not Automatable",
  "Recommended Tools": ["Selenium", "Cypress", "Appium", "Manual"],
  "Recommended Primary Tool": "Select one tool name from the list above that best fits this step, considering platform compatibility, ease of setup, team skillset, and UI interaction type. Return only the tool name.",
  "Confidence Score": 0-100,
  "Rationale": "Brief explanation"
}}

Guidelines:
- Return only valid JSON. No markdown, bullet points, or extra commentary.
- Do NOT include parentheses, qualifiers, or extra text in tool names.
- Use only the tools listed above. If multiple tools apply, include them all in "Recommended Tools".
- Choose one best-fit tool for "Recommended Primary Tool" based on platform compatibility, ease of setup, and UI interaction type.
"""}
    ]

# Analyze a single step
def analyze_step(step_text):
    try:
        response = client.chat(model='mistral', messages=build_step_prompt(step_text))
        content = response['message']['content'].strip()
        result = json.loads(content)
        return {
            "Step": step_text,
            "Feasibility": result.get("Feasibility", "Unknown"),
            "Recommended Tools": ", ".join(result.get("Recommended Tools", [])),
            "Recommended Primary Tool": result.get("Recommended Primary Tool", "Unknown"),
            "Confidence Score": int(result.get("Confidence Score", 0)),
            "Rationale": result.get("Rationale", "No rationale provided.")
        }
    except Exception as e:
        return {
            "Step": step_text,
            "Feasibility": "Error",
            "Recommended Tools": "N/A",
            "Recommended Primary Tool": "N/A",
            "Confidence Score": 0,
            "Rationale": f"Failed to analyze: {str(e)}"
        }

# Highlight feasibility
def highlight_feasibility(val):
    color = {
        "Automatable": "#d4edda",
        "Partially Automatable": "#fff3cd",
        "Not Automatable": "#f8d7da",
        "Error": "#f5c6cb"
    }.get(val, "#ffffff")
    return f"background-color: {color}"

feasibility_colors = {
    "Automatable": "#d4edda",           # light green
    "Partially Automatable": "#fff3cd", # light yellow
    "Not Automatable": "#f8d7da",       # light red
    "Error": "#f5c6cb"                  # optional, if used
}

tool_colors = {
    "Selenium": "#43B02A",        # Selenium green
    "Cypress": "#00BFA5",         # Cypress teal
    "Appium": "#9B59B6",          # Appium purple
    "Manual": "#A6B1C2"           # Neutral gray
}

# App layout
st.set_page_config(page_title="Test Cases Automation Analyzer", layout="wide")
st.title("🔍 Test Cases Automation Feasibility Analyzer")

uploaded_file = st.file_uploader("📁 Upload your Test Cases Excel file", type=["xlsx"])

# Run analysis once
if uploaded_file and "result_df" not in st.session_state:
    df = pd.read_excel(uploaded_file, sheet_name="Sheet1")
    required_columns = ["Test Case ID", "Test Description", "Steps", "Expected Result", "Actual Result"]
    if not all(col in df.columns for col in required_columns):
        st.error("❌ Excel must contain: Test Case ID, Test Description, Steps, Expected Result, Actual Result")
    else:
        if st.button("🔍 Analyze"):
            st.info("⏳ Analyzing test steps...")
            all_results = []

            for _, row in df.iterrows():
                test_id = row["Test Case ID"]
                description = row["Test Description"]
                expected = row["Expected Result"]
                actual = row["Actual Result"]
                steps = [s.strip() for s in str(row["Steps"]).split("\n") if s.strip()]

                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = {executor.submit(analyze_step, step): step for step in steps}
                    for future in as_completed(futures):
                        result = future.result()
                        result.update({
                            "Test Case ID": test_id,
                            "Test Description": description,
                            "Expected Result": expected,
                            "Actual Result": actual
                        })
                        all_results.append(result)

            result_df = pd.DataFrame(all_results)

            # Reorder Step-Level Analysis columns
            ordered_columns = [
                "Test Case ID", "Test Description", "Step", "Feasibility",
                "Recommended Tools", "Recommended Primary Tool", "Confidence Score",
                "Rationale", "Expected Result", "Actual Result"
            ]
            result_df = result_df[ordered_columns]

            # Classify test cases and include Recommended Primary Tool
            test_case_summary = []
            for test_id, group in result_df.groupby("Test Case ID"):
                feasibilities = group["Feasibility"].tolist()
                if all(f == "Automatable" for f in feasibilities):
                    case_feasibility = "Automatable"
                elif all(f == "Not Automatable" for f in feasibilities):
                    case_feasibility = "Not Automatable"
                else:
                    case_feasibility = "Partially Automatable"

                primary_tool = group["Recommended Primary Tool"].iloc[0]

                test_case_summary.append({
                    "Test Case ID": test_id,
                    "Test Description": group["Test Description"].iloc[0],
                    "Total Steps": len(group),
                    "Feasibility": case_feasibility,
                    "Recommended Primary Tool": primary_tool
                })

            summary_df = pd.DataFrame(test_case_summary)

            # Store results
            st.session_state.result_df = result_df
            st.session_state.summary_df = summary_df
            st.success("✅ Analysis complete!")

# Display results
if "result_df" in st.session_state and "summary_df" in st.session_state:
    result_df = st.session_state.result_df
    summary_df = st.session_state.summary_df

    st.subheader("📊 Summary Overview")
    st.metric("Total Test Cases", len(summary_df))
    st.metric("Total Steps Analyzed", len(result_df))
    st.metric("Automatable", summary_df["Feasibility"].value_counts().get("Automatable", 0))
    st.metric("Partially Automatable", summary_df["Feasibility"].value_counts().get("Partially Automatable", 0))
    st.metric("Not Automatable", summary_df["Feasibility"].value_counts().get("Not Automatable", 0))

    st.markdown("## 📊 Visual Insights")
    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.markdown("### 📋 Step-Level Analysis")
        st.dataframe(result_df.style.applymap(highlight_feasibility, subset=["Feasibility"]))

        st.markdown("### 🧾 Test Case Summary")
        st.dataframe(summary_df.style.applymap(highlight_feasibility, subset=["Feasibility"]))

    with right_col:
        st.markdown("### 🧮 Feasibility Breakdown (Test Cases)")
        fig1, ax1 = plt.subplots()
        feasibility_counts = summary_df["Feasibility"].value_counts()
        feasibility_labels = feasibility_counts.index.tolist()
        feasibility_values = feasibility_counts.values.tolist()
        feasibility_chart_colors = [feasibility_colors.get(label, "#ffffff") for label in feasibility_labels]
        ax1.pie(
            feasibility_values,
            labels=feasibility_labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=feasibility_chart_colors
        )
        ax1.set_ylabel("")
        st.pyplot(fig1)

        st.markdown("### 🧰 Tool Usage Across Test Cases")
        tool_case_series = result_df.groupby("Test Case ID")["Recommended Primary Tool"].first()
        tool_counts = tool_case_series.value_counts()
        tool_labels = tool_counts.index.tolist()
        tool_values = tool_counts.values.tolist()
        tool_chart_colors = [tool_colors.get(tool, "#CCCCCC") for tool in tool_labels]
        fig_tool = go.Figure(data=[
            go.Bar(
                x=tool_labels,
                 y=tool_values,
                 marker_color=tool_chart_colors,
                 text=tool_values,
                 textposition='auto',
                 hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
                )
            ])
        fig_tool.update_layout(
            title="Tool Usage Across Test Cases",
            xaxis_title="Tool",
            yaxis_title="Count",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_tool, use_container_width=True)
            
    st.markdown("### 📥 Export Results")
    st.markdown("""
<div style="display: flex; gap: 10px;">
    <div>
        <a href="data:file/csv;base64,{step_csv}" download="automation_feasibility_results.csv">
            <button style="background-color:#3C6DF0;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;">
                ⬇️ Download Step-Level Analysis
            </button>
        </a>
    </div>
    <div>
        <a href="data:file/csv;base64,{summary_csv}" download="test_case_summary.csv">
            <button style="background-color:#3C6DF0;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;">
                ⬇️ Download Test Case Summary
            </button>
        </a>
    </div>
</div>
""".format(
    step_csv=result_df.to_csv(index=False).encode().decode("utf-8"),
    summary_csv=summary_df.to_csv(index=False).encode().decode("utf-8")
), unsafe_allow_html=True)

    st.markdown("""
<div style="text-align:center; font-size:13px; color:#6c757d; margin-top:30px;">
    &copy; 2025 Devanath Kuna · All rights reserved
</div>
""", unsafe_allow_html=True)