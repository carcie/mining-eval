import numpy as np
import yfinance as yf
import requests
from .configs import MarketConfig

class MarketCalibrator:

    @staticmethod
    def get_live_hashprice(url: str = "https://insights.braiins.com/api/v1.0/hashrate-stats") -> float | None:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            return float(data["mining_economics"]["hash_price"]) * 1000.0
        except Exception:
            return None

    @staticmethod
    def calibrate_from_btc(
        ticker: str = "BTC-USD",
        period: str = "2y",
        difficulty_growth_rate: float = 0.15,
        initial_hashprice: float = 40.0,
        horizon_months: int = 12,
        discount_rate: float = 0.09,
        num_paths: int = 5000
    ) -> MarketConfig:
        try:
            df = yf.download(ticker, period=period, progress=False)
            if df.empty:
                raise ValueError(f"No data found for ticker {ticker}")
            
            prices = df["Close"].values.flatten()
        except Exception as e:
            print(f"Warning: Market calibration failed ({e}). Using defaults.")
            return MarketConfig(
                initial_hashprice=initial_hashprice,
                drift=-difficulty_growth_rate, 
                volatility=0.75,                
                horizon_months=horizon_months,
                discount_rate=discount_rate,
                num_paths=num_paths
            )

        log_returns = np.diff(np.log(prices))
        mu_btc_annual = np.mean(log_returns) * 365
        sigma_btc_annual = np.std(log_returns, ddof=1) * np.sqrt(365)
        hashprice_drift = mu_btc_annual - difficulty_growth_rate
        
        return MarketConfig(
            initial_hashprice=initial_hashprice,
            drift=hashprice_drift,
            volatility=sigma_btc_annual,
            horizon_months=horizon_months,
            discount_rate=discount_rate,
            num_paths=num_paths
        )