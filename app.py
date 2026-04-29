import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime
import requests

# ============================================================
# Coordinates of Al-Khwarizmi College of Engineering, Baghdad
# ============================================================
LAT = 33.27047
LON = 44.37339

# ============================================================
# Page configuration
# ============================================================
st.set_page_config(
    page_title="Digital Twin System - Al-Khwarizmi College",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Custom CSS for modern UI
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    body { background-color: #f5f7fa; }
    .header-container {
        background: white;
        padding: 1.2rem 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.02);
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        border-bottom: 3px solid #1e3c72;
    }
    .card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border: 1px solid #edf2f7;
        transition: all 0.2s ease;
        margin-bottom: 1.2rem;
    }
    .metric-box {
        background: #f8fafd;
        border-radius: 16px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e9edf4;
        color: #1e2b3c;
        font-weight: 500;
    }
    .metric-box b {
        font-size: 1.5rem;
        color: #1e3c72;
        display: block;
    }
    .stButton button {
        background: white;
        color: #1e3c72;
        border: 1px solid #d0ddee;
        border-radius: 40px;
        padding: 0.4rem 2rem;
        font-weight: 600;
        transition: 0.2s;
    }
    .stButton button:hover {
        background: #f0f4fc;
        border-color: #1e3c72;
        color: #1e3c72;
    }
    .stButton button[kind="primary"] {
        background: #1e3c72;
        color: white;
        border: none;
    }
    .stButton button[kind="primary"]:hover {
        background: #2a4b8a;
    }
    .stSlider > div > div > div { background-color: #1e3c72 !important; }
    h1, h2, h3 { color: #0f263b; font-weight: 600; }
    .dataframe { border-radius: 16px; overflow: hidden; border: 1px solid #e9edf4 !important; }
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        padding: 0.4rem;
        border-radius: 50px;
        border: 1px solid #e9edf4;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 40px;
        padding: 0.4rem 1.2rem;
        color: #4a5568;
    }
    .stTabs [aria-selected="true"] {
        background: #1e3c72 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Header (English)
# ============================================================
with st.container():
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        st.image("https://upload.wikimedia.org/wikipedia/ar/thumb/8/8a/University_of_Baghdad_logo.png/200px-University_of_Baghdad_logo.png", width=70)
    with col2:
        if os.path.exists("khwarizmi_logo.jpg"):
            st.image("khwarizmi_logo.jpg", width=70)
        else:
            st.markdown("<h1 style='margin:0; color:#1e3c72;'>🏛️</h1>", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <h2 style="margin:0; color:#1e3c72;">Smart Digital Twin System</h2>
        <p style="margin:0; color:#5a6d86;">Al-Khwarizmi College of Engineering – University of Baghdad</p>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# Building data (static)
# ============================================================
buildings_data = pd.DataFrame({
    'Building': ['Administration', 'Academic Depts', 'Laboratories', 'Postgraduate', 'Workshops', 'Cafeteria'],
    'Age (years)': [30, 25, 20, 12, 10, 5],
    'Floors': [3, 3, 2, 1, 1, 1],
    'Condition': ['Good', 'Excellent', 'Excellent', 'Good', 'Good', 'Excellent']
})

# Campus coordinates
CAMPUS_LAT = LAT
CAMPUS_LON = LON
locations = [
    [CAMPUS_LAT + 0.0005, CAMPUS_LON + 0.0003],
    [CAMPUS_LAT - 0.0002, CAMPUS_LON + 0.0001],
    [CAMPUS_LAT + 0.0003, CAMPUS_LON - 0.0002],
    [CAMPUS_LAT + 0.0001, CAMPUS_LON - 0.0003],
    [CAMPUS_LAT - 0.0004, CAMPUS_LON - 0.0002],
    [CAMPUS_LAT + 0.0002, CAMPUS_LON + 0.0002]
]

# ============================================================
# Equipment optimal conditions
# ============================================================
OPTIMAL_CONDITIONS = {
    '3D Printer': {'temp': (25, 35), 'vib': (0, 0.5), 'current': (5, 15), 'pressure': (100, 120)},
    'Engineering Workstations': {'temp': (30, 50), 'vib': (0, 0.3), 'current': (2, 8), 'pressure': (80, 100)},
    'Central HVAC': {'temp': (20, 30), 'vib': (0, 0.4), 'current': (10, 20), 'pressure': (150, 200)},
    'Promethean Displays': {'temp': (20, 35), 'vib': (0, 0.2), 'current': (1, 3), 'pressure': (50, 80)}
}
equipment_list = list(OPTIMAL_CONDITIONS.keys())

# ============================================================
# Weather function using wttr.in (no API key needed)
# Returns current temperature in Celsius or None if error
# ============================================================
@st.cache_data(ttl=1800)  # cache for 30 minutes
def get_current_temperature():
    """Fetch current temperature from wttr.in for Baghdad coordinates"""
    url = f"https://wttr.in/{LAT},{LON}?format=j1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data['current_condition'][0]
        temp_c = float(current['temp_C'])
        return temp_c
    except Exception as e:
        # If weather fetch fails, return None (will use default)
        return None

# ============================================================
# Weather display function (for sidebar or right column)
# ============================================================
@st.cache_data(ttl=1800)
def get_weather_baghdad():
    """Fetch current weather details for display"""
    url = f"https://wttr.in/{LAT},{LON}?format=j1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data['current_condition'][0]
        return {
            'temp': current['temp_C'],
            'humidity': current['humidity'],
            'description': current['weatherDesc'][0]['value']
        }
    except Exception as e:
        return None

# ============================================================
# Evaluation functions
# ============================================================
def evaluate_health(temp, vib, current, pressure, age, device_type):
    opts = OPTIMAL_CONDITIONS[device_type]
    issues = 0
    severity = 0

    if temp < opts['temp'][0] or temp > opts['temp'][1]:
        issues += 1
        severity += abs(temp - (opts['temp'][0] + opts['temp'][1])/2) / 10
    if vib > opts['vib'][1]:
        issues += 1
        severity += (vib - opts['vib'][1]) * 2
    if current < opts['current'][0] or current > opts['current'][1]:
        issues += 1
        severity += abs(current - (opts['current'][0] + opts['current'][1])/2) / 5
    if pressure < opts['pressure'][0] or pressure > opts['pressure'][1]:
        issues += 1
        severity += abs(pressure - (opts['pressure'][0] + opts['pressure'][1])/2) / 20
    if age > 10:
        issues += 1
        severity += (age - 10) / 10

    if issues == 0:
        return "🟢 Normal", "green", 100
    elif issues <= 2 and severity < 2:
        return "🟡 Warning", "orange", 70
    elif issues <= 3 and severity < 4:
        return "🟠 Danger", "red", 40
    else:
        return "🔴 Critical", "darkred", 10

def get_recommendations(temp, vib, current, pressure, age, device_type):
    opts = OPTIMAL_CONDITIONS[device_type]
    rec = []
    if temp < opts['temp'][0]:
        rec.append(f"🌡️ **Low temperature** (optimal {opts['temp'][0]}-{opts['temp'][1]}°C)")
    elif temp > opts['temp'][1]:
        rec.append(f"🌡️ **High temperature** (optimal {opts['temp'][0]}-{opts['temp'][1]}°C)")
    if vib > opts['vib'][1]:
        rec.append(f"📳 **High vibration** (optimal < {opts['vib'][1]} mm/s)")
    if current < opts['current'][0]:
        rec.append(f"⚡ **Low current** (optimal {opts['current'][0]}-{opts['current'][1]} A)")
    elif current > opts['current'][1]:
        rec.append(f"⚡ **High current** (optimal {opts['current'][0]}-{opts['current'][1]} A)")
    if pressure < opts['pressure'][0]:
        rec.append(f"⏲️ **Low pressure** (optimal {opts['pressure'][0]}-{opts['pressure'][1]} psi)")
    elif pressure > opts['pressure'][1]:
        rec.append(f"⏲️ **High pressure** (optimal {opts['pressure'][0]}-{opts['pressure'][1]} psi)")
    if age > 15:
        rec.append("🔋 **Very old equipment** – consider replacement")
    elif age > 10:
        rec.append("🔋 **Moderate age** – monitor performance")
    return rec if rec else ["✅ All indicators within normal range"]

# ============================================================
# Sidebar controls
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/settings.png", width=70)
    st.markdown("## 🔧 Control Panel")
    st.markdown("---")

    selected_equipment = st.selectbox("**Select Equipment**", equipment_list)

    temp = st.slider("🌡️ Temperature (°C)", 0.0, 80.0, 30.0, 0.5)
    vib = st.slider("📳 Vibration (mm/s)", 0.0, 2.0, 0.2, 0.05)
    current = st.slider("⚡ Current (A)", 0.0, 30.0, 10.0, 0.5)
    pressure = st.slider("⏲️ Pressure (psi)", 0.0, 200.0, 110.0, 1.0)
    age = st.slider("🔋 Equipment Age (years)", 0.0, 20.0, 3.0, 0.5)

    st.markdown("---")
    mode = st.radio("Operation Mode", ["Manual", "Auto"], horizontal=True)

    if mode == "Auto":
        st.caption("Simulating equipment degradation over 10 steps based on real Baghdad temperature.")
        if st.button("▶️ Start Simulation", use_container_width=True):
            st.session_state['auto_run'] = True
            st.session_state['step'] = 0
            st.session_state['auto_equipment'] = selected_equipment
    else:
        if st.button("🔮 Evaluate Condition", type="primary", use_container_width=True):
            st.session_state['input_data'] = [temp, vib, current, pressure, age, selected_equipment]
            st.session_state['predict'] = True

    st.markdown("---")
    opts = OPTIMAL_CONDITIONS[selected_equipment]
    st.markdown(f"### 📋 Optimal conditions for {selected_equipment}")
    st.markdown(f"""
    - **Temperature**: {opts['temp'][0]}–{opts['temp'][1]} °C
    - **Vibration**: < {opts['vib'][1]} mm/s
    - **Current**: {opts['current'][0]}–{opts['current'][1]} A
    - **Pressure**: {opts['pressure'][0]}–{opts['pressure'][1]} psi
    """)

# ============================================================
# Main area: Overview KPIs
# ============================================================
st.markdown("## 📊 Overview")
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.markdown(f'<div class="metric-box"><b>4</b><span style="color:#5a6d86;">Monitored Equipment</span></div>', unsafe_allow_html=True)
with col_kpi2:
    st.markdown(f'<div class="metric-box"><b>6</b><span style="color:#5a6d86;">Buildings</span></div>', unsafe_allow_html=True)
with col_kpi3:
    count = len(st.session_state.get('history', []))
    st.markdown(f'<div class="metric-box"><b>{count}</b><span style="color:#5a6d86;">Evaluations</span></div>', unsafe_allow_html=True)
with col_kpi4:
    st.markdown(f'<div class="metric-box"><b>Active</b><span style="color:#5a6d86;">System Status</span></div>', unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# Two columns: Equipment status (left) and Map + Weather (right)
# ============================================================
col_left, col_right = st.columns([1.2, 0.8])

with col_left:
    st.markdown("## 📟 Equipment Status")
    st.markdown('<div class="card">', unsafe_allow_html=True)

    if 'predict' in st.session_state or 'auto_run' in st.session_state:
        if 'auto_run' in st.session_state and st.session_state.get('step', 0) < 10:
            step = st.session_state['step']
            # Get real Baghdad temperature for realistic degradation
            real_temp = get_current_temperature()
            if real_temp is None:
                real_temp = 35  # default fallback
            
            # Ambient factor: higher temperature accelerates degradation
            # Factor increases by 1% per degree above 20°C, max 2.0
            ambient_factor = 1 + max(0, (real_temp - 20) * 0.01)
            ambient_factor = min(ambient_factor, 2.0)
            
            # Degradation formulas based on real temperature
            temp = 25 + (real_temp * ambient_factor) * (step / 10)
            vib = 0.2 + 1.5 * (step / 10) * ambient_factor
            current = 10 + 15 * (step / 10) * ambient_factor
            pressure = 110 - 60 * (step / 10) * ambient_factor
            age = 3 + 12 * (step / 10) * ambient_factor
            
            # Apply bounds
            temp = min(temp, 80)
            vib = min(vib, 2.0)
            current = min(current, 30)
            pressure = max(pressure, 50)
            age = min(age, 20)
            
            device = st.session_state.get('auto_equipment', selected_equipment)
            st.session_state['step'] = step + 1
            if step >= 9:
                st.session_state['auto_run'] = False
                st.success("✅ Simulation completed!")
        else:
            if 'input_data' in st.session_state:
                temp, vib, current, pressure, age, device = st.session_state['input_data']
            else:
                st.info("👈 Select parameters and click Evaluate Condition")
                st.stop()

        status, color, health_score = evaluate_health(temp, vib, current, pressure, age, device)

        # Display metrics in two rows of three
        cols = st.columns(3)
        cols[0].metric("🌡️ Temperature", f"{temp:.1f} °C")
        cols[1].metric("📳 Vibration", f"{vib:.2f} mm/s")
        cols[2].metric("⚡ Current", f"{current:.1f} A")
        cols2 = st.columns(3)
        cols2[0].metric("⏲️ Pressure", f"{pressure:.1f} psi")
        cols2[1].metric("🔋 Age", f"{age:.1f} years")
        cols2[2].metric("📈 Health Score", f"{health_score:.0f}%")

        st.markdown(f"### Equipment Condition: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)

        # Gauge chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Health Index"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 25], 'color': '#ffcdd2'},
                    {'range': [25, 50], 'color': '#ffb74d'},
                    {'range': [50, 75], 'color': '#fff3b0'},
                    {'range': [75, 100], 'color': '#c8e6c9'}
                ],
                'threshold': {
                    'line': {'color': 'black', 'width': 4},
                    'thickness': 0.75,
                    'value': health_score
                }
            }
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("### 💡 Maintenance Recommendations")
        for rec in get_recommendations(temp, vib, current, pressure, age, device):
            st.markdown(f"- {rec}")

        # Save to history
        if 'history' not in st.session_state:
            st.session_state['history'] = []
        st.session_state['history'].append({
            'Time': datetime.now().strftime("%H:%M:%S"),
            'Equipment': device,
            'Status': status,
            'Score': health_score
        })
        if 'predict' in st.session_state:
            st.session_state['predict'] = False
    else:
        st.info("👈 Use the sidebar to adjust parameters and evaluate")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# Right column: Map (top) and Weather (bottom)
# ============================================================
with col_right:
    # Campus Map
    st.markdown("## 🗺️ Campus Map")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    m = folium.Map(location=[CAMPUS_LAT, CAMPUS_LON], zoom_start=17, control_scale=True)
    color_map = {'Excellent': 'green', 'Good': 'orange', 'Needs maintenance': 'red'}
    for idx, row in buildings_data.iterrows():
        color = color_map.get(row['Condition'], 'blue')
        popup = folium.Popup(f"<b>{row['Building']}</b><br>Age: {row['Age (years)']} years<br>Floors: {row['Floors']}<br>Condition: {row['Condition']}", max_width=200)
        folium.Marker(locations[idx % len(locations)], popup=popup,
                      icon=folium.Icon(color=color, icon='building', prefix='fa')).add_to(m)
    st_folium(m, width=None, height=350)
    st.markdown('</div>', unsafe_allow_html=True)

    # Weather Section (below the map)
    st.markdown("## 🌦️ Current Weather in Baghdad")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    weather = get_weather_baghdad()
    if weather:
        st.markdown(f"**Temperature**: {weather['temp']}°C")
        st.markdown(f"**Condition**: {weather['description']}")
        st.markdown(f"**Humidity**: {weather['humidity']}%")
    else:
        st.info("Weather data temporarily unavailable.")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# Bottom tabs: Analytics
# ============================================================
st.markdown("---")
st.markdown("## 📈 Analytics & Statistics")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Evaluation Log", "📊 Optimal Conditions", "📉 Health Trend", "📊 Factor Deviation"])

with tab1:
    if st.session_state.get('history'):
        df_hist = pd.DataFrame(st.session_state['history'][-20:])
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("No history yet")
    if st.button("🧹 Clear Log"):
        st.session_state['history'] = []
        st.rerun()

with tab2:
    opt_df = pd.DataFrame([
        {'Equipment': d,
         'Optimal Temp (°C)': f"{opts['temp'][0]}-{opts['temp'][1]}",
         'Max Vibration (mm/s)': f"< {opts['vib'][1]}",
         'Optimal Current (A)': f"{opts['current'][0]}-{opts['current'][1]}",
         'Optimal Pressure (psi)': f"{opts['pressure'][0]}-{opts['pressure'][1]}"}
        for d, opts in OPTIMAL_CONDITIONS.items()
    ])
    st.dataframe(opt_df, use_container_width=True)

with tab3:
    if st.session_state.get('history'):
        df = pd.DataFrame(st.session_state['history'])
        fig = px.line(df, x=range(len(df)), y='Score', title="Health Index Over Time", markers=True)
        fig.update_layout(xaxis_title="Evaluation #", yaxis_title="Health Score")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data")

with tab4:
    if 'input_data' in st.session_state:
        t, v, c, p, a, dev = st.session_state['input_data']
        opts = OPTIMAL_CONDITIONS[dev]
        ideal_mid = [(opts['temp'][0]+opts['temp'][1])/2, opts['vib'][1]/2,
                     (opts['current'][0]+opts['current'][1])/2,
                     (opts['pressure'][0]+opts['pressure'][1])/2, 5]
        values = [t, v, c, p, a]
        factors = ['Temperature', 'Vibration', 'Current', 'Pressure', 'Age']
        deviation = [abs(vals - mid)/mid if mid != 0 else 0 for vals, mid in zip(values, ideal_mid)]
        fig = px.bar(x=factors, y=deviation, title="Relative Deviation from Optimal Values",
                     color=deviation, color_continuous_scale='Reds')
        fig.update_layout(yaxis_title="Deviation")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Evaluate an equipment first")

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; background: white; padding: 1.2rem; border-radius: 20px; border: 1px solid #e9edf4;">
    <p style="margin:0; color:#1e3c72;">🏛️ Digital Twin Project – Al-Khwarizmi College of Engineering, University of Baghdad</p>
    <p style="margin:0; color:#5a6d86;">Prepared by: <b>Mariam Mohsen</b> | Supervised by: Dr. <b>Wisam Thamer</b></p>
    <p style="margin:0; color:#5a6d86;">Department: <b>Master of Advanced Manufacturing Processes Engineering</b> | 2026</p>
</div>
""", unsafe_allow_html=True)
