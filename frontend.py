import requests
import streamlit as st
import io
import json
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
)

API_URL = "http://127.0.0.1:8000/review"
MAX_CODE_SIZE = 100_000
def build_pdf_report(report):
    """Build a downloadable PDF security report in memory."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="ReviewPilot AI Security Report",
        author="ReviewPilot AI",
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=23,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#172554"),
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=12,
        spaceAfter=7,
    ))

    styles.add(ParagraphStyle(
        name="SmallBody",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        spaceAfter=5,
        wordWrap="CJK",
    ))

    styles.add(ParagraphStyle(
        name="CodeText",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7,
        leading=9,
        backColor=colors.HexColor("#F1F5F9"),
        borderPadding=6,
        wordWrap="CJK",
    ))

    story = []

    def safe_text(value):
        """Escape dynamic content before inserting it into PDF paragraphs."""
        from xml.sax.saxutils import escape
        return escape(str(value if value is not None else "—"))

    def add_paragraph(value, style="SmallBody"):
        story.append(Paragraph(safe_text(value), styles[style]))

    story.append(Paragraph(
        "ReviewPilot AI",
        styles["ReportTitle"],
    ))
    story.append(Paragraph(
        "Code Security & AI Review Report",
        styles["Heading2"],
    ))
    story.append(Spacer(1, 5 * mm))

    add_paragraph(
        "Generated: "
        + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )
    add_paragraph(
        "Total findings: " + str(report.get("total_findings", 0))
    )

    story.append(Paragraph("Severity Summary", styles["SectionHeading"]))

    severity_counts = report.get("severity_counts", {})
    severity_rows = [
        ["Severity", "Findings"],
        ["Critical", str(severity_counts.get("critical", 0))],
        ["High", str(severity_counts.get("high", 0))],
        ["Medium", str(severity_counts.get("medium", 0))],
        ["Low", str(severity_counts.get("low", 0))],
        ["Informational", str(severity_counts.get("info", 0))],
    ]

    severity_table = Table(
        severity_rows,
        colWidths=[90 * mm, 45 * mm],
        repeatRows=1,
    )
    severity_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(severity_table)

    ai_review = report.get("ai_review", {})
    if not isinstance(ai_review, dict):
        ai_review = {}

    story.append(Paragraph("AI Review Summary", styles["SectionHeading"]))
    add_paragraph(
        ai_review.get("summary", "No AI summary was returned.")
    )

    story.append(Paragraph("Detected Findings", styles["SectionHeading"]))

    findings = report.get("findings", [])
    if not isinstance(findings, list):
        findings = []

    if not findings:
        add_paragraph("No findings were reported by the configured analyzers.")
    else:
        for index, finding in enumerate(findings, start=1):
            if not isinstance(finding, dict):
                continue

            story.append(Paragraph(
                f"Finding {index}: {safe_text(finding.get('rule_id', 'Unknown rule'))}",
                styles["Heading3"],
            ))

            add_paragraph(
                "Severity: " + str(finding.get("severity", "Unknown"))
                + " | Tool: " + str(finding.get("tool", "Unknown"))
                + " | Line: " + str(finding.get("line", "Unknown"))
            )
            add_paragraph("Issue: " + str(
                finding.get("message", "No message provided.")
            ))
            add_paragraph("Description: " + str(
                finding.get("description", "No description provided.")
            ))

            suggestion = finding.get("suggestion")
            if suggestion:
                add_paragraph("Analyzer suggestion: " + str(suggestion))

            story.append(Spacer(1, 2 * mm))

    explanations = ai_review.get("explanations", [])
    if not isinstance(explanations, list):
        explanations = []

    story.append(Paragraph("AI Explanations & Suggested Fixes", styles["SectionHeading"]))

    if not explanations:
        add_paragraph("No AI explanations were returned for this review.")
    else:
        for explanation in explanations:
            if not isinstance(explanation, dict):
                continue

            story.append(Paragraph(
                "Rule: " + safe_text(explanation.get("rule_id", "General")),
                styles["Heading3"],
            ))

            explanation_text = explanation.get("explanation", "")
            if explanation_text:
                add_paragraph("Why this matters: " + str(explanation_text))

            suggestion = explanation.get("suggestion", "")
            if suggestion:
                add_paragraph("Suggested fix: " + str(suggestion))

            corrected_code = explanation.get("corrected_code", "")
            if isinstance(corrected_code, str) and corrected_code.strip():
                story.append(Paragraph(
                    "Suggested corrected code",
                    styles["Heading4"],
                ))
                story.append(Preformatted(
                    corrected_code[:12000],
                    styles["CodeText"],
                ))

            story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Reviewed Source Code", styles["SectionHeading"]))

    source_code = report.get("reviewed_code", "")
    if source_code:
        story.append(Preformatted(
            str(source_code)[:20000],
            styles["CodeText"],
        ))
    else:
        add_paragraph("No source code was included in the report.")

    story.append(Spacer(1, 5 * mm))
    add_paragraph(
        "Disclaimer: Findings and AI suggestions require human review. "
        "A clean report does not guarantee that code is secure. "
        "Suggested fixes are not automatically applied or tested."
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


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

if "reviewed_code" not in st.session_state:
    st.session_state.reviewed_code = ""

if "code_input" not in st.session_state:
    st.session_state.code_input = (
        'def calculate(a, b):\n'
        '    return eval("a + b")\n'
    )

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
        st.session_state.reviewed_code = ""
        st.rerun()

    st.divider()
    st.caption("ReviewPilot AI · Portfolio Edition")

# -------------------- Code Input --------------------

st.subheader("📝 Analyze Python Code")

code = st.text_area(
    "Paste your Python code below",
    key="code_input",
    height=260,
    help="Maximum input size: 100 KB.",
)

left, right = st.columns([3, 1])

with left:
    review_clicked = st.button(
        "🔍 Analyze Code",
        type="primary",
        use_container_width=True,
    )

with right:
    st.caption(f"Characters: {len(code):,} / {MAX_CODE_SIZE:,}")

# -------------------- Submit Review --------------------

if review_clicked:
    st.session_state.review_result = None
    st.session_state.review_error = None
    st.session_state.reviewed_code = ""

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
                    st.session_state.reviewed_code = code

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

    if not isinstance(findings, list):
        findings = []

    if not isinstance(ai_review, dict):
        ai_review = {}

    if not isinstance(explanations, list):
        explanations = []

    def severity_of(finding):
        if not isinstance(finding, dict):
            return "unknown"

        value = str(
            finding.get("severity", "unknown")
        ).lower().strip()

        if value in {
            "critical", "high", "medium", "low",
            "info", "informational",
        }:
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

    # -------------------- Security Overview --------------------

    st.subheader("📊 Security Overview")

    metrics = st.columns(5)

    metrics[0].metric("Total Findings", len(findings))
    metrics[1].metric("Critical / High", high_risk)
    metrics[2].metric("Medium", counts["medium"])
    metrics[3].metric("Low", counts["low"])
    metrics[4].metric("AI Explanations", len(explanations))

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

    # -------------------- Severity Distribution --------------------

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
            options=[
                "critical", "high", "medium",
                "low", "info", "unknown",
            ],
            default=[
                "critical", "high", "medium",
                "low", "info", "unknown",
            ],
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

        for finding in filtered_findings:
            if not isinstance(finding, dict):
                continue

            severity = severity_of(finding)
            rule_id = finding.get("rule_id", "Unknown rule")
            message = finding.get("message", "Finding")
            file_name = finding.get("file", "Unknown")
            line_number = finding.get("line", "Unknown")

            title = f"{severity.upper()} · {rule_id} · {message}"

            with st.expander(title):
                detail_columns = st.columns(3)

                detail_columns[0].write(
                    f"**Tool:** {finding.get('tool', 'Unknown')}"
                )
                detail_columns[1].write(f"**File:** {file_name}")
                detail_columns[2].write(f"**Line:** {line_number}")

                st.markdown("**Description**")
                st.write(finding.get("description", message))

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

                explanation_text = explanation.get("explanation", "")
                if explanation_text:
                    st.markdown("**Why this matters**")
                    st.write(explanation_text)

                suggestion = explanation.get("suggestion", "")
                if suggestion:
                    st.markdown("**Suggested Fix**")
                    st.write(suggestion)

                corrected_code = explanation.get("corrected_code", "")

                if isinstance(corrected_code, str) and corrected_code.strip():
                    st.markdown("### Before vs. After Code Comparison")

                    before_col, after_col = st.columns(2)

                    with before_col:
                        st.markdown("**🔴 Before — Original Code**")
                        st.code(
                            st.session_state.reviewed_code,
                            language="python",
                        )

                    with after_col:
                        st.markdown("**🟢 After — Suggested Fix**")
                        st.code(corrected_code, language="python")

                    st.caption(
                        "The suggested code has not been automatically "
                        "applied or tested. Review it before using it."
                    )

    elif summary != "No issues were detected by the static analyzers.":
        st.info(
            "AI explanations are unavailable for this review. "
            "The static analysis results are still shown above."
        )

    # -------------------- Developer Details --------------------

    with st.expander("Developer Details — Complete JSON Response"):
        st.json(result)

    # -------------------- Export Review Report --------------------

    st.subheader("📥 Export Security Report")

    report = {
        "project": "ReviewPilot AI",
        "reviewed_code": st.session_state.reviewed_code,
        "total_findings": len(findings),
        "severity_counts": {
            "critical": counts["critical"],
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"],
            "info": counts["info"],
        },
        "findings": findings,
        "ai_review": ai_review,
    }

    st.download_button(
        label="⬇️ Download JSON Report",
        data=__import__("json").dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        file_name="reviewpilot_security_report.json",
        mime="application/json",
        use_container_width=True,
    )
    pdf_bytes = build_pdf_report(report)

    st.download_button(
        label="📄 Download PDF Security Report",
        data=pdf_bytes,
        file_name="reviewpilot_security_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

# -------------------- Footer --------------------

st.divider()

st.caption(
    "ReviewPilot AI · FastAPI · Streamlit · Ruff · Bandit · Ollama"
)
