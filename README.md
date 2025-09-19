# 🧪 Automation Feasibility Analyzer

This **Streamlit dashboard** evaluates the feasibility of automating test cases using a **local LLM via Ollama**. It loads test cases from an Excel file, runs classification, and displays results in a **branded, judge-ready UI**.


---

## 🚀 Setup Instructions

### 1. 📦 Install Python 3.12

Download and install Python 3.12 from the official Python website:  
👉 [https://www.python.org/downloads/release/python-3120/](https://www.python.org/downloads/release/python-3120/)

✅ **Important**: During installation, check the box **“Add Python to PATH”**

---

### 2. 🧠 Install Ollama (Local LLM Runtime)

Ollama allows you to run large language models (LLMs) locally on your machine.

#### 🔧 Windows Installation

1. Download and install Ollama:  
   👉 [https://ollama.com/download](https://ollama.com/download)

2. Verify the installation in your terminal:

    ```bash
    ollama --version
    ```

3. Pull the required model for feasibility classification:

    ```bash
    ollama pull mistral
    ```

    > 💡 You can replace `mistral` with any other supported model like `llama3`, `codellama`, etc., depending on your use case.

---

### 3. 📦 Install Python Dependencies

Install the required packages using `pip`:

```bash
python -m pip install -r requirements.txt

🌐 Launch the Dashboard
Start the Streamlit dashboard with:

streamlit run app.py
You can run this in:

✅ VS Code Terminal

✅ Command Prompt / PowerShell

The dashboard will open automatically in your default web browser upload your Test cases excel and click analyze button.

👨‍💻 Author
Built by:
Devanath Kuna
Senior Test Automation Specialist @ IBM
📍 Bengaluru, India
