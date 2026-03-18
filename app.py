import streamlit as st
from claim_analyzer import analyze_claim
from scoring import calculate_priority
from sample_claims import SAMPLE_CLAIMS

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Claims Copilot", page_icon="📋", layout="wide")

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .section-header {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888;
        margin-bottom: 0.25rem;
    }
    .priority-score {
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1;
    }
    .comparison-box {
        background-color: #1e1e2e;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
    }
    .tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .divider { margin: 1.2rem 0; border-top: 1px solid #2e2e2e; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "claims" not in st.session_state:
    st.session_state.claims = [
        {**c, "status": "Pending", "analysis": None, "scoring": None}
        for c in SAMPLE_CLAIMS
    ]
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_claim(claim_id):
    return next((c for c in st.session_state.claims if c["id"] == claim_id), None)

def update_claim(claim_id, updates):
    for i, c in enumerate(st.session_state.claims):
        if c["id"] == claim_id:
            st.session_state.claims[i].update(updates)
            break

def score_icon(score):
    if score is None: return "⚪"
    if score >= 80: return "🔴"
    if score >= 50: return "🟡"
    return "🟢"

def risk_label(level):
    mapping = {"low": "🟢 Low", "medium": "🟡 Medium", "high": "🔴 High"}
    return mapping.get(str(level).lower(), level)

def status_icon(status):
    return {"Pending": "⏳", "In Review": "🔍", "Processed": "✅"}.get(status, "")

# ── Auto-analyze on first load ─────────────────────────────────────────────────
if not all(c["analysis"] for c in st.session_state.claims):
    progress = st.progress(0, text="Running AI analysis on all claims...")
    total = len(st.session_state.claims)
    for i, claim in enumerate(st.session_state.claims):
        if not claim["analysis"]:
            analysis = analyze_claim(claim["description"])
            scoring = calculate_priority(analysis)
            update_claim(claim["id"], {"analysis": analysis, "scoring": scoring})
        progress.progress((i + 1) / total, text=f"Analyzing claim {i + 1} of {total}...")
    progress.empty()
    st.rerun()

sorted_claims = sorted(
    st.session_state.claims,
    key=lambda c: c["scoring"]["priority_score"] if c["scoring"] else 0,
    reverse=True,
)

# ── Metrics ────────────────────────────────────────────────────────────────────
total_claims = len(st.session_state.claims)
high_priority = sum(1 for c in st.session_state.claims if c["scoring"] and c["scoring"]["priority_score"] >= 80)
in_review = sum(1 for c in st.session_state.claims if c["status"] == "In Review")
processed = sum(1 for c in st.session_state.claims if c["status"] == "Processed")

total_time_saved = sum(
    (c["analysis"].get("estimated_manual_time_min", 0) - c["analysis"].get("estimated_ai_time_min", 0))
    for c in st.session_state.claims if c["analysis"]
)
avg_time_saved = round(total_time_saved / total_claims, 1) if total_claims else 0

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📋 AI Claims Processing Copilot")
st.caption("Intelligent triage and decision support for insurance operations")
st.markdown("---")

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total Claims", total_claims)
m2.metric("High Priority", f"🔴 {high_priority}")
m3.metric("In Review", f"🔍 {in_review}")
m4.metric("Processed", f"✅ {processed}")
m5.metric("Avg Time Saved", f"{avg_time_saved} min")
m6.metric("Total Time Saved Today", f"{total_time_saved} min")

st.markdown("---")

# ── Main layout ────────────────────────────────────────────────────────────────
left, right = st.columns([2, 3], gap="large")

# ── LEFT — Claim list ──────────────────────────────────────────────────────────
with left:
    st.markdown('<div class="section-header">Claims Queue — Sorted by Priority</div>', unsafe_allow_html=True)
    st.markdown(" ")

    st.markdown("**🔺 Top Priority Cases**")
    for claim in sorted_claims[:3]:
        s = claim["scoring"]
        score = s["priority_score"] if s else 0
        label = f"{score_icon(score)} **{claim['id']}** · {score}/100 · {status_icon(claim['status'])} {claim['status']}"
        if st.button(label, key=f"top_{claim['id']}", use_container_width=True):
            st.session_state.selected_id = claim["id"]

    st.markdown(" ")
    st.markdown("**All Claims**")
    for claim in sorted_claims[3:]:
        s = claim["scoring"]
        score = s["priority_score"] if s else 0
        label = f"{score_icon(score)} **{claim['id']}** · {score}/100 · {status_icon(claim['status'])} {claim['status']}"
        if st.button(label, key=f"list_{claim['id']}", use_container_width=True):
            st.session_state.selected_id = claim["id"]

# ── RIGHT — Detail panel ───────────────────────────────────────────────────────
with right:
    selected = get_claim(st.session_state.selected_id)

    if not selected:
        st.info("👈 Select a claim from the queue to view the full analysis.")
        st.stop()

    a = selected["analysis"]
    s = selected["scoring"]
    score = s["priority_score"]
    manual_time = a.get("estimated_manual_time_min", 10)
    ai_time = a.get("estimated_ai_time_min", 3)
    time_saved = manual_time - ai_time

    # ── 1. Claim Overview ──────────────────────────────────────────────────────
    st.markdown(f"### {selected['id']} — Claim Overview")
    st.markdown(f"**Description:** {selected['description']}")
    st.markdown(f"**Status:** {status_icon(selected['status'])} `{selected['status']}`")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── 2. Risk & Priority ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Risk & Priority Assessment</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Claim Type", a.get("claim_type", "N/A"))
    c2.metric("Urgency Level", a.get("urgency_level", "N/A").capitalize())
    c3.metric("Injury Reported", a.get("injury_present", "no").capitalize())
    c4.metric("Fraud Risk Assessment", risk_label(a.get("fraud_risk", "N/A")))

    st.markdown(" ")
    st.markdown(f'<div class="priority-score">{score_icon(score)} {score}<span style="font-size:1rem;font-weight:400;color:#aaa;"> / 100 — {s["recommendation"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f"**Damage:** {a.get('damage_description', 'N/A')}")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── 3. Fraud Indicators ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Fraud Indicators</div>', unsafe_allow_html=True)
    indicators = a.get("fraud_indicators", [])
    if indicators:
        for item in indicators:
            st.warning(f"⚠ {item}")
    else:
        st.success("✔ No fraud signals detected")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── 4. Why This Claim Is Prioritized ──────────────────────────────────────
    st.markdown('<div class="section-header">Why This Claim Is Prioritized</div>', unsafe_allow_html=True)
    reasoning = a.get("priority_reasoning", [])
    if reasoning:
        for point in reasoning:
            st.markdown(f"- {point}")
    else:
        st.markdown("_No reasoning available._")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── 5. Recommended Actions ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">Recommended Actions</div>', unsafe_allow_html=True)
    actions = a.get("recommended_actions", [])
    if actions:
        for action in actions:
            st.checkbox(action, key=f"action_{selected['id']}_{action[:20]}")
    else:
        st.markdown("_No actions available._")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── 6. Efficiency Impact ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">Efficiency Impact</div>', unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    e1.metric("Manual Review", f"{manual_time} min")
    e2.metric("AI-Assisted Review", f"{ai_time} min")
    e3.metric("Time Saved", f"{time_saved} min", delta=f"-{time_saved} min")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── 7. Without AI vs With AI ───────────────────────────────────────────────
    st.markdown('<div class="section-header">Without AI vs. With AI</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.error("**❌ Without AI**\n\n- Claims reviewed sequentially\n- Priority determined manually\n- Fraud signals often missed\n- High adjuster workload")
    with col_b:
        st.success("**✅ With AI**\n\n- Instant triage on submission\n- Automatic priority ranking\n- Early fraud detection\n- Adjusters focus on high-impact cases")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── 8. Workflow Actions ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Workflow Actions</div>', unsafe_allow_html=True)
    w1, w2 = st.columns(2)
    with w1:
        if selected["status"] == "Pending":
            if st.button("▶ Start Review", use_container_width=True):
                update_claim(selected["id"], {"status": "In Review"})
                st.rerun()
    with w2:
        if selected["status"] == "In Review":
            if st.button("✔ Mark as Processed", use_container_width=True, type="primary"):
                update_claim(selected["id"], {"status": "Processed"})
                st.rerun()

    st.markdown("---")
    st.caption("This system dynamically prioritizes claims and assists adjusters in focusing on high-impact cases first. All AI outputs are advisory and require human review.")