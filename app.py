# app.py
import sys
if sys.version_info < (3, 11):
    raise RuntimeError("Python 3.11+ required. Run: python3.11 -m pip install -r requirements.txt")

import streamlit as st
from dotenv import load_dotenv

from graph import fact_checker_graph
from state import FactCheckerState
from utils.formatting import verdict_color, verdict_emoji, confidence_label, severity_color

load_dotenv()

st.set_page_config(
    page_title="FactCheck AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ──
st.markdown("""
<style>
    .verdict-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
        color: white;
        letter-spacing: 0.5px;
    }
    .verdict-TRUE        { background: #1a7f37; }
    .verdict-FALSE       { background: #cf222e; }
    .verdict-MISLEADING  { background: #9a6700; }
    .verdict-UNVERIFIABLE{ background: #57606a; }
    .verdict-DISPUTED    { background: #0550ae; }

    .confidence-bar-container {
        background: #e9ecef;
        border-radius: 4px;
        height: 10px;
        margin-top: 6px;
        overflow: hidden;
    }
    .confidence-bar-fill {
        height: 10px;
        border-radius: 4px;
        transition: width 0.4s ease;
    }

    .source-card {
        padding: 6px 10px;
        margin: 4px 0;
        border-left: 3px solid #0550ae;
        background: #f6f8fa;
        border-radius: 4px;
        font-size: 13px;
    }

    .verdict-banner {
        border-radius: 12px;
        padding: 24px 32px;
        text-align: center;
        margin-bottom: 24px;
    }

    .fallacy-card {
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #e1e4e8;
        margin-bottom: 12px;
        background: #fafbfc;
        color: #24292f;
    }
    .fallacy-card strong {
        color: #24292f;
    }
    .fallacy-card em {
        color: #444d56;
    }

    .section-header {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 12px;
        padding-bottom: 6px;
        border-bottom: 2px solid #e1e4e8;
    }

    .stExpander > div > div {
        padding: 12px !important;
    }

    div[data-testid="metric-container"] {
        background: #f6f8fa;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ── DISPLAY RESULTS FUNCTION (must be defined before button block) ──

def display_results(state: dict) -> None:
    """Render the full fact-check results UI."""
    overall   = state.get("overall_verdict", "UNVERIFIABLE")
    score     = state.get("credibility_score", 0)
    summary   = state.get("executive_summary", "")
    sub_claims = state.get("sub_claims", [])
    fallacies  = state.get("fallacies", [])
    report     = state.get("final_report", "")

    # ── OVERALL VERDICT BANNER ──
    verdict_bg = {
        "TRUE":          "#d4edda",
        "FALSE":         "#f8d7da",
        "MISLEADING":    "#fff3cd",
        "UNVERIFIABLE":  "#e2e3e5",
        "DISPUTED":      "#cce5ff",
    }
    verdict_fg = {
        "TRUE":          "#155724",
        "FALSE":         "#721c24",
        "MISLEADING":    "#856404",
        "UNVERIFIABLE":  "#383d41",
        "DISPUTED":      "#004085",
    }
    bg  = verdict_bg.get(overall, "#e2e3e5")
    fg  = verdict_fg.get(overall, "#383d41")
    emj = verdict_emoji(overall)

    st.markdown(f"""
    <div style="background:{bg}; border:1px solid {fg}40; border-radius:12px;
                padding:24px 32px; text-align:center; margin-bottom:24px;">
        <div style="font-size:48px; margin-bottom:8px;">{emj}</div>
        <div style="font-size:28px; font-weight:800; color:{fg}; letter-spacing:2px;">{overall}</div>
        <div style="font-size:16px; color:{fg}; margin-top:8px; opacity:0.85;">
            Credibility Score: {score}/100 — {confidence_label(score)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if summary:
        st.info(f"**Summary:** {summary}")

    st.divider()

    # ── METRICS ROW ──
    m1, m2, m3, m4 = st.columns(4)
    true_count        = sum(1 for sc in sub_claims if sc.get("verdict") == "TRUE")
    false_count       = sum(1 for sc in sub_claims if sc.get("verdict") == "FALSE")
    misleading_count  = sum(1 for sc in sub_claims if sc.get("verdict") == "MISLEADING")
    avg_confidence    = int(
        sum(sc.get("confidence", 0) for sc in sub_claims) / max(len(sub_claims), 1)
    )

    m1.metric("✅ True Claims",    true_count)
    m2.metric("❌ False Claims",   false_count)
    m3.metric("⚠️ Misleading",    misleading_count)
    m4.metric("📊 Avg Confidence", f"{avg_confidence}%")

    st.divider()

    # ── SUB-CLAIMS BREAKDOWN ──
    st.subheader("📋 Claim-by-Claim Breakdown")

    for sc in sub_claims:
        v        = sc.get("verdict", "UNVERIFIABLE")
        c        = sc.get("confidence", 0)
        color    = verdict_color(v)
        emoji_v  = verdict_emoji(v)
        label    = sc["text"]
        short_label = label[:80] + ("..." if len(label) > 80 else "")

        bar_colors = {
            "TRUE":          "#1a7f37",
            "FALSE":         "#cf222e",
            "MISLEADING":    "#9a6700",
            "UNVERIFIABLE":  "#57606a",
            "DISPUTED":      "#0550ae",
        }
        bar_color = bar_colors.get(v, "#57606a")

        with st.expander(f"{emoji_v} Sub-claim {sc['id']}: {short_label}", expanded=True):
            col_v, col_c = st.columns([1, 2])
            with col_v:
                st.markdown(f"**Verdict:** :{color}[**{v}**]")
            with col_c:
                st.markdown(f"**Confidence:** {c}% — {confidence_label(c)}")
                st.markdown(f"""
                <div class="confidence-bar-container">
                  <div class="confidence-bar-fill" style="background:{bar_color}; width:{c}%;"></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"**Analysis:** {sc.get('reasoning', 'No analysis available.')}")

            src_col1, src_col2 = st.columns(2)
            with src_col1:
                supporting = sc.get("supporting_sources", [])
                if supporting:
                    st.markdown("**Supporting sources:**")
                    for s in supporting[:3]:
                        title = s.get("title", s.get("url", "Source"))[:60]
                        url   = s.get("url", "#")
                        st.markdown(f'<div class="source-card"><a href="{url}" target="_blank">{title}</a></div>',
                                    unsafe_allow_html=True)
            with src_col2:
                contradicting = sc.get("contradicting_sources", [])
                if contradicting:
                    st.markdown("**Contradicting sources:**")
                    for s in contradicting[:3]:
                        title = s.get("title", s.get("url", "Source"))[:60]
                        url   = s.get("url", "#")
                        st.markdown(f'<div class="source-card" style="border-left-color:#cf222e;"><a href="{url}" target="_blank">{title}</a></div>',
                                    unsafe_allow_html=True)

    st.divider()

    # ── FALLACIES SECTION ──
    st.subheader("🧠 Logical & Rhetorical Analysis")

    if fallacies:
        sev_hex = {"low": "#0550ae", "medium": "#9a6700", "high": "#cf222e"}
        for f in fallacies:
            sev     = f.get("severity", "low")
            color   = sev_hex.get(sev, "#57606a")
            st.markdown(
                f'<div class="fallacy-card">'
                f'<span style="color:{color}; font-weight:700;">{f["name"]}</span>'
                f' — Severity: <code style="color:{color};">{sev.upper()}</code><br>'
                f'<em>{f["description"]}</em>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("✅ No significant logical fallacies or manipulation techniques detected in this claim.")

    st.divider()

    # ── FULL REPORT ──
    st.subheader("📄 Full Fact-Check Report")

    if report:
        st.markdown(report)
        st.divider()

        dl1, dl2, _ = st.columns([1, 1, 2])
        claim_slug = (
            state.get("original_claim", "claim")[:30]
            .replace(" ", "_")
            .lower()
        )

        dl1.download_button(
            "⬇️ Download .md",
            data=report,
            file_name=f"factcheck_{claim_slug}.md",
            mime="text/markdown",
        )
        dl2.download_button(
            "⬇️ Download .txt",
            data=report,
            file_name=f"factcheck_{claim_slug}.txt",
            mime="text/plain",
        )

    st.divider()
    st.caption(
        f"Fact-checked with FactCheck AI · Overall verdict: {overall} · Credibility: {score}/100"
    )


# ── SIDEBAR ──
with st.sidebar:
    st.title("⚙️ Settings")

    iteration_limit = st.slider(
        "Max research iterations",
        min_value=1,
        max_value=3,
        value=2,
        help="Higher = more thorough but slower",
    )

    search_depth = st.selectbox(
        "Search depth",
        options=["Standard (faster)", "Advanced (thorough)"],
        index=1,
    )

    st.divider()

    with st.expander("📖 How it works"):
        st.markdown("""
1. **Deconstruct** — GPT-4o-mini breaks your claim into 3–6 atomic sub-claims
2. **Research** — Tavily searches for supporting & contradicting evidence per sub-claim
3. **Evaluate** — GPT-4o-mini assigns a verdict and confidence score to each sub-claim
4. **Deep Research** *(conditional)* — If any sub-claim confidence < 60%, the agent generates targeted queries and searches again
5. **Fallacy Detection** — GPT-4o-mini scans the original claim for logical fallacies and manipulation techniques
6. **Report Writing** — GPT-4o-mini synthesises all findings into a structured fact-check report

> If any sub-claim confidence < 60%, the agent automatically searches for more evidence (up to 2 extra rounds)
        """)

    with st.expander("🎯 Best for"):
        st.markdown("""
- 📰 News headlines
- 🏛️ Political statements
- 📱 Viral social media posts
- 🛒 Product claims
- 🔬 Scientific claims
- 📚 Historical statements
        """)

    with st.expander("⚡ Example claims"):
        examples = [
            "The Great Wall of China is visible from space",
            "Vaccines cause autism",
            "Einstein failed math as a child",
            "Humans only use 10% of their brains",
        ]
        for example in examples:
            if st.button(example, key=f"example_{example[:20]}", use_container_width=True):
                st.session_state["prefill_claim"] = example
                st.rerun()


# ── MAIN AREA ──
col_logo, col_title = st.columns([1, 8])
with col_title:
    st.title("🔍 FactCheck AI")
    st.caption("Multi-source autonomous fact verification powered by GPT-4o-mini + Tavily")

st.divider()

# Claim input — respect prefill from example buttons
claim_value: str = st.session_state.get("prefill_claim", "")

claim: str = st.text_area(
    "Enter a claim to fact-check",
    value=claim_value,
    height=100,
    placeholder="Paste any statement, headline, or claim here...",
    help="Works best with specific, factual claims. Opinions and predictions cannot be fact-checked.",
)

col_btn, col_chars, col_tip = st.columns([2, 2, 4])
with col_btn:
    run_btn = st.button("🔍 Fact Check", type="primary", use_container_width=True)
with col_chars:
    st.caption(f"{len(claim)} / 500 characters")
with col_tip:
    st.caption("💡 Tip: Specific claims check better than vague ones")

# ── ON RUN ──
if run_btn and claim.strip():
    if len(claim.strip()) < 10:
        st.error("Please enter a longer claim (at least 10 characters).")
        st.stop()

    # Clear any prefill after use
    if "prefill_claim" in st.session_state:
        del st.session_state["prefill_claim"]

    st.divider()

    initial_state: FactCheckerState = {
        "original_claim":   claim.strip(),
        "sub_claims":       [],
        "fallacies":        [],
        "overall_verdict":  None,
        "credibility_score": 0,
        "executive_summary": "",
        "final_report":     "",
        "iteration_count":  0,
        "error":            "",
    }

    accumulated_state: dict = dict(initial_state)
    deep_research_count: int = 0

    with st.status("🤖 Fact-checking in progress...", expanded=True) as status:
        try:
            for event in fact_checker_graph.stream(initial_state, stream_mode="updates"):
                node_name   = list(event.keys())[0]
                node_output = list(event.values())[0]

                # Accumulate state (avoid double-invoke)
                accumulated_state.update(node_output)

                if node_name == "deconstructor":
                    sc_list = node_output.get("sub_claims", [])
                    st.write(f"**Step 1 — Deconstructing claim** into {len(sc_list)} sub-claims:")
                    for sc in sc_list:
                        st.write(f"  `{sc['id']}.` {sc['text']}")

                elif node_name == "researcher":
                    sc_list = node_output.get("sub_claims", [])
                    total_sources = sum(
                        len(sc.get("supporting_sources", []))
                        + len(sc.get("contradicting_sources", []))
                        for sc in sc_list
                    )
                    st.write("**Step 2 — Searching** for supporting and contradicting evidence...")
                    st.write(f"  Found {total_sources} sources across all sub-claims")

                elif node_name == "evaluator":
                    sc_list = node_output.get("sub_claims", [])
                    st.write("**Step 3 — Evaluating** each sub-claim...")
                    for sc in sc_list:
                        v   = sc.get("verdict", "UNVERIFIABLE")
                        c   = sc.get("confidence", 0)
                        emj = verdict_emoji(v)
                        st.write(f"  {emj} Sub-claim {sc['id']}: **{v}** ({c}% confidence)")

                elif node_name == "deep_researcher":
                    deep_research_count += 1
                    st.write(
                        f"**Step 3b — Deep research pass #{deep_research_count}** "
                        f"— some claims need more evidence..."
                    )

                elif node_name == "fallacy_detector":
                    st.write("**Step 4 — Detecting** logical fallacies and manipulation techniques...")
                    fallacies = node_output.get("fallacies", [])
                    if fallacies:
                        st.write(f"  Found {len(fallacies)} logical issue(s)")
                    else:
                        st.write("  No significant logical issues detected")

                elif node_name == "writer":
                    st.write("**Step 5 — Writing** comprehensive fact-check report...")

            status.update(label="✅ Fact-check complete!", state="complete", expanded=False)

        except Exception as e:
            status.update(label="❌ Error occurred", state="error")
            st.error(f"Agent failed: {str(e)}")
            st.stop()

    display_results(accumulated_state)

elif run_btn and not claim.strip():
    st.warning("⚠️ Please enter a claim to fact-check.")
