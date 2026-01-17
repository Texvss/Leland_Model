"""
Optimized Leland Strategy
==========================
Data-driven optimization of Leland's A parameter

Instead of using fixed A = (k/σ)*sqrt(8/(π*dt)),
we find optimal A* by minimizing hedging error variance
"""

import numpy as np
from typing import Tuple, List
from black_scholes import BlackScholesUtils


def simulate_hedging_with_A(
    S_path: np.ndarray,
    K: float,
    r: float,
    sigma: float,
    dt: float,
    k: float,
    A: float
) -> Tuple[float, float]:
    """
    Simulate option hedging with given A parameter

    Parameters:
    -----------
    S_path : np.ndarray
        Stock price path
    K : float
        Strike price
    r : float
        Risk-free rate
    sigma : float
        True volatility
    dt : float
        Time step
    k : float
        Transaction cost rate
    A : float
        Leland's adjustment parameter (to be optimized)

    Returns:
    --------
    hedging_error : float
        Final P&L (replication error)
    total_tc : float
        Total transaction costs
    """
    n_steps = len(S_path) - 1
    T_total = n_steps * dt

    bs = BlackScholesUtils()

    # Modified volatility with parameter A
    sigma_hedge = sigma * np.sqrt(max(1 + A, 0.01))

    # Initialize portfolio
    portfolio_value = 0.0
    shares_held = 0.0
    total_tc = 0.0

    # Hedging loop
    for i in range(n_steps):
        S = S_path[i]
        T_remain = T_total - i * dt

        if T_remain <= 0:
            break

        # Target delta with modified volatility
        target_delta = bs.delta(S, K, T_remain, r, sigma_hedge)

        # Rebalance
        shares_to_trade = target_delta - shares_held
        transaction_cost = k * abs(shares_to_trade) * S

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


def optimize_A_parameter(
    S0: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    k: float,
    dt: float,
    n_simulations: int = 5000,
    A_grid: np.ndarray = None
) -> Tuple[float, dict]:
    """
    Find optimal A parameter by minimizing hedging error variance

    Parameters:
    -----------
    S0 : float
        Initial stock price
    K : float
        Strike price
    T : float
        Time to maturity
    r : float
        Risk-free rate
    sigma : float
        Volatility
    k : float
        Transaction cost rate
    dt : float
        Time step
    n_simulations : int
        Number of Monte Carlo paths
    A_grid : np.ndarray, optional
        Grid of A values to test. If None, uses default.

    Returns:
    --------
    A_optimal : float
        Optimal A parameter
    results : dict
        Dictionary with optimization details
    """
    print(f"\n{'='*70}")
    print(" "*20 + "OPTIMIZING LELAND'S A PARAMETER")
    print(f"{'='*70}")
    print(f"\nParameters:")
    print(f"  S0={S0:.2f}, K={K:.2f}, T={T:.2f}, σ={sigma:.4f}")
    print(f"  k={k:.4f}, dt={dt:.6f}")
    print(f"  Simulations: {n_simulations:,}")

    # Default A grid
    if A_grid is None:
        # Classical Leland's A for reference
        A_leland = (k / sigma) * np.sqrt(8 / (np.pi * dt))
        print(f"\n  Classical Leland A: {A_leland:.4f}")

        # Create grid around classical value
        A_grid = np.linspace(0.0, min(2.0, 3 * A_leland), 21)

    print(f"  Testing A ∈ [{A_grid[0]:.3f}, {A_grid[-1]:.3f}] ({len(A_grid)} points)")

    # Storage for results
    mean_errors = []
    std_errors = []
    mean_tcs = []

    print(f"\nRunning optimization...")

    # Test each A value
    for idx, A in enumerate(A_grid):
        errors = []
        tcs = []

        # Monte Carlo simulations
        for sim in range(n_simulations):
            # Generate stock path (GBM)
            n_steps = int(T / dt)
            S_path = np.zeros(n_steps + 1)
            S_path[0] = S0

            for i in range(n_steps):
                epsilon = np.random.normal(0, 1)
                S_path[i+1] = S_path[i] * np.exp(
                    (r - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*epsilon
                )

            # Hedge with this A
            error, tc = simulate_hedging_with_A(
                S_path, K, r, sigma, dt, k, A
            )
            errors.append(error)
            tcs.append(tc)

        # Statistics
        mean_errors.append(np.mean(errors))
        std_errors.append(np.std(errors))
        mean_tcs.append(np.mean(tcs))

        # Progress
        if (idx + 1) % 5 == 0 or idx == len(A_grid) - 1:
            print(f"  Progress: {idx+1}/{len(A_grid)} | "
                  f"Current A={A:.3f}, Std={std_errors[-1]:.4f}")

    # Find optimal A (minimize std)
    optimal_idx = np.argmin(std_errors)
    A_optimal = A_grid[optimal_idx]

    print(f"\n{'='*70}")
    print(f"✓ OPTIMIZATION COMPLETE")
    print(f"{'='*70}")
    print(f"\n  Optimal A*:          {A_optimal:.4f}")
    print(f"  Optimal Std Error:   {std_errors[optimal_idx]:.4f}")
    print(f"  Mean Error:          {mean_errors[optimal_idx]:.4f}")
    print(f"  Mean Trans. Cost:    {mean_tcs[optimal_idx]:.4f}")

    # Classical Leland for comparison
    A_leland_idx = np.argmin(np.abs(A_grid - (k / sigma) * np.sqrt(8 / (np.pi * dt))))
    print(f"\n  Classical Leland A:  {A_grid[A_leland_idx]:.4f}")
    print(f"  Classical Std Error: {std_errors[A_leland_idx]:.4f}")
    print(f"  Improvement:         {(1 - std_errors[optimal_idx]/std_errors[A_leland_idx])*100:.2f}%")

    print(f"{'='*70}\n")

    results = {
        'A_optimal': A_optimal,
        'A_grid': A_grid,
        'mean_errors': np.array(mean_errors),
        'std_errors': np.array(std_errors),
        'mean_tcs': np.array(mean_tcs),
        'optimal_idx': optimal_idx,
        'A_leland': (k / sigma) * np.sqrt(8 / (np.pi * dt)),
        'improvement_pct': (1 - std_errors[optimal_idx]/std_errors[A_leland_idx])*100
    }

    return A_optimal, results


# Test
if __name__ == "__main__":
    print("Testing Optimized Leland...")

    # Test parameters (similar to project)
    S0 = 100.0
    K = 100.0
    T = 1.0
    r = 0.05
    sigma = 0.25
    k = 0.01
    dt = 1/252  # Daily

    # Optimize A
    A_optimal, results = optimize_A_parameter(
        S0, K, T, r, sigma, k, dt,
        n_simulations=1000,  # Reduced for testing
        A_grid=np.linspace(0, 1.0, 11)
    )

    print(f"\n✓ Optimal A found: {A_optimal:.4f}")
    print("✓ Optimization module working!")
