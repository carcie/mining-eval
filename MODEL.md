Financial model for a cryptocurrency mining operation that draws up to 20 MW of power from an existing wind‑solar hybrid plant under a **fixed‑price, behind‑the‑meter energy contract**. The model explicitly accounts for the intermittency of renewable generation, hardware constraints, network difficulty dynamics, and market price volatility. Its output comprises the standard investment metrics: Net Present Value (NPV), Internal Rate of Return (IRR), payback period, and probability distributions for key outcomes obtained via Monte Carlo simulation.

All mathematical formulations are stated explicitly, assumptions are justified, and the computational framework is designed to be fully reproducible given the same input data.

---

## 2. Key Assumptions & Constraints

### 2.1 Energy Supply and Contract
- **Source**: A hybrid wind‑solar plant with a metered point of interconnection. The miner is connected behind the utility meter (BTM).
- **Generation Profile**: Realistic hourly capacity factors are derived from a Typical Meteorological Year (TMY) dataset for the location. The profile exhibits the described diurnal pattern: strong winds overnight and early morning, a midday lull, rising again after 4 PM, supplemented by solar generation during daylight hours.
- **Power Cap**: The miner may draw **up to 20 MW** at any instant. If available generation is less than 20 MW, the miner’s load must be curtailed accordingly. If generation exceeds 20 MW, the miner consumes exactly 20 MW and the surplus is assumed to be sold to the grid by the renewable plant (not modelled here).
- **Pricing**: The miner pays a **fixed price per kWh** of energy consumed (input by the user). There is no capacity or demand charge, and no exposure to wholesale spot prices. The contract is “take‑if‑available”; there is no penalty for partial load.

### 2.2 Mining Hardware
- A homogeneous fleet of a single SHA‑256 ASIC model is deployed. The model selection is optimised to maximise hashrate density (minimise Joules per Terahash) within the 20 MW envelope. The dataset provided (or any updated list) is used to choose the machine that yields the highest total hashrate under the power limit.
- **Power‑Usage Effectiveness (PUE)** is applied: total facility load = IT load × PUE. The 20 MW cap applies to the total facility load, so the allowable IT load = 20 MW / PUE.
- **Throttling and Fleet Management**: The miner’s total power draw can be modulated continuously from 0 to 20 MW (idealised). In practice this is achieved by switching individual units on/off, with a sufficiently large number of units that the quantisation error is negligible. Each ASIC is assumed to have a constant hashrate‑per‑watt efficiency across its entire load range (no efficiency loss at partial load).

### 2.3 Market & Network Dynamics
- **Initial Hashprice** ($H_0$): The daily revenue per petahash per second (PH/s) at model start, expressed in USD.
- **BTC Price & Difficulty**: Both evolve stochastically. The hashprice drift and volatility are modelled directly as a Geometric Brownian Motion (GBM) to reduce dimensionality.
  - Long‑term expected hashprice decline (negative drift) reflects expected network hashrate growth exceeding any BTC price appreciation.
  - Volatility captures combined price and difficulty uncertainty.
- **Horizon**: The project is evaluated over a finite horizon \(T\) (e.g., 24 or 48 months), after which all hardware is considered fully depreciated (no salvage value).

### 2.4 Financial Assumptions
- **Capital Expenditure (CAPEX)**: Purchase cost of ASICs + balance‑of‑plant (transformers, switchgear, cooling). For simplicity, balance‑of‑plant is modelled as a fixed mark‑up on hardware cost (or a lump sum).
- **Operating Expenditure (OPEX)**:
  - Energy cost: \(E_{\text{consumed}} \times \text{fixed\_price/kWh}\)
  - Maintenance & overheads: a fixed monthly cost, possibly as a percentage of hardware CAPEX.
- **Discount Rate**: Weighted Average Cost of Capital (WACC, \(r\)).
- **Tax and Depreciation**: Ignored for simplicity; can be added later.

---

## 3. Mathematical Formulation

### 3.1 Generation Profile and Available Power
Let the year‑long hourly generation time series be \(G(t)\) [MW] for hours \(t = 1, 2, \dots, 8760\). This series is repeated for each year of the project. The miner’s load at hour \(t\) is:

\[
P_{\text{load}}(t) = \min\bigl(G(t),\, P_{\max}\bigr)
\]

where \(P_{\max} = 20\) MW. The total energy consumed in month \(m\) (with \(n_m\) hours) is:

\[
E_m = \sum_{t \in \text{month } m} P_{\text{load}}(t) \times 1\,\text{hour}
\]

The **capacity factor** of the mining operation is

\[
CF_m = \frac{E_m}{P_{\max} \times n_m}
\]

which directly reduces the effective hashrate and revenue.

### 3.2 Hardware Fleet Sizing
Given a chosen ASIC with nominal hashrate \(h\) [TH/s], power consumption \(w\) [W] and cost \(C_u\), the **IT power limit** is \(P_{\text{IT}} = \frac{20\,\text{MW}}{\text{PUE}}\). The maximum number of units is:

\[
N = \left\lfloor \frac{P_{\text{IT}} \times 10^6}{w} \right\rfloor
\]

Total installed hashrate (theoretical maximum, if running at full IT power):

\[
H_{\text{inst}} = N \times h \quad [\text{TH/s}] = N \times h \times 10^{-6} \quad [\text{PH/s}]
\]

### 3.3 Effective Hashrate and Revenue
Since the miner throttles with available generation, the **realised hashrate** in hour \(t\) is scaled proportionally to the power drawn:

\[
H_{\text{eff}}(t) = H_{\text{inst}} \times \frac{P_{\text{load}}(t)}{P_{\max}}
\]

Revenue per hour is:

\[
R_{\text{hour}}(t) = H_{\text{eff}}(t) \times \text{hashprice}_{\text{hourly}}(t)
\]

where hourly hashprice is derived from the monthly stochastic process described below, assumed constant within a month.

**Monthly revenue** (month \(m\)):

\[
R_m = \sum_{\text{hours in } m} H_{\text{eff}}(t) \times \text{hashprice}_m \times \frac{1}{24} \quad \text{(if hashprice is daily) or appropriate time factor}
\]

Using daily hashprice \(H_{\text{daily}}\) expressed in $/PH/day, monthly revenue becomes:

\[
R_m = \left( \sum_{t \in m} H_{\text{eff}}(t) \right) \times H_{\text{daily},m} \times \frac{1}{24} \times \frac{1}{10^6}
\]

(where \(H_{\text{eff}}\) is in TH/s, converted to PH/s appropriately).

### 3.4 Cost Model
- **CAPEX**: \( \text{CAPEX} = N \times C_u + \text{Infra\_Cost} \)
- **Monthly OPEX**: 
  \[
  \text{OPEX}_m = E_m \times p_{\text{fix}} + \text{Maintenance}_m
  \]
  where \(p_{\text{fix}}\) is the fixed energy price ($/kWh). \(E_m\) is in kWh.

### 3.5 Cash Flow and Valuation Metrics
Monthly free cash flow to firm:

\[
\text{FCF}_0 = -\text{CAPEX}
\]
\[
\text{FCF}_m = R_m - \text{OPEX}_m \quad (m = 1, \dots, T)
\]

NPV:

\[
\text{NPV} = \sum_{m=0}^{T} \frac{\text{FCF}_m}{(1 + r_m)^m}
\]

where the monthly discount rate \(r_m = (1 + r)^{1/12} - 1\) (or simply \(r/12\) for continuous compounding). IRR is the rate \(i\) that solves \(\text{NPV}(i) = 0\). Payback period is the first month where cumulative undiscounted cash flow becomes positive.

### 3.6 Stochastic Modeling of Hashprice
The daily hashprice \(H_t\) (USD per PH/s per day) is modelled as a Geometric Brownian Motion under the risk‑neutral or real‑world measure:

\[
dH = \mu H \, dt + \sigma H \, dW
\]

where \(\mu\) is the expected annual drift (negative, due to difficulty growth) and \(\sigma\) is annual volatility. For monthly simulation, the discrete update is:

\[
H_{m+1} = H_m \exp\left[ \left(\mu - \tfrac{1}{2}\sigma^2\right)\Delta t + \sigma \sqrt{\Delta t} \, \epsilon \right], \quad \epsilon \sim \mathcal{N}(0,1)
\]

with \(\Delta t = 1/12\).

**Calibration**: \(\mu\) and \(\sigma\) are estimated from historical hashprice time series or from separate BTC price and network difficulty models. For an investment analysis, conservative values are used (e.g., \(\mu = -20\%\) p.a., \(\sigma = 80\%\) p.a.).

**Monte Carlo Procedure**: Generate \(K\) independent paths of monthly hashprices. For each path, compute the resulting cash flows using the deterministic generation profile (repeated annually) and the variable \(H_m\). Discount each path’s cash flows to obtain a distribution of NPV and IRR. Report median, percentiles, and probability of positive NPV.

### 3.7 Sensitivity Analysis
A tornado chart can be constructed by varying key inputs (\(\pm 20\%\)) one at a time (energy price, initial hashprice, \(\mu\), \(\sigma\), PUE) and recording the impact on base‑case NPV.

---

## 4. Model Constraints & Limitations

- **Throttling Ideality**: ASIC miners do not scale linearly down to zero load; efficiency may degrade slightly at partial load. The error is small if the fleet consists of many units and the capacity factor is above ~20%.
- **No Grid Export Arbitrage**: The model assumes the miner cannot choose to export to the grid when spot prices are high; it only consumes what is available. A more advanced model could add a dispatch choice if the BTM agreement allows it.
- **Static Fleet**: No mid‑horizon hardware upgrades. The model can be extended to include a deployment phase.
- **No BTC Price / Difficulty Separation**: The combined hashprice GBM simplifies analysis but obscures scenarios where price soars while difficulty lags. For a more granular view, separate stochastic processes for BTC price and network hashrate growth could be used.
- **Contract Price Risk**: The fixed energy price is assumed constant for the entire horizon. Escalation clauses are easily added.

---


Relationship between the electrical energy consumed by a mining facility and the fiat revenue it generates.

---

## 1. Derivation

### 1.1 Hashrate as a function of power
For any given ASIC miner (or a homogeneous fleet), the nominal hashrate \(H\) (in TH/s) and power consumption \(P\) (in Watts) are linked by the **energy efficiency** of the hardware:

\[
J = \frac{P}{H} \quad \text{[Joules per Terahash, J/TH]}
\]

Conversely,

\[
H = \frac{P}{J}
\]

If the miner’s actual power draw is \(P(t)\) at time \(t\), the instantaneous hashrate is

\[
H(t) = \frac{P(t)}{J}
\]

*(Note: This assumes the efficiency \(J\) is constant across the load range. For fleets with many units that are switched on/off, the aggregate efficiency is effectively constant.)*

### 1.2 Revenue as a function of hashrate
The fiat revenue per unit of hashrate is the **hashprice** \(HP\) (commonly quoted in USD per PH/s per day). In consistent units, the instantaneous revenue rate is:

\[
R_{\text{inst}}(t) \;\; \left[\frac{\text{USD}}{\text{day}}\right] = H(t) \cdot HP(t)
\]

With \(H\) in PH/s and \(HP\) in USD/PH/s/day.  
If \(H\) is in TH/s, convert: \(1 \text{ PH/s} = 1000 \text{ TH/s}\), so

\[
R_{\text{inst}}(t) = \frac{H_{\text{TH}}(t)}{1000} \cdot HP(t) \quad \text{[USD/day]}
\]

### 1.3 Revenue as a function of energy consumption
Substitute \(H(t) = P(t)/J\) (with \(P\) in Watts, \(J\) in J/TH, careful with units):

- \(P\) in Watts = Joules per second.
- \(H\) in TH/s = \(P / J\) (since 1 W = 1 J/s, and 1 TH/s = \(10^{12}\) H/s, but \(J\) is defined as J/TH, meaning \(J\) Joules per \(10^{12}\) hashes).


(Work directly in practical units)  
If the miner consumes \(E\) kWh of energy over some period, the total power-seconds is \(E \times 1000 \times 3600 = 3.6 \times 10^6 \, E\) Joules.

The total hashes computed are

\[
\text{Total TH} = \frac{\text{Total Joules}}{J} = \frac{3.6 \times 10^6 \, E}{J} \quad [\text{TH}]
\]

If we define the hashprice \(HP\) in USD per TH (instead of per PH), the revenue \(R\) [USD] from consuming \(E\) kWh is simply:

\[
R = \text{Total TH} \times HP_{\text{per TH}} = \frac{3.6 \times 10^6 \, E}{J} \cdot HP_{\text{per TH}}
\]

Thus, **for a fixed hardware efficiency and constant hashprice**, revenue is strictly proportional to energy consumed:

\[
\boxed{R = k \cdot E}
\]
where the constant \(k\) is
\[
k = \frac{3.6 \times 10^6}{J} \cdot HP_{\text{per TH}} \quad \text{or equivalently} \quad k = \frac{HP_{\text{daily per PH}}}{J/1000} \cdot \frac{1}{24} \quad \text{(if you prefer daily units).}
\]

---

## 2. Why the Relationship Is Not Trivial

In reality, both \(J\) and \(HP\) change over time:

- **Hardware upgrades**: Newer machines have lower \(J\) (better efficiency), so the same kWh yields more revenue.
- **Hashprice fluctuates**: The market price of Bitcoin and the global network difficulty cause \(HP\) to vary hour by hour. So the revenue per kWh is not constant; it’s a **stochastic process**.
- **Behind‑the‑meter dispatch**: With variable renewable generation, consumption isn't always the maximum possible power. If hashprice and available generation are correlated (e.g., high hashprice exactly when the wind lulls), the effective revenue per kWh consumed can differ from the unconditional average.

Therefore, studying the relationship requires separating the deterministic physical kernel from the stochastic market overlay.

---

## 3. Reliable Tools to Study the Energy‑Revenue Relationship

Three categories: **static analysis**, **time‑series / empirical models**, and **stochastic simulation**.

### 3.1 Deterministic Unit Economics (First‑Principle Model)

Use the derived formula to calculate the **static revenue efficiency** of any hardware fleet:

\[
\text{Revenue per kWh} = \frac{HP_{\text{current}}}{J} \times \text{(unit conversion factor)}
\]

**Application**:
- Compute this number for each ASIC model in our dataset using the current hashprice.
- Rank machines by revenue per kWh to quickly see which converts electricity into dollars most efficiently.
- Track this metric historically by substituting a time series of hashprice; you obtain a time series of revenue per kWh for a fixed hardware.


### 3.2 Empirical Regression and Correlation Analysis

Historical data for your mining facility (or a similar one) that includes:
- Hourly (or daily) energy consumption \(E_t\)
- Hourly (or daily) revenue \(R_t\)
- And the corresponding hashprice \(HP_t\)


#### a) Simple linear regression (no intercept)
\[
R_t = \beta \, E_t + \varepsilon_t
\]
The estimated coefficient \(\hat{\beta}\) is the **average realized revenue per kWh** over the sample period. If the hardware efficiency didn’t change, this \(\hat{\beta}\) should be close to the deterministic \(k\) computed using the average hashprice. Any deviation indicates hardware degradation, curtailment losses, or measurement errors.

#### b) Multiple regression with hashprice as a control
\[
R_t = \beta_1 E_t + \beta_2 HP_t + \varepsilon_t
\]
Theory says \(\beta_1\) should be proportional to \(1/J\) and \(\beta_2\) should be proportional to the total hashes per unit energy. This allows you to verify the physical model from data.

#### c) Correlation with generation profile
If only have the renewable generation profile and not actual mining data, we can compute the **Pearson correlation coefficient** between available power \(P_{\text{avail}}(t)\) and the hashprice \(HP(t)\) over the same time windows (e.g., daily, hourly). This quantifies whether high-revenue hours tend to coincide with high-availability hours.

**Tool**: Ordinary Least Squares (OLS) with standard errors robust to heteroskedasticity (common in financial data). 

### 3.3 Time‑Series Models for Revenue per kWh

Define a new variable:

\[
Y_t = \frac{R_t}{E_t} \quad \text{(revenue per kWh consumed at time }t\text{)}
\]

From the derivation, \(Y_t = \frac{3.6 \times 10^6}{J} \cdot HP_t\), a simple scaled version of the hashprice. Thus, any model that fits hashprice can be applied to \(Y_t\).

**Recommended tools**:
- **Autoregressive Integrated Moving Average (ARIMA)** models to forecast future \(Y_t\) based on its own past values, for a purely statistical forecast.
- **Geometric Brownian Motion (GBM)** for simulation. GBM is widely used for hashprice; the same model with drift \(\mu\) and volatility \(\sigma\) directly describes the evolution of revenue per kWh.

These models are reliable if the underlying series is stationary (or made stationary by differencing). Standard diagnostic tests (ADF, KPSS, Ljung‑Box) must be applied to validate the model.

### 3.4 Stochastic Simulation (Monte Carlo) for the Behind‑the‑Meter Case

When the facility is subject to intermittent generation, the relationship between **total monthly energy consumed** and **total monthly revenue** becomes:

\[
R_{\text{month}} = \frac{3.6 \times 10^6}{J} \cdot \sum_{t \in \text{month}} \bigl( E_{\text{consumed}}(t) \cdot HP_t \bigr)
\]

Because \(E_{\text{consumed}}(t) = \min(G(t), P_{\max})\), the monthly revenue is **not** simply proportional to total monthly energy unless \(HP_t\) is constant. To study this relationship rigorously:

- **Step 1**: Model the joint hourly process of \((G(t), HP_t)\). For \(G(t)\), use the historical generation profile (deterministic repeatable pattern). For \(HP_t\), either assume it is independent of \(G(t)\) (justified if no local market manipulation) or model a diurnal/seasonal pattern if empirical data show correlation.
- **Step 2**: Generate many Monte Carlo paths of \(HP_t\) (hourly) by downscaling the monthly GBM to hourly using a consistent variance (e.g., assume constant volatility per hour and no intraday patterns).
- **Step 3**: For each path, compute the pair \(\bigl(\text{Total Energy}_m, \text{Revenue}_m\bigr)\) for each month.
- **Step 4**: Analyze the scatter plot of Revenue vs Energy across all simulated months. Fit a linear model (or a non‑parametric smoother like LOESS) to see if the relationship remains linear. Compute the coefficient of variation and confidence bands.

**Mathematical tools**: Monte Carlo simulation with a deterministic generation profile is a robust numerical method. The result gives you the **stochastic revenue‑per‑kWh function** \(f(E) = \mathbb{E}[R \mid E]\). If \(HP_t\) is independent of generation, the function is linear with slope equal to the average hashprice scaled by hardware efficiency. If not, you’ll see curvature.

### 3.5 Optimization Under Uncertainty: Stochastic Programming

If the facility can *choose* its load level (e.g., by turning miners on/off), the relationship between energy and revenue becomes a decision function. Tools like **Dynamic Programming** or **Reinforcement Learning** can find the optimal dispatch policy that maximizes profit by balancing the cost of energy (fixed price) against the stochastic revenue. Here the “revenue generated per unit energy” is the marginal value of electricity. The mathematical framework is Markov Decision Processes (MDP) with state variables = current hashprice and available generation.

---

## 4. A Concrete Example: Studying the Revenue/kWh Distribution

**Problem**: You have a wind‑solar hybrid plant with an hourly generation profile for a full year, and a fixed hardware fleet with efficiency \(J = 20 \text{ J/TH}\). You want to know the probability distribution of the annual average revenue per kWh consumed, given a GBM for hashprice.

**Tool**: Monte Carlo simulation (Python `numpy`).

**Steps**:
1. Import generation profile \(G(t)\) (8760 hours).
2. Initialize Monte Carlo parameters: \(H_0\) (initial hashprice), \(\mu, \sigma\), number of paths \(N\).
3. For each path:
   - Generate an 8760‑hour hashprice series: start with daily values from GBM, interpolate to hourly (e.g., constant within day, or a small diurnal pattern if desired).
   - For each hour, compute power drawn \(P(t) = \min(G(t), 20\text{ MW})\).
   - Energy consumed in hour: \(E(t) = P(t) \times 1\text{ h}\).
   - Revenue in hour: \(R(t) = \frac{P(t) \times 10^6 \text{ W}}{J \text{ (J/TH)}} \cdot HP(t) \cdot \text{(conversion factor)}\) (careful with units: \(P\) in W = J/s, so hashrate TH/s = \(P/J \times 10^{-12}\)? Actually, we can use the earlier conversion: total hashes per hour = \((P \times 3600) / J\) TH, then revenue = total hashes × HP_per_TH. So easier: compute daily revenue using daily average power and daily HP.
   - Sum monthly revenue and energy.
4. For each path, compute the annual average revenue per kWh = total revenue / total energy.





