"""
Agent Classes
=============
All agent types: Fundamentalist, NoiseTrader, MarketMaker
"""

import numpy as np
from black_scholes import BlackScholesUtils


class Agent:
    """Base agent class"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.cash = 0.0
        self.stock_position = 0.0
        self.action_history = []

    def get_order(self, market_state: dict):
        """Override in subclasses"""
        raise NotImplementedError

    def log_action(self, action: str, details: dict):
        """Log agent action"""
        self.action_history.append({
            'action': action,
            'details': details
        })


class Fundamentalist(Agent):
    """
    FUNDAMENTALIST AGENT

    Strategy from seminar:
    Order = aggressiveness * (fundamental_value - current_price)

    Behavior:
    - Buys when price < fundamental value
    - Sells when price > fundamental value
    - Stabilizing force
    """

    def __init__(self, agent_id: str, fundamental_value: float, aggressiveness: float):
        super().__init__(agent_id)
        self.fundamental_value = fundamental_value
        self.aggressiveness = aggressiveness
        self.type = f"Fundamentalist(a={aggressiveness:.2f})"

    def get_order(self, market_state: dict):
        """
        Calculate order based on mispricing

        market_state: {'price': float, 'volatility': float, ...}
        """
        current_price = market_state['price']

        # Mispricing
        mispricing = self.fundamental_value - current_price

        # Order proportional to mispricing and aggressiveness
        order = self.aggressiveness * mispricing

        # Small random noise (agents not perfect)
        order += np.random.normal(0, 0.1)

        return order


class NoiseTrader(Agent):
    """
    NOISE TRADER

    Strategy: Random trading
    - Provides liquidity
    - Adds realism
    """

    def __init__(self, agent_id: str, noise_level: float):
        super().__init__(agent_id)
        self.noise_level = noise_level
        self.type = "NoiseTrader"

    def get_order(self, market_state: dict):
        """Pure random order"""
        return np.random.normal(0, self.noise_level)


class MarketMaker(Agent):
    """
    MARKET MAKER with DELTA HEDGING

    Job:
    1. Sells call option
    2. Delta hedges with rebalancing
    3. Pays transaction costs

    Two versions:
    - Black-Scholes (use original σ)
    - Leland (use modified σ_m)
    """

    def __init__(self, agent_id: str, strike: float, time_to_maturity: float,
                 risk_free_rate: float, k_transaction: float,
                 rebalance_frequency: int, use_leland: bool = True):
        super().__init__(agent_id)

        # Option parameters
        self.strike = strike
        self.initial_ttm = time_to_maturity
        self.time_to_maturity = time_to_maturity
        self.r = risk_free_rate
        self.k_transaction = k_transaction
        self.rebalance_frequency = rebalance_frequency
        self.use_leland = use_leland

        # Position
        self.short_option_position = 0
        self.target_delta = 0

        # Tracking
        self.cumulative_transaction_costs = 0.0
        self.step_counter = 0
        self.pnl_history = []
        self.bs = BlackScholesUtils()

        self.type = "MarketMaker_Leland" if use_leland else "MarketMaker_BS"

    def sell_option(self, initial_price: float, volatility: float):
        """Sell call option at start"""
        option_price = self.bs.call_price(
            initial_price, self.strike, self.time_to_maturity,
            self.r, volatility
        )

        self.cash += option_price
        self.short_option_position = -1

        self.log_action('sell_option', {
            'option_price': option_price,
            'stock_price': initial_price
        })

        return option_price

    def get_order(self, market_state: dict):
        """
        Delta hedging with rebalancing frequency

        КЛЮЧЕВОЕ: Ребалансируем НЕ каждый день!
        """
        self.step_counter += 1

        # Update time to maturity
        total_steps = market_state['total_steps']
        self.time_to_maturity = self.initial_ttm * (1 - self.step_counter / total_steps)

        if self.time_to_maturity <= 0 or self.short_option_position == 0:
            return 0

        # REBALANCE only every N days
        if self.step_counter % self.rebalance_frequency != 0:
            return 0

        current_price = market_state['price']
        volatility = market_state['volatility']
        dt = market_state['dt']

        # Choose volatility
        if self.use_leland:
            sigma_hedge = self.bs.leland_volatility(
                volatility, self.k_transaction, dt, short_gamma=True
            )
        else:
            sigma_hedge = volatility

        # Calculate target delta
        target_delta = self.bs.delta(
            current_price, self.strike, self.time_to_maturity,
            self.r, sigma_hedge
        )

        # How much to trade
        delta_hedge = target_delta - self.stock_position

        if abs(delta_hedge) < 0.01:
            return 0

        # Transaction cost: k * S * |ΔH|
        transaction_cost = self.k_transaction * current_price * abs(delta_hedge)

        # Update portfolio
        self.stock_position = target_delta
        self.cash -= delta_hedge * current_price
        self.cash -= transaction_cost
        self.cumulative_transaction_costs += transaction_cost

        # Log
        self.log_action('hedge', {
            'price': current_price,
            'delta_trade': delta_hedge,
            'tc': transaction_cost,
            'sigma_used': sigma_hedge
        })

        return delta_hedge

    def settle_option(self, final_price: float):
        """Settlement at expiration"""
        if self.short_option_position < 0:
            payoff = max(final_price - self.strike, 0)
            self.cash -= payoff
            self.cash += self.stock_position * final_price
            self.stock_position = 0

            self.log_action('settle', {
                'final_price': final_price,
                'option_payoff': payoff,
                'total_tc': self.cumulative_transaction_costs
            })

            return payoff

    def get_pnl(self, current_price: float):
        """Current P&L"""
        return self.cash + self.stock_position * current_price

    def update_pnl(self, current_price: float):
        """Update P&L history"""
        pnl = self.get_pnl(current_price)
        self.pnl_history.append(pnl)


# Test
if __name__ == "__main__":
    print("Testing agents...\n")

    # Test Fundamentalist
    fund = Fundamentalist("Fund_1", fundamental_value=100, aggressiveness=0.05)
    market_state = {'price': 95, 'volatility': 0.25}
    order = fund.get_order(market_state)
    print(f"Fundamentalist at price $95: order = {order:.2f} (should be BUY)")

    # Test NoiseTrader
    noise = NoiseTrader("Noise_1", noise_level=1.0)
    order = noise.get_order(market_state)
    print(f"NoiseTrader: order = {order:.2f} (random)")

    print("\n✓ Agents working!")
