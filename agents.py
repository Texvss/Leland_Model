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


class OptimizedLelandMarketMaker(MarketMaker):
    """
    OPTIMIZED LELAND MARKET MAKER

    Extends MarketMaker with optimized A parameter
    Instead of using Leland's formula A = (k/σ)*sqrt(8/(π*dt)),
    uses empirically optimized A* that minimizes hedging error variance

    Key difference:
    - MarketMaker (Leland=True): uses fixed A from formula
    - OptimizedLelandMarketMaker: uses calibrated A*
    """

    def __init__(self, agent_id: str, strike: float, time_to_maturity: float,
                 risk_free_rate: float, k_transaction: float,
                 rebalance_frequency: int, A_optimal: float):
        """
        Parameters:
        -----------
        A_optimal : float
            Pre-calibrated optimal A parameter
            Should be found using optimization.optimize_A_parameter()
        """
        # Initialize as Leland MM
        super().__init__(
            agent_id, strike, time_to_maturity, risk_free_rate,
            k_transaction, rebalance_frequency, use_leland=True
        )

        self.A_optimal = A_optimal
        self.type = "MarketMaker_OptimizedLeland"

    def get_order(self, market_state: dict):
        """
        Delta hedging with OPTIMIZED volatility adjustment

        Key difference: Uses A_optimal instead of Leland's formula
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

        # KEY DIFFERENCE: Use optimized A instead of formula
        sigma_hedge = volatility * np.sqrt(max(1 + self.A_optimal, 0.01))

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
            'sigma_used': sigma_hedge,
            'A_used': self.A_optimal
        })

        return delta_hedge


class MLCalibratedLelandMarketMaker(MarketMaker):
    """
    ML-CALIBRATED LELAND MARKET MAKER

    Extends OptimizedLelandMarketMaker with ML-based calibration
    Uses Bayesian Optimization + Gaussian Process instead of grid search

    Key differences:
    - MarketMaker (Leland=True): uses fixed A from formula
    - OptimizedLelandMarketMaker: uses grid-search calibrated A*
    - MLCalibratedLelandMarketMaker: uses ML-calibrated A* (more efficient)

    Hypothesis H2: ML-Calibrated performs better than Optimized
    """

    def __init__(self, agent_id: str, strike: float, time_to_maturity: float,
                 risk_free_rate: float, k_transaction: float,
                 rebalance_frequency: int, A_ml: float):
        """
        Parameters:
        -----------
        A_ml : float
            ML-calibrated optimal A parameter
            Should be found using ml_optimization.optimize_A_with_ML()
        """
        # Initialize as Leland MM
        super().__init__(
            agent_id, strike, time_to_maturity, risk_free_rate,
            k_transaction, rebalance_frequency, use_leland=True
        )

        self.A_ml = A_ml
        self.type = "MarketMaker_MLCalibrated"

    def get_order(self, market_state: dict):
        """
        Delta hedging with ML-CALIBRATED volatility adjustment

        Key difference: Uses A_ml from Bayesian Optimization
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

        # KEY DIFFERENCE: Use ML-calibrated A
        sigma_hedge = volatility * np.sqrt(max(1 + self.A_ml, 0.01))

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
            'sigma_used': sigma_hedge,
            'A_used': self.A_ml
        })

        return delta_hedge


class OptionTrader(Agent):
    """
    OPTION TRADER (Buyer)

    Strategy:
    - Buys call option at t=0 (pays premium)
    - Holds until expiration (no hedging)
    - Receives payoff at maturity

    Represents aggregate of all option buyers
    Counterparty to MarketMaker
    """

    def __init__(self, agent_id: str, strike: float):
        super().__init__(agent_id)
        self.strike = strike
        self.long_option_position = 0
        self.type = "OptionTrader"
        self.option_premium_paid = 0.0

    def buy_option(self, option_price: float):
        """Buy call option at start"""
        self.cash -= option_price
        self.long_option_position = 1
        self.option_premium_paid = option_price

        self.log_action('buy_option', {
            'premium_paid': option_price
        })

        return option_price

    def get_order(self, market_state: dict):
        """
        Option trader does NOT trade during life of option
        Just holds until expiration
        """
        return 0  # No trading

    def settle_option(self, final_price: float):
        """Receive option payoff at expiration"""
        if self.long_option_position > 0:
            payoff = max(final_price - self.strike, 0)
            self.cash += payoff
            self.long_option_position = 0

            total_pnl = self.cash  # Cash now = payoff - initial_premium

            self.log_action('settle', {
                'final_price': final_price,
                'option_payoff': payoff,
                'initial_premium': self.option_premium_paid,
                'total_pnl': total_pnl
            })

            return payoff

    def get_pnl(self, current_price: float):
        """Current P&L (mark-to-market)"""
        if self.long_option_position > 0:
            # Approximate value = intrinsic value (simplified)
            current_value = max(current_price - self.strike, 0)
            return self.cash + current_value
        return self.cash


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

    # Test OptionTrader
    option_trader = OptionTrader("OptionTrader_1", strike=100)
    option_trader.buy_option(10.0)
    print(f"\nOptionTrader bought option for $10.00")
    print(f"  Position: {option_trader.long_option_position} call")
    payoff = option_trader.settle_option(110)
    print(f"  Settled at S=$110: payoff=${payoff:.2f}, P&L=${option_trader.cash:.2f}")

    print("\n✓ All agents working!")
