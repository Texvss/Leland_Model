"""
Monte Carlo Model for Black-Scholes
====================================
Traditional Monte Carlo simulation for comparison with ABM
"""

import numpy as np
from config import Config
from black_scholes import BlackScholesUtils


def simulate_stock_path(S0, mu, sigma, T, dt):
    """
    Simulate one stock price path using GBM

    dS = μS·dt + σS·dW
    """
    n_steps = int(T / dt)
    S = np.zeros(n_steps + 1)
    S[0] = S0

    for i in range(n_steps):
        epsilon = np.random.normal(0, 1)
        S[i+1] = S[i] * np.exp((mu - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*epsilon)

    return S


def simulate_hedging(S_path, K, r, sigma, dt, lambda_tc, strategy='BS'):
    """
    Simulate option hedging along a stock path

    strategy: 'BS' or 'Leland'
    """
    n_steps = len(S_path) - 1
    T_total = n_steps * dt

    bs = BlackScholesUtils()

    # Choose hedging volatility
    if strategy == 'Leland':
        sigma_hedge = bs.leland_volatility(sigma, lambda_tc, dt, short_gamma=True)
    else:
        sigma_hedge = sigma

    # Initialize portfolio
    portfolio_value = 0.0
    shares_held = 0.0
    total_tc = 0.0

    # Hedging loop
    for i in range(n_steps):
        S = S_path[i]
        T_remain = T_total - i*dt

        # Target delta
        target_delta = bs.delta(S, K, T_remain, r, sigma_hedge)

        # Rebalance
        shares_to_trade = target_delta - shares_held
        transaction_cost = lambda_tc * abs(shares_to_trade) * S

        # Update portfolio
        portfolio_value -= shares_to_trade * S
        portfolio_value -= transaction_cost
        portfolio_value *= np.exp(r * dt)

        shares_held = target_delta
        total_tc += transaction_cost

    # At expiration
    S_final = S_path[-1]
    option_payoff = max(S_final - K, 0)

    # Close position
    portfolio_value += shares_held * S_final
    portfolio_value -= option_payoff

    return portfolio_value, total_tc


def run_monte_carlo(config: Config, initial_price: float, strike: float, volatility: float):
    """
    Run Monte Carlo simulation

    Parameters:
    -----------
    config: Config object
    initial_price: float - S0
    strike: float - K
    volatility: float - σ (realized from data)

    Returns:
    --------
    results dict
    """
    print("\n" + "="*60)
    print("MONTE CARLO SIMULATION")
    print("="*60)

    print(f"\nParameters:")
    print(f"  Initial Price (S0): ${initial_price:.2f}")
    print(f"  Strike (K):         ${strike:.2f}")
    print(f"  Volatility (σ):     {volatility*100:.2f}%")
    print(f"  Time to Maturity:   {config.time_to_maturity} year")
    print(f"  Transaction Cost:   {config.k_transaction*100:.2f}%")
    print(f"  Simulations:        {config.mc_simulations:,}")

    # Simulation parameters
    T = config.time_to_maturity
    dt = 1 / config.mc_steps_per_year
    n_steps = int(T / dt)

    print(f"  Steps per path:     {n_steps}")
    print(f"\nRunning simulations...")

    # Storage
    errors_BS = []
    errors_Leland = []
    tc_BS = []
    tc_Leland = []

    # Run simulations
    for sim in range(config.mc_simulations):
        # Generate stock path
        S_path = simulate_stock_path(
            initial_price, config.risk_free_rate, volatility, T, dt
        )

        # Test Black-Scholes
        error_bs, tc_bs = simulate_hedging(
            S_path, strike, config.risk_free_rate, volatility,
            dt, config.k_transaction, 'BS'
        )
        errors_BS.append(error_bs)
        tc_BS.append(tc_bs)

        # Test Leland
        error_leland, tc_leland = simulate_hedging(
            S_path, strike, config.risk_free_rate, volatility,
            dt, config.k_transaction, 'Leland'
        )
        errors_Leland.append(error_leland)
        tc_Leland.append(tc_leland)

        # Progress
        if (sim + 1) % 10000 == 0:
            print(f"  Completed {sim+1:,}/{config.mc_simulations:,}")

    print("✓ Monte Carlo complete!\n")

    # Calculate statistics
    results = {
        'config': config,
        'initial_price': initial_price,
        'strike': strike,
        'volatility': volatility,
        'strategies': {
            'BlackScholes': {
                'mean_pnl': np.mean(errors_BS),
                'std_pnl': np.std(errors_BS),
                'mean_tc': np.mean(tc_BS),
                'errors': errors_BS
            },
            'Leland': {
                'mean_pnl': np.mean(errors_Leland),
                'std_pnl': np.std(errors_Leland),
                'mean_tc': np.mean(tc_Leland),
                'errors': errors_Leland
            }
        }
    }

    return results


def print_mc_results(results):
    """Print Monte Carlo results"""
    print("="*70)
    print(" "*20 + "MONTE CARLO RESULTS")
    print("="*70)

    print(f"\n{'Strategy':<20} {'Mean P&L':<15} {'Std Dev':<15} {'Avg Trans Cost':<15}")
    print("-"*70)

    for strategy in ['BlackScholes', 'Leland']:
        data = results['strategies'][strategy]
        print(f"{strategy:<20} ${data['mean_pnl']:>8.2f}      "
              f"${data['std_pnl']:>8.2f}      "
              f"${data['mean_tc']:>8.2f}")

    print("-"*70)

    # Comparison
    bs_mean = results['strategies']['BlackScholes']['mean_pnl']
    leland_mean = results['strategies']['Leland']['mean_pnl']
    diff = leland_mean - bs_mean

    bs_std = results['strategies']['BlackScholes']['std_pnl']
    leland_std = results['strategies']['Leland']['std_pnl']
    std_diff = leland_std - bs_std

    print(f"\nImprovement (Leland vs BS):")
    print(f"  Better return:    ${diff:>8.2f} ({diff/abs(bs_mean)*100:+.1f}%)")
    print(f"  Risk reduction:   ${std_diff:>8.2f} ({std_diff/bs_std*100:+.1f}%)")

    print("="*70 + "\n")


# Test
if __name__ == "__main__":
    from config import config

    print("Testing Monte Carlo Model...")
    config.display()

    # Use typical parameters
    S0 = 100
    K = 100
    sigma = 0.25

    results = run_monte_carlo(config, S0, K, sigma)
    print_mc_results(results)
