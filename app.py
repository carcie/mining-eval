import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from engine.configs import HardwareConfig, FacilityConfig, MarketConfig
from engine.core import MiningFinancialModel
from engine.market import MarketCalibrator

st.set_page_config(page_title="BTM Financial Model", layout="wide")

HARDWARE_LIBRARY = {
    "Bitmain Antminer S23 Hyd 3U (SHA-256)": {"th": 1160.0, "w": 11020, "cost": 7760},
    "Bitdeer SealMiner A4 Ultra Hydro (SHA-256)": {"th": 886.0, "w": 8372, "cost": 9983},
    "Bitmain Antminer S23e Hyd 2U (SHA-256)": {"th": 865.0, "w": 8650, "cost": 11699},
    "Bitmain Antminer S21e XP Hyd 3U (SHA-256)": {"th": 860.0, "w": 11180, "cost": 5140},
    "Bitdeer SealMiner A4 Pro Hydro (SHA-256)": {"th": 680.0, "w": 7412, "cost": 8666},
    "Bitdeer SealMiner A3 Pro Hydro (SHA-256)": {"th": 660.0, "w": 8250, "cost": 6995},
    "Bitmain Antminer S23 Hyd (SHA-256)": {"th": 580.0, "w": 5510, "cost": 11980},
    "Bitmain Antminer S21 XP+ Hyd (SHA-256)": {"th": 500.0, "w": 5500, "cost": 2700},
    "Bitmain Antminer S21j XP Hyd (SHA-256)": {"th": 495.0, "w": 5940, "cost": 6070},
    "Bitmain Antminer L11 Hyd 2U (Scrypt)": {"th": 0.035, "w": 5775, "cost": 9000},
    "Bitmain Antminer L11 Hyd 6U (Scrypt)": {"th": 0.033, "w": 5676, "cost": 9627},
    "Bitdeer SealMiner DL1 Air (Scrypt)": {"th": 0.025, "w": 3725, "cost": 8000},
    "Pinecone Matches INIBOX Pro (VersaHash)": {"th": 0.0024, "w": 1280, "cost": 7046},
    "IceRiver ALEO AE3 (zkSNARK)": {"th": 0.002, "w": 3400, "cost": 4863},
    "Pinecone Matches INIBOX (VersaHash)": {"th": 0.00085, "w": 500, "cost": 1964},
    "Bitmain Antminer X9 (RandomX)": {"th": 0.000001, "w": 2472, "cost": 5363},
    "Bitmain Antminer Z15 Pro (Equihash)": {"th": 0.00000084, "w": 2780, "cost": 950},
    "Bitmain Antminer Z15 (Equihash)": {"th": 0.00000042, "w": 1510, "cost": 812},
    "Innosilicon A9++ ZMaster (Equihash)": {"th": 0.00000014, "w": 1550, "cost": 0},
    "Bitmain Antminer Z11 (Equihash)": {"th": 0.000000135, "w": 1418, "cost": 266},
}

with st.sidebar:
    st.header("Hardware Config")
    selected_model = st.selectbox("ASIC Model", list(HARDWARE_LIBRARY.keys()) + ["Custom"])
    
    if selected_model == "Custom":
        h_th = st.number_input("Hashrate (TH/s)", value=120.0)
        p_w = st.number_input("Power (W)", value=3000.0)
        c_usd = st.number_input("Unit Cost ($)", value=2000.0)
    else:
        data = HARDWARE_LIBRARY[selected_model]
        st.info(f"Specs: {data['th']} TH/s | {data['w']} W")
        h_th = data['th']
        p_w = data['w']
        c_usd = st.number_input("Unit Cost ($)", value=float(data['cost']), step=100.0)

    hw = HardwareConfig(hashrate_th=h_th, power_w=p_w, cost_usd=c_usd)

    st.header("Facility Specs")
    fac = FacilityConfig(
        max_power_mw=st.slider("Max Power Cap (MW)", 1.0, 20.0, 20.0),
        pue=st.slider("PUE", 1.0, 1.2, 1.03),
        energy_price_kwh=st.number_input("Energy Price ($/kWh)", value=0.045, format="%.3f"),
        infra_markup_pct=0.15,
        monthly_maintenance_usd=st.number_input("Fixed O&M ($/mo)", value=5000.0)
    )

st.subheader("Market Calibration & Stochastic Inputs")
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
m2.metric("Prob. of Profit (NPV > 0)", f"{results['prob_positive_npv']:.1%}")
m3.metric("Required Fleet Size", f"{results['fleet_size_units']:,} Units")
m4.metric("Rev/kWh (Current)", f"${model.revenue_per_kwh(h0):.4f}")

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"colspan": 2, "secondary_y": True}, None],
           [{}, {}]],
    subplot_titles=(
        "Historical BTC Price vs. Revenue/kWh",
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
    fig.add_trace(go.Scatter(y=cum_cf[:, i], mode='lines', line=dict(color='#3498db', width=1), opacity=0.05, showlegend=False), row=2, col=1)
fig.add_trace(go.Scatter(y=np.median(cum_cf, axis=1), mode='lines', line=dict(color='white', width=3), name='Median CF'), row=2, col=1)

npv_totals = results['raw_cash_flows'].sum(axis=0)
fig.add_trace(go.Histogram(x=npv_totals, nbinsx=50, marker_color='#2ecc71', name='NPV Freq'), row=2, col=2)
fig.add_vline(x=0, line_dash="dash", line_color="red", row=2, col=2)

fig.update_layout(height=800, showlegend=False, template="plotly_dark", hovermode="x unified")
st.plotly_chart(fig, width='stretch')