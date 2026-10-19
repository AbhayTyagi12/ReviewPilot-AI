
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/review"
MAX_CODE_SIZE = 100_000

st.set_page_config(
    page_title="ReviewPilot AI | Security Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Session State --------------------

if "review_result" not in st.session_state:
    st.session_state.review_result = None

if "review_error" not in st.session_state:
    st.session_state.review_error = None

# -------------------- Styling --------------------

st.markdown(
    """
    <style>
    .stApp {
        background: #0b1120;
        color: #e2e8f0;
    }

    [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #263449;
    }

    .hero {
        padding: 1.8rem;
        border-radius: 18px;
        background: linear-gradient(120deg, #172554, #1e293b);
        border: 1px solid #334155;
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        color: #f8fafc;
        font-size: 2.3rem;
        margin-bottom: 0.4rem;
    }

    .hero p {
        color: #cbd5e1;
        margin-bottom: 0;
        font-size: 1rem;
    }

    div[data-testid="stMetric"] {
        background: #111c30;
        border: 1px solid #29384f;
        padding: 1rem;
        border-radius: 14px;
    }

    .section-label {
        color: #94a3b8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }

    div.stButton > button {
        border-radius: 10px;
        min-height: 2.7rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="section-label">AI-powered developer security</div>
        <h1>🛡️ ReviewPilot AI</h1>
        <p>
            Find potential bugs, detect security risks, and understand
            how to improve your Python code with AI-assisted reviews.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------- Sidebar --------------------

with st.sidebar:
    st.header("⚙️ ReviewPilot")

    st.markdown("**Analysis engines**")
    st.write("🔎 Ruff — Python linting")
    st.write("🛡️ Bandit — security checks")
    st.write("🤖 Ollama — local AI review")

    st.divider()

    st.caption(
        "Code is submitted to your configured local FastAPI backend. "
        "Avoid running untrusted code."
    )

    if st.button("🗑️ Clear Results", use_container_width=True):
        st.session_state.review_result = None
        st.session_state.review_error = None
        st.rerun()

    st.divider()
    st.caption("ReviewPilot AI · Portfolio Edition")

# -------------------- Code Input --------------------

st.subheader("📝 Submit Python Code")

code = st.text_area(
    "Paste your code",
    height=300,
    placeholder=(
        "def calculate(value):\n"
        "    return eval(value)\n"
    ),
    help="Maximum submission size: 100 KB.",
)

left, right = st.columns([3, 1])

with left:
    review_clicked = st.button(
        "🔍 Analyze Code",
        type="primary",
        use_container_width=True,
    )

with right:
    st.caption(f"Characters: {len(code):,}")

# -------------------- Submit Review --------------------

if review_clicked:
    st.session_state.review_result = None
    st.session_state.review_error = None

    if not code.strip():
        st.session_state.review_error = (
            "Please enter some Python code first."
        )

    elif len(code.encode("utf-8")) > MAX_CODE_SIZE:
        st.session_state.review_error = (
            "Code exceeds the 100 KB limit."
        )

    else:
        try:
            with st.spinner(
                "Running static analysis and generating AI explanations..."
            ):
                response = requests.post(
                    API_URL,
                    json={"code": code},
                    timeout=(5, 300),
                )

                if response.status_code != 200:
                    try:
                        detail = response.json().get(
                            "detail",
                            "The API returned an error.",
                        )
                    except (ValueError, AttributeError):
                        detail = "The API returned an error."

                    st.session_state.review_error = (
                        f"Review failed: {detail}"
                    )

                else:
                    result = response.json()

                    if not isinstance(result, dict):
                        raise ValueError(
                            "The API returned an unexpected response."
                        )

                    if not isinstance(result.get("findings", []), list):
                        raise ValueError(
                            "The API returned invalid findings data."
                        )

                    if not isinstance(result.get("ai_review", {}), dict):
                        result["ai_review"] = {}

                    st.session_state.review_result = result

        except requests.exceptions.Timeout:
            st.session_state.review_error = (
                "The review timed out. The local AI model may be busy. "
                "Please try again."
            )

        except requests.exceptions.ConnectionError:
            st.session_state.review_error = (
                "Cannot connect to the FastAPI backend. "
                "Ensure the backend is running and try again."
            )

        except requests.exceptions.RequestException as error:
            st.session_state.review_error = f"Request failed: {error}"

        except ValueError as error:
            st.session_state.review_error = (
                f"Invalid review response: {error}"
            )

# -------------------- Errors --------------------

if st.session_state.review_error:
    st.error(st.session_state.review_error)

# -------------------- Results Dashboard --------------------

result = st.session_state.review_result

if result is not None:
    findings = result.get("findings", [])
    ai_review = result.get("ai_review", {})
    explanations = ai_review.get("explanations", [])

    if not isinstance(explanations, list):
        explanations = []

    # Normalize severity labels for dashboard counting and sorting.
    def severity_of(finding):
        value = str(finding.get("severity", "unknown")).lower().strip()

        if value in {"critical", "high", "medium", "low", "info", "informational"}:
            return "info" if value == "informational" else value

        return "unknown"

    severity_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "info": 4,
        "unknown": 5,
    }

    ordered_findings = sorted(
        findings,
        key=lambda item: severity_order[severity_of(item)],
    )

    counts = {
        severity: sum(
            1 for finding in findings
            if severity_of(finding) == severity
        )
        for severity in ["critical", "high", "medium", "low", "info"]
    }

    high_risk = counts["critical"] + counts["high"]

    st.success("Code review completed.")

    st.subheader("📊 Security Overview")

    metrics = st.columns(4)

    metrics[0].metric("Total Findings", len(findings))
    metrics[1].metric("Critical / High", high_risk)
    metrics[2].metric("Medium", counts["medium"])
    metrics[3].metric("AI Explanations", len(explanations))

    if high_risk:
        st.warning(
            f"Prioritize remediation: {high_risk} critical or high-severity "
            "finding(s) detected."
        )
    elif findings:
        st.info("No critical or high-severity findings were reported.")
    else:
        st.success(
            "No findings were reported by the configured static analyzers. "
            "This does not guarantee that the code is secure."
        )

    # Severity distribution.
    st.subheader("Severity Distribution")

    severity_columns = st.columns(5)

    for column, severity in zip(
        severity_columns,
        ["critical", "high", "medium", "low", "info"],
    ):
        column.metric(severity.title(), counts[severity])

    # -------------------- Static Findings --------------------

    st.subheader("🔎 Static Analysis Findings")

    if not ordered_findings:
        st.info("No static analysis findings were returned.")
    else:
        severity_filter = st.multiselect(
            "Filter by severity",
            options=["critical", "high", "medium", "low", "info", "unknown"],
            default=["critical", "high", "medium", "low", "info", "unknown"],
            format_func=lambda value: value.title(),
        )

        filtered_findings = [
            finding for finding in ordered_findings
            if severity_of(finding) in severity_filter
        ]

        st.caption(
            f"Showing {len(filtered_findings)} of {len(findings)} findings, "
            "sorted by severity."
        )

        for index, finding in enumerate(filtered_findings, start=1):
            severity = severity_of(finding)
            rule_id = finding.get("rule_id", "Unknown rule")
            message = finding.get("message", "Finding")
            file_name = finding.get("file", "Unknown")
            line_number = finding.get("line", "Unknown")

            title = (
                f"{severity.upper()} · {rule_id} · {message}"
            )

            with st.expander(title):
                detail_columns = st.columns(3)
                detail_columns[0].write(
                    f"**Tool:** {finding.get('tool', 'Unknown')}"
                )
                detail_columns[1].write(f"**File:** {file_name}")
                detail_columns[2].write(f"**Line:** {line_number}")

                st.markdown("**Description**")
                st.write(
                    finding.get(
                        "description",
                        message,
                    )
                )

                if finding.get("confidence") is not None:
                    st.write(
                        f"**Confidence:** {finding['confidence']}"
                    )

                suggestion = finding.get("suggestion")

                if suggestion:
                    st.markdown("**Suggested Fix**")
                    st.write(suggestion)

    # -------------------- AI Review --------------------

    st.subheader("🤖 AI Review")

    summary = ai_review.get("summary", "")

    if summary:
        st.markdown("**Review Summary**")
        st.write(summary)

    if explanations:
        for explanation in explanations:
            if not isinstance(explanation, dict):
                continue

            rule_id = explanation.get("rule_id", "General")

            with st.container(border=True):
                st.markdown(f"**Rule:** {rule_id}")

                st.write(
                    explanation.get(
                        "explanation",
                        "No explanation provided.",
                    )
                )

                st.markdown("**Suggested Fix**")
                st.write(
                    explanation.get(
                        "suggestion",
                        "No suggestion provided.",
                    )
                )

    elif summary != "No issues were detected by the static analyzers.":
        st.info(
            "AI explanations are unavailable for this review. "
            "The static analysis results are still shown above."
        )

    # -------------------- Debugging --------------------

    with st.expander("Developer Details — Complete JSON Response"):
        st.json(result)

# -------------------- Footer --------------------

st.divider()

st.caption(
    "ReviewPilot AI · FastAPI · Streamlit · Ruff · Bandit · Ollama"
)
