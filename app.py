import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from engine.configs import HardwareConfig, FacilityConfig, MarketConfig
from engine.core import MiningFinancialModel
from engine.market import MarketCalibrator

st.set_page_config(page_title="CG Model | Digdefi", layout="wide", page_icon="assets/img/logo1.png")
    
HARDWARE_LIBRARY = {
    "Bitmain Antminer S23 Hyd 3U (SHA-256)": {"th": 1160.0, "w": 11020, "cost": 7755},
    "Bitdeer SealMiner A4 Ultra Hydro (SHA-256)": {"th": 886.0, "w": 8372, "cost": 9966},
    "Bitmain Antminer S23e Hyd 2U (SHA-256)": {"th": 865.0, "w": 8650, "cost": 11699},
    "Bitmain Antminer S23 Hyd (SHA-256)": {"th": 580.0, "w": 5510, "cost": 11979},
    "Bitdeer SealMiner A4 Pro Hydro (SHA-256)": {"th": 680.0, "w": 7412, "cost": 8662},
    "Bitmain Antminer S21 XP+ Hyd (SHA-256)": {"th": 500.0, "w": 5500, "cost": 2699},
    "Bitdeer SealMiner A3 Pro Hydro (SHA-256)": {"th": 660.0, "w": 8250, "cost": 6988},
    "Bitmain Antminer S21e XP Hyd 3U (SHA-256)": {"th": 860.0, "w": 11180, "cost": 5139},
    "Bitmain Antminer S21j XP Hyd (SHA-256)": {"th": 495.0, "w": 5940, "cost": 6069},
    "Bitdeer SealMiner A4 Pro Air (SHA-256)": {"th": 336.0, "w": 3662, "cost": 3373},
    "Bitmain Antminer S21 XP Hyd (SHA-256)": {"th": 473.0, "w": 5676, "cost": 1042},
    "Bitmain Antminer S23 (SHA-256)": {"th": 318.0, "w": 3498, "cost": 4950},
    "Bitmain Antminer S23 Imm. (SHA-256)": {"th": 442.0, "w": 5304, "cost": 7880},
    "MicroBT WhatsMiner M7DS (SHA-256)": {"th": 680.0, "w": 9200, "cost": 7859},
    "Bitmain Antminer S21e XP Hyd (SHA-256)": {"th": 430.0, "w": 5590, "cost": 2699},
    "MicroBT WhatsMiner M73S+ (SHA-256)": {"th": 540.0, "w": 7200, "cost": 7909},
    "Bitdeer SealMiner A3 Pro Air (SHA-256)": {"th": 290.0, "w": 3625, "cost": 4449},
    "Bitdeer SealMiner A3 Hydro (SHA-256)": {"th": 500.0, "w": 6750, "cost": 6076},
    "Canaan Avalon A16XP-300T (SHA-256)": {"th": 300.0, "w": 3850, "cost": 4199},
    "MicroBT WhatsMiner M76S+ (SHA-256)": {"th": 390.0, "w": 5200, "cost": 4875},
}

st.logo("assets/img/logo2.png", size="large")
with st.sidebar:
    st.header("Hardware Config")
    selected_model = st.selectbox("ASIC Model", list(HARDWARE_LIBRARY.keys()) + ["Custom"])
    
    if selected_model == "Custom":
        h_th = st.number_input("Hashrate (TH/s)", value=120.0)
        p_w = st.number_input("Power (W)", value=3000.0)
        c_usd = st.number_input("Unit Cost ($)", value=2000.0)
    else:
        data = HARDWARE_LIBRARY[selected_model]
        h_th = data['th']
        p_w = data['w']
        c_usd = st.number_input("Unit Cost ($)", value=float(data['cost']), step=100.0)

    hw = HardwareConfig(hashrate_th=h_th, power_w=p_w, cost_usd=c_usd)

    st.header("Facility Specs")
    fac = FacilityConfig(
        max_power_mw=st.slider("Max Power Cap (MW)", 1.0, 20.0, 20.0),
        pue=st.slider("PUE", 1.0, 1.2, 1.03),
        energy_price_kwh=st.number_input("Energy Price ($/kWh)", value=0.025, format="%.3f"),
        infra_markup_pct=0.15,
        monthly_maintenance_usd=st.number_input("Fixed O&M ($/mo)", value=15000.0)
    )

with st.container():
    st.subheader(f"Current Scenario: {selected_model}")
    hc1, hc2, hc3, hc4 = st.columns(4)
    hc1.metric("Hashrate", f"{h_th:,.0f} TH/s")
    hc2.metric("Power", f"{p_w:,.0f} W")
    hc3.metric("Efficiency", f"{(p_w/h_th):.1f} J/TH")
    hc4.metric("Capital Expense", f"${c_usd:,.0f} per unit")
    st.divider()
    
st.subheader("Calibration & Inputs")
col1, col2, col3 = st.columns(3)

with col1:
    api_toggle = st.toggle("Fetch live hashprice via Braiins API", value=False)
    if api_toggle:
        live_hp = MarketCalibrator.get_live_hashprice()
        if live_hp:
            st.success(f"Live API Active: ${live_hp:.2f} / PH / day")
            h0 = live_hp
        else:
            st.error("Live API offline. Reverting to manual input.")
            h0 = st.number_input("Initial Hashprice ($/PH/day)", value=60.0)
    else:
        h0 = st.number_input("Initial Hashprice ($/PH/day)", value=60.0)
        
    horizon = st.slider("Horizon (Months)", 6, 60, 24)

with col2:
    diff_growth = st.slider("Annual Difficulty Growth (%)", 0, 100, 25) / 100
    wacc = st.slider("WACC (%)", 5, 25, 12) / 100

with col3:
    use_cal = st.toggle("Calibrate Volatility via yfinance", value=True)
    n_paths = st.number_input("Monte Carlo Paths", value=5000, step=1000)

@st.cache_data(show_spinner=False)
def get_market_params(h0, diff, wacc, horizon, paths, calibrate):
    if calibrate:
        try:
            config = MarketCalibrator.calibrate_from_btc(difficulty_growth_rate=diff, initial_hashprice=h0)
        except Exception:
            config = MarketConfig(h0, -diff, 0.7, horizon, wacc, paths)
    else:
        config = MarketConfig(h0, -diff, 0.7, horizon, wacc, paths)
    return MarketConfig(h0, config.drift, config.volatility, horizon, wacc, paths)

@st.cache_data(show_spinner=False)
def fetch_historical_btc():
    try:
        df = yf.download("BTC-USD", period="1y", interval="1d", progress=False)
        return df['Close'].squeeze().dropna()
    except Exception:
        return pd.Series()

m_config = get_market_params(h0, diff_growth, wacc, horizon, n_paths, use_cal)
btc_history = fetch_historical_btc()

tmy_data = np.random.beta(2, 5, 8760) * fac.max_power_mw * 1.2 
model = MiningFinancialModel(hw, fac, m_config)
results = model.run_monte_carlo(tmy_data)

st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Median NPV", f"${results['npv_median']:,.0f}")
m2.metric("Prob. NPV > 0", f"{results['prob_positive_npv']:.1%}")
m3.metric("Fleet Size", f"{results['fleet_size_units']:,} Units")
m4.metric("Rev/kWh", f"${model.revenue_per_kwh(h0):.4f}")

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"colspan": 2, "secondary_y": True}, None],
           [{}, {}]],
    subplot_titles=(
        "BTC vs. Revenue/kWh",
        "Cumulative Free Cash Flow (100 Paths)",
        "NPV Probability Distribution"
    ),
    vertical_spacing=0.15
)

if not btc_history.empty:
    btc_dates = btc_history.index
    btc_vals = btc_history.values
    baseline_btc = btc_vals[0]
    implied_hp = h0 * (btc_vals / baseline_btc)
    implied_rev_kwh = model.revenue_per_kwh(implied_hp)

    fig.add_trace(go.Scatter(x=btc_dates, y=btc_vals, mode='lines', line=dict(color='#f7931a'), name='BTC Price (USD)'), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=btc_dates, y=implied_rev_kwh, mode='lines', line=dict(color='#00CC96', dash='dot'), name='Implied Rev/kWh ($)'), row=1, col=1, secondary_y=True)
    fig.add_hline(y=fac.energy_price_kwh, line_dash="dash", line_color="red", annotation_text="Energy Cost Basis", row=1, col=1, secondary_y=True)

    fig.update_yaxes(title_text="BTC Price ($)", secondary_y=False, row=1, col=1)
    fig.update_yaxes(title_text="Revenue per kWh ($)", secondary_y=True, row=1, col=1)

cum_cf = np.cumsum(results['raw_cash_flows'], axis=0)
for i in range(min(100, n_paths)):
    fig.add_trace(go.Scatter(y=cum_cf[:, i], mode='lines', line=dict(color='orange', width=1), opacity=0.05, showlegend=False), row=2, col=1)
fig.add_trace(go.Scatter(y=np.median(cum_cf, axis=1), mode='lines', line=dict(color='green', width=3), name='Median CF'), row=2, col=1)

npv_totals = results['raw_cash_flows'].sum(axis=0)
fig.add_trace(go.Histogram(x=npv_totals, nbinsx=50, marker_color='#2ecc71', name='NPV Freq'), row=2, col=2)
fig.add_vline(x=0, line_dash="dash", line_color="red", row=2, col=2)

fig.update_layout(height=800, showlegend=False, template="plotly_dark", hovermode="x unified")
st.plotly_chart(fig, width='stretch')