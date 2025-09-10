@echo off
echo Starting Streamlit app...
start cmd /k ".venv\Scripts\streamlit.exe run app.py"

timeout /t 5 >nul

echo Starting ngrok tunnel...
start cmd /k "ngrok http 8501"