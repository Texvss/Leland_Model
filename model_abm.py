"""
ABM Model with Real Data
========================
Agent-Based Model running on historical market data
"""

import numpy as np
from config import Config
from market import RealDataMarket, download_market_data
from agents import Fundamentalist, NoiseTrader, MarketMaker, OptionTrader, OptimizedLelandMarketMaker, MLCalibratedLelandMarketMaker


class ABMModel:
    """
    Agent-Based Model with Real Market Data

    Combines:
    - Real historical prices from Yahoo Finance
    - Multiple agent types (Fundamentalists, Noise Traders)
    - Market Makers with delta hedging (BS vs Leland)
    """

    def __init__(self, config: Config, market_data: dict, A_optimal: float = None, A_ml: float = None):
        self.config = config
        self.A_optimal = A_optimal  # Optional: for Optimized Leland
        self.A_ml = A_ml  # Optional: for ML-Calibrated Leland

        # Create market with real data
        self.market = RealDataMarket(
            real_prices=market_data['prices'],
            realized_volatility=market_data['volatility'],
            time_to_maturity=config.time_to_maturity
        )

        # Calculate strike
        initial_price = market_data['prices'][0]
        self.strike = initial_price * (1 + config.strike_offset)

        # Fundamental value = initial price (or could be different)
        self.fundamental_value = initial_price

        # Create agents
        self.agents = []
        self._create_agents()

        print(f"\n✓ ABM Model created")
        print(f"   Total agents: {len(self.agents)}")
        print(f"   Simulation days: {self.market.n_steps}")
        if A_optimal is not None:
            print(f"   Optimized Leland A*: {A_optimal:.4f}")
        if A_ml is not None:
            print(f"   ML-Calibrated A*_ml: {A_ml:.4f}")

    def _create_agents(self):
        """Create all agents"""
        config = self.config
        agent_id = 0

        # === FUNDAMENTALISTS (3 types with different aggressiveness) ===

        # Low aggressiveness (conservative)
        for i in range(config.n_fundamentalist_low):
            agent = Fundamentalist(
                agent_id=f"Fund_Low_{i}",
                fundamental_value=self.fundamental_value,
                aggressiveness=config.aggressiveness_low
            )
            self.agents.append(agent)

        # Medium aggressiveness
        for i in range(config.n_fundamentalist_medium):
            agent = Fundamentalist(
                agent_id=f"Fund_Med_{i}",
                fundamental_value=self.fundamental_value,
                aggressiveness=config.aggressiveness_medium
            )
            self.agents.append(agent)

        # High aggressiveness (aggressive)
        for i in range(config.n_fundamentalist_high):
            agent = Fundamentalist(
                agent_id=f"Fund_High_{i}",
                fundamental_value=self.fundamental_value,
                aggressiveness=config.aggressiveness_high
            )
            self.agents.append(agent)

        # === NOISE TRADERS ===
        for i in range(config.n_noise_traders):
            agent = NoiseTrader(
                agent_id=f"Noise_{i}",
                noise_level=config.noise_level
            )
            self.agents.append(agent)

        # === MARKET MAKERS (2: Black-Scholes and Leland) ===
        self.mm_blackscholes = MarketMaker(
            agent_id="MM_BlackScholes",
            strike=self.strike,
            time_to_maturity=config.time_to_maturity,
            risk_free_rate=config.risk_free_rate,
            k_transaction=config.k_transaction,
            rebalance_frequency=config.rebalance_frequency,
            use_leland=False
        )

        self.mm_leland = MarketMaker(
            agent_id="MM_Leland",
            strike=self.strike,
            time_to_maturity=config.time_to_maturity,
            risk_free_rate=config.risk_free_rate,
            k_transaction=config.k_transaction,
            rebalance_frequency=config.rebalance_frequency,
            use_leland=True
        )

        self.agents.append(self.mm_blackscholes)
        self.agents.append(self.mm_leland)

        # === OPTIMIZED LELAND (optional, if A_optimal provided) ===
        self.mm_optimized = None
        if self.A_optimal is not None:
            self.mm_optimized = OptimizedLelandMarketMaker(
                agent_id="MM_OptimizedLeland",
                strike=self.strike,
                time_to_maturity=config.time_to_maturity,
                risk_free_rate=config.risk_free_rate,
                k_transaction=config.k_transaction,
                rebalance_frequency=config.rebalance_frequency,
                A_optimal=self.A_optimal
            )
            self.agents.append(self.mm_optimized)

        # === ML-CALIBRATED LELAND (optional, if A_ml provided) ===
        self.mm_ml = None
        if self.A_ml is not None:
            self.mm_ml = MLCalibratedLelandMarketMaker(
                agent_id="MM_MLCalibrated",
                strike=self.strike,
                time_to_maturity=config.time_to_maturity,
                risk_free_rate=config.risk_free_rate,
                k_transaction=config.k_transaction,
                rebalance_frequency=config.rebalance_frequency,
                A_ml=self.A_ml
            )
            self.agents.append(self.mm_ml)

        # === OPTION TRADERS (2, 3, or 4: counterparties to MMs) ===
        self.option_trader_bs = OptionTrader(
            agent_id="OptionTrader_BS",
            strike=self.strike
        )

        self.option_trader_leland = OptionTrader(
            agent_id="OptionTrader_Leland",
            strike=self.strike
        )

        self.agents.append(self.option_trader_bs)
        self.agents.append(self.option_trader_leland)

        self.option_trader_optimized = None
        if self.A_optimal is not None:
            self.option_trader_optimized = OptionTrader(
                agent_id="OptionTrader_Optimized",
                strike=self.strike
            )
            self.agents.append(self.option_trader_optimized)

        self.option_trader_ml = None
        if self.A_ml is not None:
            self.option_trader_ml = OptionTrader(
                agent_id="OptionTrader_ML",
                strike=self.strike
            )
            self.agents.append(self.option_trader_ml)

    def initialize(self):
        """Initialize: Market Makers sell options"""
        print("\nInitializing ABM...")

        initial_price = self.market.get_price()
        initial_vol = self.market.get_volatility()

        # Convert to float to ensure scalar values
        initial_price = float(initial_price)
        initial_vol = float(initial_vol)

        # MMs sell options, OptionTraders buy them
        bs_premium = self.mm_blackscholes.sell_option(initial_price, initial_vol)
        leland_premium = self.mm_leland.sell_option(initial_price, initial_vol)

        # OptionTraders buy options (counterparty)
        self.option_trader_bs.buy_option(bs_premium)
        self.option_trader_leland.buy_option(leland_premium)

        print(f"  ✓ Black-Scholes MM sold option for ${float(bs_premium):.2f}")
        print(f"    → OptionTrader_BS bought it")
        print(f"  ✓ Leland MM sold option for ${float(leland_premium):.2f}")
        print(f"    → OptionTrader_Leland bought it")

        # If Optimized Leland exists
        if self.mm_optimized is not None:
            optimized_premium = self.mm_optimized.sell_option(initial_price, initial_vol)
            self.option_trader_optimized.buy_option(optimized_premium)
            print(f"  ✓ Optimized Leland MM sold option for ${float(optimized_premium):.2f}")
            print(f"    → OptionTrader_Optimized bought it")

        # If ML-Calibrated Leland exists
        if self.mm_ml is not None:
            ml_premium = self.mm_ml.sell_option(initial_price, initial_vol)
            self.option_trader_ml.buy_option(ml_premium)
            print(f"  ✓ ML-Calibrated MM sold option for ${float(ml_premium):.2f}")
            print(f"    → OptionTrader_ML bought it")

        print(f"  ✓ Strike price: ${float(self.strike):.2f}")

    def run(self):
        """Run full ABM simulation"""
        print(f"\nRunning ABM on real {self.market.real_prices[0]:.2f} → {self.market.real_prices[-1]:.2f} data...")
        print("Progress: ", end='', flush=True)

        while not self.market.is_finished():
            self.step()

            # Progress indicator
            if self.market.current_step % 50 == 0:
                print(f"{self.market.current_step}", end='...', flush=True)

        print(f"{self.market.n_steps} Done!")

        # Finalize
        self.finalize()

    def step(self):
        """One simulation step"""
        # Get market state
        market_state = self.market.get_market_state()

        # All agents act
        for agent in self.agents:
            order = agent.get_order(market_state)

            # Log significant orders
            if abs(order) > 0.01:
                self.market.log_trade(
                    agent.agent_id,
                    'BUY' if order > 0 else 'SELL',
                    abs(order),
                    market_state['price']
                )

        # Market moves to next day (real data)
        self.market.step()

        # Update MMs P&L
        current_price = self.market.get_price()
        self.mm_blackscholes.update_pnl(current_price)
        self.mm_leland.update_pnl(current_price)
        if self.mm_optimized is not None:
            self.mm_optimized.update_pnl(current_price)
        if self.mm_ml is not None:
            self.mm_ml.update_pnl(current_price)

    def finalize(self):
        """Option expiration"""
        print("\nFinalizing (option expiration)...")

        final_price = self.market.get_price()
        option_payoff = max(final_price - self.strike, 0)

        # MMs settle options (pay out)
        self.mm_blackscholes.settle_option(final_price)
        self.mm_leland.settle_option(final_price)
        if self.mm_optimized is not None:
            self.mm_optimized.settle_option(final_price)
        if self.mm_ml is not None:
            self.mm_ml.settle_option(final_price)

        # OptionTraders settle options (receive payoff)
        self.option_trader_bs.settle_option(final_price)
        self.option_trader_leland.settle_option(final_price)
        if self.option_trader_optimized is not None:
            self.option_trader_optimized.settle_option(final_price)
        if self.option_trader_ml is not None:
            self.option_trader_ml.settle_option(final_price)

        print(f"✓ Final stock price: ${final_price:.2f}")
        print(f"✓ Option payoff: ${option_payoff:.2f}")
        print(f"  - OptionTraders received ${option_payoff:.2f} each")
        print(f"  - MarketMakers paid ${option_payoff:.2f} each (minus hedging P&L)")

    def get_results(self):
        """Collect results"""
        results = {
            'config': self.config,
            'ticker': self.config.ticker,
            'real_prices': self.market.real_prices,
            'strike': self.strike,
            'final_price': self.market.get_price(),
            'market_makers': {
                'BlackScholes': {
                    'final_pnl': self.mm_blackscholes.get_pnl(self.market.get_price()),
                    'transaction_costs': self.mm_blackscholes.cumulative_transaction_costs,
                    'pnl_history': self.mm_blackscholes.pnl_history,
                    'num_hedges': len([a for a in self.mm_blackscholes.action_history if a['action'] == 'hedge'])
                },
                'Leland': {
                    'final_pnl': self.mm_leland.get_pnl(self.market.get_price()),
                    'transaction_costs': self.mm_leland.cumulative_transaction_costs,
                    'pnl_history': self.mm_leland.pnl_history,
                    'num_hedges': len([a for a in self.mm_leland.action_history if a['action'] == 'hedge'])
                }
            },
            'option_traders': {
                'BlackScholes': {
                    'final_pnl': self.option_trader_bs.get_pnl(self.market.get_price()),
                    'premium_paid': self.option_trader_bs.option_premium_paid
                },
                'Leland': {
                    'final_pnl': self.option_trader_leland.get_pnl(self.market.get_price()),
                    'premium_paid': self.option_trader_leland.option_premium_paid
                }
            },
            'trades': self.market.trade_history
        }

        # Add Optimized Leland if it exists
        if self.mm_optimized is not None:
            results['market_makers']['OptimizedLeland'] = {
                'final_pnl': self.mm_optimized.get_pnl(self.market.get_price()),
                'transaction_costs': self.mm_optimized.cumulative_transaction_costs,
                'pnl_history': self.mm_optimized.pnl_history,
                'num_hedges': len([a for a in self.mm_optimized.action_history if a['action'] == 'hedge']),
                'A_optimal': self.A_optimal
            }
            results['option_traders']['OptimizedLeland'] = {
                'final_pnl': self.option_trader_optimized.get_pnl(self.market.get_price()),
                'premium_paid': self.option_trader_optimized.option_premium_paid
            }

        # Add ML-Calibrated Leland if it exists
        if self.mm_ml is not None:
            results['market_makers']['MLCalibratedLeland'] = {
                'final_pnl': self.mm_ml.get_pnl(self.market.get_price()),
                'transaction_costs': self.mm_ml.cumulative_transaction_costs,
                'pnl_history': self.mm_ml.pnl_history,
                'num_hedges': len([a for a in self.mm_ml.action_history if a['action'] == 'hedge']),
                'A_ml': self.A_ml
            }
            results['option_traders']['MLCalibratedLeland'] = {
                'final_pnl': self.option_trader_ml.get_pnl(self.market.get_price()),
                'premium_paid': self.option_trader_ml.option_premium_paid
            }

        return results


def run_abm(config: Config):
    """
    Main function to run ABM

    Returns:
    --------
    results dict
    """
    # Download market data
    market_data = download_market_data(
        config.ticker,
        config.start_date,
        config.end_date
    )

    # Create and run model
    model = ABMModel(config, market_data)
    model.initialize()
    model.run()

    # Get results
    results = model.get_results()

    return results, market_data


# Test
if __name__ == "__main__":
    from config import config

    print("Testing ABM Model...")
    config.display()

    results, market_data = run_abm(config)

    print("\n" + "="*60)
    print("ABM RESULTS")
    print("="*60)
    print(f"\nBlack-Scholes:")
    print(f"  Final P&L: ${results['market_makers']['BlackScholes']['final_pnl']:.2f}")
    print(f"  Trans Costs: ${results['market_makers']['BlackScholes']['transaction_costs']:.2f}")

    print(f"\nLeland:")
    print(f"  Final P&L: ${results['market_makers']['Leland']['final_pnl']:.2f}")
    print(f"  Trans Costs: ${results['market_makers']['Leland']['transaction_costs']:.2f}")
