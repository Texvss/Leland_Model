"""
Market with Real Data
=====================
Market that uses historical prices from Yahoo Finance
"""

import numpy as np
import pandas as pd
import yfinance as yf


def download_market_data(ticker: str, start_date: str, end_date: str):
    """
    Download historical stock data from Yahoo Finance

    Returns:
    --------
    dict with 'prices', 'dates', 'volatility', 'drift'
    """
    print(f"\n📊 Downloading {ticker} data...")
    print(f"   Period: {start_date} to {end_date}")

    # Download with auto_adjust=True to suppress warning
    data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)

    if data.empty:
        raise ValueError(f"No data downloaded for {ticker}")

    # Handle MultiIndex columns (when auto_adjust=True)
    if isinstance(data.columns, pd.MultiIndex):
        # Flatten MultiIndex: ('Close', 'AAPL') -> just get Close column
        data.columns = data.columns.droplevel(1)

    # Get Close prices
    if 'Close' in data.columns:
        prices = data['Close'].values
    else:
        # Fallback: use first column
        prices = data.iloc[:, 0].values

    dates = data.index

    # Validate data
    if len(prices) < 20:
        raise ValueError(f"Not enough data downloaded for {ticker}. Got only {len(prices)} days. Need at least 20 days.")

    # Calculate realized volatility
    returns = np.diff(np.log(prices))

    # Handle potential NaN/inf
    returns = returns[np.isfinite(returns)]

    if len(returns) < 10:
        raise ValueError(f"Not enough valid returns for volatility calculation. Got {len(returns)} valid returns.")

    realized_vol = np.std(returns) * np.sqrt(252)
    realized_drift = np.mean(returns) * 252

    # Ensure scalar values
    realized_vol = float(realized_vol) if np.isfinite(realized_vol) else 0.25
    realized_drift = float(realized_drift) if np.isfinite(realized_drift) else 0.05

    print(f"✓ Downloaded {len(prices)} days")
    print(f"   Price range: ${float(prices.min()):.2f} - ${float(prices.max()):.2f}")
    print(f"   Realized volatility: {realized_vol*100:.2f}%")
    print(f"   Realized drift: {realized_drift*100:.2f}%\n")

    return {
        'prices': prices,
        'dates': dates,
        'ticker': ticker,
        'volatility': realized_vol,
        'drift': realized_drift
    }


class RealDataMarket:
    """
    Market using REAL historical prices

    Key difference from standard ABM:
    - Prices come from Yahoo Finance
    - Agents don't affect price (it's historical)
    - But agents REACT to real market movements
    """

    def __init__(self, real_prices: np.ndarray, realized_volatility: float,
                 time_to_maturity: float):
        self.real_prices = real_prices
        self.realized_volatility = realized_volatility
        self.time_to_maturity = time_to_maturity

        self.current_step = 0
        self.n_steps = len(real_prices) - 1

        # Current state
        self.current_price = real_prices[0]

        # History
        self.trade_history = []

    def get_price(self):
        """Current price from historical data"""
        return float(self.real_prices[self.current_step])

    def get_volatility(self, window=20):
        """
        Calculate rolling volatility

        Uses last 'window' days of price data
        """
        if self.current_step < window:
            return float(self.realized_volatility)

        recent_prices = self.real_prices[max(0, self.current_step - window):self.current_step + 1]

        if len(recent_prices) < 2:
            return float(self.realized_volatility)

        returns = np.diff(np.log(recent_prices))
        returns = returns[np.isfinite(returns)]

        if len(returns) < 2:
            return float(self.realized_volatility)

        vol = np.std(returns) * np.sqrt(252)

        # Return scalar float
        vol = float(vol) if np.isfinite(vol) and vol > 0 else float(self.realized_volatility)
        return vol

    def get_time_to_maturity(self):
        """Time remaining until option expiration"""
        time_fraction = 1 - (self.current_step / self.n_steps)
        return self.time_to_maturity * time_fraction

    def get_market_state(self):
        """
        Get current market state for agents

        Returns dict with all info agents need
        """
        return {
            'price': self.get_price(),
            'volatility': self.get_volatility(),
            'time_to_maturity': self.get_time_to_maturity(),
            'step': self.current_step,
            'total_steps': self.n_steps,
            'dt': self.time_to_maturity / self.n_steps
        }

    def log_trade(self, agent_id: str, trade_type: str, quantity: float, price: float):
        """Log a trade"""
        self.trade_history.append({
            'step': self.current_step,
            'agent': agent_id,
            'type': trade_type,
            'quantity': quantity,
            'price': price
        })

    def step(self):
        """
        Move to next time step

        Price comes from historical data!
        """
        self.current_step += 1
        if self.current_step < len(self.real_prices):
            self.current_price = self.real_prices[self.current_step]

    def is_finished(self):
        """Check if simulation is done"""
        return self.current_step >= self.n_steps


# Test
if __name__ == "__main__":
    print("Testing market with real data...\n")

    # Download test data
    market_data = download_market_data("AAPL", "2023-01-01", "2023-12-31")

    # Create market
    market = RealDataMarket(
        real_prices=market_data['prices'],
        realized_volatility=market_data['volatility'],
        time_to_maturity=1.0
    )

    print(f"Market created:")
    print(f"  Initial price: ${market.get_price():.2f}")
    print(f"  Volatility: {market.get_volatility()*100:.2f}%")
    print(f"  Total steps: {market.n_steps}")

    # Simulate a few steps
    print("\nSimulating 5 steps:")
    for i in range(5):
        state = market.get_market_state()
        print(f"  Step {i}: Price=${state['price']:.2f}, TTM={state['time_to_maturity']:.4f}")
        market.step()

    print("\n✓ Market working!")
