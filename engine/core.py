import numpy as np
from .configs import HardwareConfig, FacilityConfig, MarketConfig

class MiningFinancialModel:
    def __init__(self, hardware: HardwareConfig, facility: FacilityConfig, market: MarketConfig):
        self.hardware = hardware
        self.facility = facility
        self.market = market

    def calculate_fleet_sizing(self) -> tuple[int, float, float]:
        it_power_mw = self.facility.max_power_mw / self.facility.pue
        max_units = int((it_power_mw * 1e6) // self.hardware.power_w)
        installed_hashrate_ph = (max_units * self.hardware.hashrate_th) / 1e6
        capex = (max_units * self.hardware.cost_usd) * (1 + self.facility.infra_markup_pct)
        return max_units, installed_hashrate_ph, capex

    def _process_energy_profile(self, generation_tmy_mw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        years_needed = int(np.ceil(self.market.horizon_months / 12))
        full_generation = np.tile(generation_tmy_mw, years_needed)
        
        load_mw = np.clip(full_generation, a_min=0.0, a_max=self.facility.max_power_mw)
        
        chunk_size = 730 
        monthly_energy_kwh = np.zeros(self.market.horizon_months)
        capacity_factors = np.zeros(self.market.horizon_months)
        
        for i in range(self.market.horizon_months):
            start = i * chunk_size
            end = start + chunk_size
            chunk = load_mw[start:end]
            
            monthly_energy_kwh[i] = np.sum(chunk) * 1000
            capacity_factors[i] = np.mean(chunk) / self.facility.max_power_mw if self.facility.max_power_mw > 0 else 0
            
        return monthly_energy_kwh, capacity_factors

    def _simulate_gbm_hashprice(self) -> np.ndarray:
        dt = 1.0 / 12.0
        paths = np.zeros((self.market.horizon_months, self.market.num_paths))
        paths[0] = self.market.initial_hashprice
        
        drift_adj = (self.market.drift - 0.5 * self.market.volatility**2) * dt
        vol_adj = self.market.volatility * np.sqrt(dt)
        
        z = np.random.standard_normal((self.market.horizon_months - 1, self.market.num_paths))
        growth_multipliers = np.exp(drift_adj + vol_adj * z)
        
        for t in range(1, self.market.horizon_months):
            paths[t] = paths[t-1] * growth_multipliers[t-1]
            
        return paths

    def revenue_per_kwh(self, hashprice: float | np.ndarray) -> float | np.ndarray:
        j_per_th = self.hardware.power_w / self.hardware.hashrate_th
        return hashprice / (24 * j_per_th)
        
    def run_monte_carlo(self, generation_tmy_mw: np.ndarray) -> dict[str, float | np.ndarray]:
        units, hashrate_ph, capex = self.calculate_fleet_sizing()
        monthly_energy_kwh, capacity_factors = self._process_energy_profile(generation_tmy_mw)
        
        hashprice_paths = self._simulate_gbm_hashprice()
        
        rev_per_kwh_matrix = self.revenue_per_kwh(hashprice_paths)
        revenue_matrix = monthly_energy_kwh[:, None] * rev_per_kwh_matrix
        
        opex_energy = monthly_energy_kwh * self.facility.energy_price_kwh
        total_opex = opex_energy + self.facility.monthly_maintenance_usd
        
        fcf_matrix = revenue_matrix - total_opex[:, None]
        cash_flows = np.vstack([-capex * np.ones((1, self.market.num_paths)), fcf_matrix])
        
        monthly_discount_rate = (1 + self.market.discount_rate)**(1/12) - 1
        discount_factors = (1 + monthly_discount_rate)**-np.arange(self.market.horizon_months + 1)
        
        npv_paths = np.sum(cash_flows * discount_factors[:, None], axis=0)
        
        return {
            "fleet_size_units": units,
            "installed_hashrate_ph": hashrate_ph,
            "total_capex_usd": capex,
            "npv_mean": np.mean(npv_paths),
            "npv_median": np.median(npv_paths),
            "npv_5th_pct": np.percentile(npv_paths, 5),
            "npv_95th_pct": np.percentile(npv_paths, 95),
            "prob_positive_npv": np.mean(npv_paths > 0),
            "raw_cash_flows": cash_flows
        }