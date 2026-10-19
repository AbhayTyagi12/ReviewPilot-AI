
import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/review"
MAX_CODE_SIZE = 100_000

st.set_page_config(
    page_title="ReviewPilot AI",
    page_icon="🛡️",
    layout="wide",
)

# Initialize persistent session state.
if "review_result" not in st.session_state:
    st.session_state.review_result = None

if "review_error" not in st.session_state:
    st.session_state.review_error = None


# -------------------- Styling --------------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] {
        background-color: #111827;
    }
    .hero {
        padding: 1.5rem;
        border-radius: 16px;
        background: linear-gradient(120deg, #172554, #1e293b);
        border: 1px solid #334155;
        margin-bottom: 1.5rem;
    }
    .hero h1 {
        margin-bottom: 0.3rem;
        color: #f8fafc;
    }
    .hero p {
        color: #cbd5e1;
        margin-bottom: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🛡️ ReviewPilot AI</h1>
        <p>
            AI-powered Python code review, security analysis,
            and actionable fix suggestions.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("About")
    st.write("Static analysis: Ruff + Bandit")
    st.write("Local AI: Qwen 2.5 Coder via Ollama")
    st.caption("Your submitted code is sent to your local API.")

    if st.button("🗑️ Clear Results", use_container_width=True):
        st.session_state.review_result = None
        st.session_state.review_error = None
        st.rerun()


# -------------------- Code Input --------------------

st.subheader("Submit Python code")

code = st.text_area(
    "Paste your Python code below",
    height=320,
    placeholder=(
        "def calculate(value):\n"
        "    return eval(value)\n"
    ),
)

review_clicked = st.button(
    "🔍 Review Code",
    type="primary",
    use_container_width=True,
)


# -------------------- Submit Review --------------------

if review_clicked:
    # Remove previous results when a new review is requested.
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
                "Analyzing code and generating explanations..."
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
                    except ValueError:
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

                    st.session_state.review_result = result

        except requests.exceptions.Timeout:
            st.session_state.review_error = (
                "The review took too long. Your local model may be busy. "
                "Please try again."
            )

        except requests.exceptions.ConnectionError:
            st.session_state.review_error = (
                "Cannot connect to the FastAPI backend. "
                "Start the backend and try again."
            )

        except requests.exceptions.RequestException as error:
            st.session_state.review_error = (
                f"Request failed: {error}"
            )

        except ValueError as error:
            st.session_state.review_error = (
                f"Invalid review response: {error}"
            )


# -------------------- Display Errors --------------------

if st.session_state.review_error:
    st.error(st.session_state.review_error)


# -------------------- Display Saved Results --------------------

result = st.session_state.review_result

if result is not None:
    findings = result.get("findings", [])
    ai_review = result.get("ai_review", {})
    explanations = ai_review.get("explanations", [])

    st.success("Code review completed.")

    metric_columns = st.columns(3)

    metric_columns[0].metric(
        "Total findings",
        result.get("issue_count", len(findings)),
    )

    metric_columns[1].metric(
        "Files analyzed",
        1,
    )

    metric_columns[2].metric(
        "AI explanations",
        len(explanations),
    )

    # Static analysis results.
    st.subheader("Static Analysis Findings")

    if not findings:
        st.info("No issues were detected by the analyzers.")

    else:
        for finding in findings:
            severity = str(
                finding.get("severity", "unknown")
            ).upper()

            rule_id = finding.get("rule_id", "Unknown rule")
            message = finding.get("message", "Finding")

            with st.expander(
                f"{severity} · {rule_id} · {message}"
            ):
                st.write(
                    "**Tool:**",
                    finding.get("tool", "Unknown"),
                )

                st.write(
                    "**File:**",
                    finding.get("file", "Unknown"),
                )

                st.write(
                    "**Line:**",
                    finding.get("line", "Unknown"),
                )

                st.write(
                    "**Description:**",
                    finding.get(
                        "description",
                        finding.get("message", ""),
                    ),
                )

                if finding.get("suggestion"):
                    st.write(
                        "**Suggested fix:**",
                        finding["suggestion"],
                    )

    # AI-generated review.
    st.subheader("🤖 AI Review")

    summary = ai_review.get("summary", "")

    if summary:
        st.write(summary)

    if explanations:
        for explanation in explanations:
            with st.container(border=True):
                st.markdown(
                    "**Rule:** "
                    + str(explanation.get("rule_id", "General"))
                )

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

    elif summary != (
        "No issues were detected by the static analyzers."
    ):
        st.info(
            "No AI explanations are available for this review."
        )

    # Full API response for debugging.
    with st.expander("View Complete JSON Response"):
        st.json(result)


# -------------------- Footer --------------------

st.divider()

st.caption(
    "ReviewPilot AI · Built with FastAPI, Streamlit, Ruff, Bandit and Ollama"
)
