import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# ============================================================
# NAVIFUSION REVIEW DASHBOARD
# ============================================================

st.set_page_config(
    page_title="NaviFusion Command Console",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CSV_PATH = os.path.expanduser(
    "~/navifusion_ws/live_telemetry.csv"
)

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.main {
    background: #080b12;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

h1 {
    letter-spacing: -1px;
}

.metric-card {
    background: linear-gradient(145deg, #111722, #0b0f17);
    border: 1px solid #252d3a;
    border-radius: 14px;
    padding: 18px;
    min-height: 125px;
}

.metric-label {
    color: #8d98aa;
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.metric-value {
    color: #f4f7fb;
    font-size: 2rem;
    font-weight: 700;
    margin-top: 8px;
}

.metric-sub {
    color: #8d98aa;
    font-size: 0.8rem;
    margin-top: 5px;
}

.status-good {
    color: #4ade80;
}

.status-warning {
    color: #facc15;
}

.status-danger {
    color: #fb7185;
}

.status-critical {
    color: #ff4d6d;
}

.section-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-top: 15px;
    margin-bottom: 8px;
}

.event-box {
    background: #111722;
    border: 1px solid #252d3a;
    border-radius: 12px;
    padding: 18px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD TELEMETRY
# ============================================================

@st.cache_data(ttl=1)
def load_data():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()

    try:
        df = pd.read_csv(CSV_PATH)

        if len(df) == 0:
            return df

        numeric_cols = [
            "timestamp",
            "ekf_x",
            "ekf_y",
            "imu_x",
            "imu_y",
            "drift_error",
            "gnss_mahalanobis",
            "anomaly_count",
            "navigation_confidence",
            "intelligence_score"
        ]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

        return df

    except Exception:
        return pd.DataFrame()


df = load_data()

# ============================================================
# HEADER
# ============================================================

st.title("🛰️ NaviFusion Command Console")

st.markdown(
    "**GNSS-Independent Navigation & Intelligent Threat Detection**"
)

st.caption(
    "Adaptive EKF • GNSS anomaly detection • dead reckoning • navigation intelligence"
)

if df.empty:

    st.warning(
        "Waiting for telemetry... Start the NaviFusion EKF node."
    )

    st.code(
        "ros2 node list\n"
        "ros2 node info /navifusion_ekf_node"
    )

    time.sleep(2)
    st.rerun()


# ============================================================
# LATEST DATA
# ============================================================

latest = df.iloc[-1]

gnss_status = str(latest.get("gnss_status", "UNKNOWN"))
navigation_state = str(
    latest.get("navigation_state", "UNKNOWN")
)
threat = str(
    latest.get("threat_level", "UNKNOWN")
)
mode = str(
    latest.get("navigation_mode", "UNKNOWN")
    if "navigation_mode" in df.columns
    else navigation_state
)

confidence = float(
    latest.get("navigation_confidence", 0)
)

intelligence = float(
    latest.get("intelligence_score", 0)
)

drift = float(
    latest.get("drift_error", 0)
)

mahal = float(
    latest.get("gnss_mahalanobis", 0)
)

anomalies = int(
    latest.get("anomaly_count", 0)
)

action = str(
    latest.get("recommended_action", "N/A")
)

decision = str(
    latest.get("gnss_decision", "N/A")
)

reason = str(
    latest.get("navigation_reason", "N/A")
)

ekf_x = float(latest.get("ekf_x", 0))
ekf_y = float(latest.get("ekf_y", 0))


# ============================================================
# SYSTEM STATUS BANNER
# ============================================================

if threat == "CRITICAL":
    banner = "🔴 CRITICAL — NAVIGATION THREAT DETECTED"
    banner_class = "status-critical"
elif threat == "HIGH":
    banner = "🟠 HIGH — NAVIGATION DEGRADED"
    banner_class = "status-danger"
elif threat == "MEDIUM":
    banner = "🟡 MEDIUM — GNSS UNDER MONITORING"
    banner_class = "status-warning"
else:
    banner = "🟢 NORMAL — NAVIGATION SYSTEM HEALTHY"
    banner_class = "status-good"

st.markdown(
    f"""
    <div style="
        padding:14px 18px;
        border-radius:12px;
        border:1px solid #252d3a;
        background:#0d121b;
        margin-bottom:18px;
        font-weight:700;
        font-size:1.05rem;
    ">
        <span class="{banner_class}">{banner}</span>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# KPI CARDS
# ============================================================

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">GNSS Status</div>
            <div class="metric-value status-good">
                {gnss_status}
            </div>
            <div class="metric-sub">
                Decision: {decision}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    threat_class = (
        "status-critical"
        if threat == "CRITICAL"
        else "status-danger"
        if threat == "HIGH"
        else "status-warning"
        if threat == "MEDIUM"
        else "status-good"
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Threat Level</div>
            <div class="metric-value {threat_class}">
                {threat}
            </div>
            <div class="metric-sub">
                Anomalies: {anomalies}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Navigation Confidence</div>
            <div class="metric-value">
                {confidence:.1f}%
            </div>
            <div class="metric-sub">
                Intelligence risk: {intelligence:.1f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">GNSS Integrity</div>
            <div class="metric-value">
                {100-intelligence:.1f}%
            </div>
            <div class="metric-sub">
                Mahalanobis: {mahal:.2f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Navigation Mode</div>
            <div class="metric-value" style="font-size:1.35rem;">
                {mode}
            </div>
            <div class="metric-sub">
                Drift: {drift:.2f} m
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# POSITION
# ============================================================

st.markdown(
    '<div class="section-title">📍 Current Navigation State</div>',
    unsafe_allow_html=True
)

p1, p2, p3 = st.columns(3)

with p1:
    st.metric(
        "EKF Position",
        f"({ekf_x:.2f}, {ekf_y:.2f}) m"
    )

with p2:
    st.metric(
        "Position Drift",
        f"{drift:.2f} m"
    )

with p3:
    st.metric(
        "Recommended Action",
        action
    )


# ============================================================
# TRAJECTORY + DRIFT
# ============================================================

left, right = st.columns([1.6, 1])

with left:

    st.markdown(
        '<div class="section-title">🗺️ Real-Time Robot Trajectory</div>',
        unsafe_allow_html=True
    )

    trajectory = df[
        ["ekf_x", "ekf_y", "imu_x", "imu_y"]
    ].dropna()

    if len(trajectory) > 500:
        trajectory = trajectory.tail(500)

    chart_df = pd.DataFrame({
        "EKF X": trajectory["ekf_x"].values,
        "EKF Y": trajectory["ekf_y"].values,
        "IMU X": trajectory["imu_x"].values,
        "IMU Y": trajectory["imu_y"].values
    })

    # Streamlit line chart gives us a clean live trend.
    st.line_chart(
        chart_df,
        height=390
    )

    st.caption(
        "EKF trajectory should remain bounded relative to inertial dead reckoning."
    )


with right:

    st.markdown(
        '<div class="section-title">📈 Drift Error</div>',
        unsafe_allow_html=True
    )

    drift_df = df[
        ["drift_error"]
    ].dropna()

    if len(drift_df) > 500:
        drift_df = drift_df.tail(500)

    st.line_chart(
        drift_df,
        height=390
    )

    st.metric(
        "Current Drift",
        f"{drift:.2f} m"
    )


# ============================================================
# GNSS ANOMALY DETECTION
# ============================================================

st.markdown(
    '<div class="section-title">🛡️ GNSS Integrity Monitor</div>',
    unsafe_allow_html=True
)

a1, a2 = st.columns([1.4, 1])

with a1:

    st.markdown("**Mahalanobis Innovation Distance**")

    mahal_df = df[
        ["gnss_mahalanobis"]
    ].dropna()

    if len(mahal_df) > 500:
        mahal_df = mahal_df.tail(500)

    st.line_chart(
        mahal_df,
        height=300
    )

    st.caption(
        "Thresholds: 9.21 = degraded • 50 = severe anomaly"
    )

with a2:

    st.markdown(
        """
        <div class="event-box">
        <b>Detection Logic</b><br><br>
        EKF predicts the vehicle position.<br>
        GNSS reports a position.<br><br>
        The system calculates the statistical innovation
        distance between them.<br><br>
        If the measurement is inconsistent, GNSS is rejected
        instead of contaminating the fused navigation estimate.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.metric(
        "Current Mahalanobis",
        f"{mahal:.2f}"
    )

    st.metric(
        "Rejected / Anomalous Samples",
        anomalies
    )


# ============================================================
# INTELLIGENCE ENGINE
# ============================================================

st.markdown(
    '<div class="section-title">🧠 Navigation Intelligence</div>',
    unsafe_allow_html=True
)

i1, i2, i3 = st.columns(3)

with i1:

    st.markdown(
        f"""
        <div class="event-box">
        <b>Current State</b><br><br>
        {navigation_state}<br><br>
        <span style="color:#8d98aa;">
        {reason}
        </span>
        </div>
        """,
        unsafe_allow_html=True
    )

with i2:

    st.markdown(
        f"""
        <div class="event-box">
        <b>System Decision</b><br><br>
        Threat: <b>{threat}</b><br>
        Decision: <b>{decision}</b><br>
        Action: <b>{action}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

with i3:

    st.markdown(
        f"""
        <div class="event-box">
        <b>Why This Matters</b><br><br>
        NaviFusion does not blindly trust GNSS.
        It continuously evaluates GNSS consistency and
        dynamically decides whether to fuse, monitor,
        or reject the signal.
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# INTELLIGENCE SCORE
# ============================================================

st.markdown(
    '<div class="section-title">⚠️ Navigation Risk Score</div>',
    unsafe_allow_html=True
)

score_df = df[
    ["intelligence_score", "navigation_confidence"]
].dropna()

if len(score_df) > 500:
    score_df = score_df.tail(500)

st.line_chart(
    score_df,
    height=260
)


# ============================================================
# RECENT TELEMETRY
# ============================================================

st.markdown(
    '<div class="section-title">📡 Latest Telemetry</div>',
    unsafe_allow_html=True
)

display_cols = [
    "timestamp",
    "ekf_x",
    "ekf_y",
    "imu_x",
    "imu_y",
    "drift_error",
    "gnss_mahalanobis",
    "gnss_decision",
    "navigation_state",
    "threat_level",
    "navigation_confidence",
    "recommended_action",
    "intelligence_score"
]

display_cols = [
    c for c in display_cols
    if c in df.columns
]

recent = df[display_cols].tail(12).copy()

if "timestamp" in recent.columns:
    recent["timestamp"] = recent["timestamp"].round(2)

st.dataframe(
    recent,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    f"NaviFusion • Adaptive EKF Navigation Intelligence • "
    f"{len(df):,} telemetry samples • Live telemetry source: live_telemetry.csv"
)

# ============================================================
# AUTO REFRESH
# ============================================================

time.sleep(2)
st.rerun()

