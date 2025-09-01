import streamlit as st
import pandas as pd
import json
from ollama import Client
from concurrent.futures import ThreadPoolExecutor, as_completed

client = Client()

# Prompt builder with multiple tools + primary recommendation
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
            "Recommended Tools": result.get("Recommended Tools", []),
            "Recommended Primary Tool": result.get("Recommended Primary Tool", "Unknown"),
            "Confidence Score": int(result.get("Confidence Score", 0)),
            "Rationale": result.get("Rationale", "No rationale provided.")
        }
    except Exception as e:
        return {
            "Step": step_text,
            "Feasibility": "Error",
            "Recommended Tools": ["N/A"],
            "Recommended Primary Tool": "N/A",
            "Confidence Score": 0,
            "Rationale": f"Failed to analyze: {str(e)}"
        }

# Extract step number for sorting
def extract_step_number(step_text):
    try:
        return int(step_text.split('.')[0].strip())
    except:
        return 9999

# Streamlit UI
st.title("📎Test Cases Automation Feasibility Analyzer")

uploaded_file = st.file_uploader("Attach your Test Cases Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="Sheet1")
    required_columns = ["Test Case ID", "Test Description", "Steps", "Expected Result", "Actual Result"]
    if not all(col in df.columns for col in required_columns):
        st.error("❌ Excel file must contain columns: Test Case ID, Test Description, Steps, Expected Result, Actual Result")
    else:
        if st.button("🔍 Analyze"):
            st.info("⏳ Running analysis...")

            all_results = []

            for _, row in df.iterrows():
                test_id = row["Test Case ID"]
                description = row["Test Description"]
                steps_raw = str(row["Steps"]).strip()
                expected = str(row["Expected Result"]).strip()
                actual = str(row["Actual Result"]).strip()

                steps = [s.strip() for s in steps_raw.split("\n") if s.strip()]
                step_results = []

                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = {executor.submit(analyze_step, step): step for step in steps}
                    for future in as_completed(futures):
                        result = future.result()
                        step_results.append(result)

                step_results.sort(key=lambda x: extract_step_number(x["Step"]))

                for step in step_results:
                    all_results.append({
                        "Test Case ID": test_id,
                        "Test Description": description,
                        "Expected Result": expected,
                        "Actual Result": actual,
                        "Step": step["Step"],
                        "Feasibility": step["Feasibility"],
                        "Recommended Tools": ", ".join(step["Recommended Tools"]),
                        "Recommended Primary Tool": step["Recommended Primary Tool"],
                        "Confidence Score": step["Confidence Score"],
                        "Rationale": step["Rationale"]
                    })

            result_df = pd.DataFrame(all_results)

            st.success("✅ Analysis complete!")

            # Visuals
            st.subheader("Feasibility Distribution")
            st.bar_chart(result_df["Feasibility"].value_counts())

            st.subheader("Confidence Scores by Step")
            st.line_chart(result_df[["Step", "Confidence Score"]].set_index("Step"))

            st.subheader("Tool Recommendations")
            tool_series = result_df["Recommended Tools"].str.split(", ").explode()
            st.dataframe(tool_series.value_counts())

            st.subheader("Primary Tool Recommendations")
            st.dataframe(result_df["Recommended Primary Tool"].value_counts())

            st.subheader("Detailed Step-Level Analysis")
            st.dataframe(result_df)
