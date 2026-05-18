from dataclasses import dataclass

@dataclass(frozen=True)
class HardwareConfig:
    """
    Defines the physical and economic specifications of a single mining unit.
    """
    hashrate_th: float  # Nominal hashrate in Terahash per second (TH/s)
    power_w: float      # Power consumption in Watts (W)
    cost_usd: float     # Purchase price per unit in USD


@dataclass(frozen=True)
class FacilityConfig:
    """
    Defines the infrastructure, energy contract, and operational constraints.
    """
    max_power_mw: float            # Maximum allowable power draw from the grid/plant (MW)
    pue: float                     # Power Usage Effectiveness (Total Power / IT Power)
    energy_price_kwh: float        # Fixed cost of electricity in USD/kWh
    infra_markup_pct: float        # CAPEX markup for balance-of-plant (transformers, racks, etc.)
    monthly_maintenance_usd: float # Fixed monthly OPEX (security, staff, insurance)


@dataclass(frozen=True)
class MarketConfig:
    """
    Parameters for the stochastic (GBM) and deterministic market dynamics.
    """
    initial_hashprice: float  # Starting revenue in USD per PH/day
    drift: float              # Annualized expected growth/decline (mu)
    volatility: float         # Annualized standard deviation of returns (sigma)
    horizon_months: int       # Total duration of the simulation
    discount_rate: float      # Annualized WACC used for NPV calculations
    num_paths: int            # Total iterations for the Monte Carlo simulation