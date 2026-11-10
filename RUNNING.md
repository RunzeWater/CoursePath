# Run the scaffold in VS Code

This version is a command-line prerequisite checker. It does not include a Streamlit app.
All source comments and docstrings are in English.

Open this folder in VS Code. In its PowerShell terminal, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m coursepath --courses data/sample_courses.json --completed "DEMO 101" "DEMO 201"
.\.venv\Scripts\python.exe -m pytest tests
```

After setup, press Ctrl+Shift+B to run the example. Use Terminal > Run Task > CoursePath: run tests to run the test suite.

The example marks DEMO 101 and DEMO 301 eligible. With only DEMO 101 completed, DEMO 301 is ineligible because DEMO 201 or DEMO 202 is still required.
