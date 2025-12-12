"""
Configuration for Leland ABM Project
====================================
All parameters in one place
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class Config:
    """Main configuration"""

    # ===== DATA PARAMETERS =====
    ticker: str = "AAPL"
    start_date: str = "2021-01-01"
    end_date: str = "2023-12-31"  # 2 ГОДА!

    # ===== OPTION PARAMETERS =====
    strike_offset: float = 0.0  # K = S0 * (1 + offset), 0 = ATM
    time_to_maturity: float = 1.0  # years
    risk_free_rate: float = 0.05

    # ===== TRANSACTION COSTS =====
    k_transaction: float = 0.01  # 1%

    # ===== REBALANCING =====
    # ВАЖНО: Не каждый день!
    rebalance_frequency: int = 5  # Каждые 5 дней (1 неделя)

    # ===== FUNDAMENTALIST PARAMETERS =====
    # 3 типа фундаменталистов с разной агрессивностью
    n_fundamentalist_low: int = 3      # Консервативные
    n_fundamentalist_medium: int = 3   # Средние
    n_fundamentalist_high: int = 3     # Агрессивные

    aggressiveness_low: float = 0.02    # Низкая агрессивность
    aggressiveness_medium: float = 0.05  # Средняя
    aggressiveness_high: float = 0.10    # Высокая

    # ===== NOISE TRADER PARAMETERS =====
    n_noise_traders: int = 5
    noise_level: float = 1.0

    # ===== MONTE CARLO PARAMETERS =====
    mc_simulations: int = 50000
    mc_steps_per_year: int = 252  # Торговых дней

    # ===== OTHER =====
    random_seed: int = 42

    def __post_init__(self):
        """Calculate derived parameters"""
        np.random.seed(self.random_seed)

    def display(self):
        """Print configuration"""
        print("\n" + "="*60)
        print("PROJECT CONFIGURATION")
        print("="*60)

        print(f"\nData:")
        print(f"  Ticker:              {self.ticker}")
        print(f"  Period:              {self.start_date} to {self.end_date}")
        print(f"  Duration:            ~2 years")

        print(f"\nOption:")
        print(f"  Time to maturity:    {self.time_to_maturity} year")
        print(f"  Risk-free rate:      {self.risk_free_rate*100:.2f}%")
        print(f"  Strike offset:       {self.strike_offset*100:+.1f}%")

        print(f"\nTransaction Costs:")
        print(f"  k coefficient:       {self.k_transaction*100:.2f}%")

        print(f"\nRebalancing:")
        print(f"  Frequency:           Every {self.rebalance_frequency} days")

        print(f"\nAgents:")
        total_fund = (self.n_fundamentalist_low +
                     self.n_fundamentalist_medium +
                     self.n_fundamentalist_high)
        print(f"  Fundamentalists:     {total_fund}")
        print(f"    - Low aggr.:       {self.n_fundamentalist_low} (a={self.aggressiveness_low})")
        print(f"    - Medium aggr.:    {self.n_fundamentalist_medium} (a={self.aggressiveness_medium})")
        print(f"    - High aggr.:      {self.n_fundamentalist_high} (a={self.aggressiveness_high})")
        print(f"  NoiseTraders:        {self.n_noise_traders}")
        print(f"  MarketMakers:        2 (BS + Leland)")
        print(f"  OptionTraders:       2 (counterparties to MMs)")

        print(f"\nMonte Carlo:")
        print(f"  Simulations:         {self.mc_simulations:,}")

        print("="*60 + "\n")


# Create global config instance
config = Config()


if __name__ == "__main__":
    config.display()
