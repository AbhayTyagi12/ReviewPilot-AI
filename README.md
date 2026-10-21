# ReviewPilot AI 🛡️

**AI-Powered Code Review and Security Analysis Platform**

ReviewPilot AI is a Python-based code review tool that combines static analysis and AI-generated explanations to help developers identify potential bugs, security vulnerabilities, and code quality issues.

## 🚀 Features

- **Automated Code Analysis:** Detects code quality issues using Ruff.
- **Security Scanning:** Identifies common security risks using Bandit.
- **AI-Powered Explanations:** Uses a local Ollama model to explain findings and suggest improvements.
- **Severity Dashboard:** Displays findings by severity, with filtering and sorting.
- **Before-and-After Comparison:** Review suggested code fixes alongside the original code.
- **Security Reports:** Download review results as JSON and PDF.
- **Interactive Web Interface:** Analyze Python code through a Streamlit dashboard.
- **REST API:** Submit code for analysis using a FastAPI backend.

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | Backend REST API |
| Streamlit | Interactive dashboard |
| Ruff | Linting and code quality analysis |
| Bandit | Python security analysis |
| Ollama | Local AI inference |
| ReportLab | PDF report generation |
| Pytest | Automated testing |

## 🏗️ Architecture

1. The user submits Python code through the Streamlit dashboard.
2. The frontend sends the code to the FastAPI backend.
3. Ruff and Bandit analyze the submitted code.
4. The AI reviewer generates explanations and suggested fixes when available.
5. Findings are displayed in the dashboard and can be exported as JSON or PDF.

## ⚙️ Installation and Setup

### Prerequisites

- Python installed
- Git installed
- Ollama installed for local AI reviews

### 1. Clone the repository

```bash
git clone https://github.com/AbhayTyagi12/ReviewPilot-AI.git
cd ReviewPilot-AI
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Start the backend

Open a terminal in the project folder:

```powershell
python -m uvicorn main:app --reload
```

Backend: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

### 6. Start the frontend

Open a second terminal in the project folder:

```powershell
python -m streamlit run frontend.py
```

Dashboard: http://localhost:8501

### 7. Enable AI reviews

Install and start Ollama, then make sure the configured model is available:

```powershell
ollama pull qwen2.5-coder:1.5b
ollama run qwen2.5-coder:1.5b
```

Keep Ollama running while using AI review features. The static analysis features may work independently of Ollama.

## 🧪 Running Tests

Run the automated test suite from the project root:

```powershell
python -m pytest -v
```

**Current development status:** 10 tests passed in the local test run.

## 📊 Example Use Case

Consider this potentially unsafe Python function:

```python
def calculate(a, b):
    return eval("a + b")
```

Bandit can flag the use of `eval()` as a security concern. ReviewPilot AI can help explain the finding and recommend replacing the expression with:

```python
def calculate(a, b):
    return a + b
```

Always review suggested fixes and test them before using them in production.

## 🗺️ Roadmap

- [x] FastAPI backend
- [x] Streamlit dashboard
- [x] Ruff and Bandit integration
- [x] AI-assisted explanations
- [x] JSON and PDF report exports
- [x] Automated tests
- [ ] GitHub pull-request integration
- [ ] CI/CD pipeline
- [ ] Expanded test coverage and benchmarking

## 🔒 Security Note

ReviewPilot AI is a development and educational tool. AI-generated suggestions may be incomplete or incorrect. Validate findings and test suggested changes before merging or deploying code.

## 👨‍💻 Author

**Abhay Tyagi**

GitHub: [AbhayTyagi12](https://github.com/AbhayTyagi12)

---

*Built as a portfolio project exploring Python development, application security, static analysis, and AI-assisted code review.*
