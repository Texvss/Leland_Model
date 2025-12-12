"""
ML-Calibrated Leland Strategy
==============================
Machine Learning-based optimization of Leland's A parameter

Key Improvement over Optimized Leland:
- Optimized Leland: Grid search (exhaustive, many simulations)
- ML-Calibrated Leland: Bayesian Optimization with Gaussian Process
  → Adaptive, efficient, fewer simulations needed

Hypothesis H2: ML-Calibrated Leland < Optimized Leland (variance)
"""

import numpy as np
from typing import Tuple, Dict
from black_scholes import BlackScholesUtils


def simulate_hedging_with_A_ml(
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
    (Same as optimization.py but kept separate for clarity)

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
        Leland's adjustment parameter

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


def optimize_A_with_ML(
    S0: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    k: float,
    dt: float,
    n_initial: int = 10,
    n_iterations: int = 20,
    n_simulations_per_eval: int = 1000,
    A_bounds: Tuple[float, float] = (0.0, 2.0),
    acquisition: str = 'ei'
) -> Tuple[float, Dict]:
    """
    Optimize A parameter using Bayesian Optimization with Gaussian Process

    Algorithm:
    1. Initial exploration: Random sampling (n_initial points)
    2. Exploitation/Exploration: GP-guided search (n_iterations)
    3. For each A candidate:
       - Run n_simulations_per_eval Monte Carlo paths
       - Calculate mean and std of hedging errors
       - GP learns objective function
       - Acquisition function suggests next A to try

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
    n_initial : int
        Number of random initial points (exploration)
    n_iterations : int
        Number of BO iterations (exploitation)
    n_simulations_per_eval : int
        Monte Carlo sims per A evaluation
    A_bounds : tuple
        (min_A, max_A)
    acquisition : str
        Acquisition function: 'ei' (Expected Improvement) or 'ucb' (Upper Confidence Bound)

    Returns:
    --------
    A_ml : float
        ML-optimized A parameter
    results : dict
        Optimization details
    """
    try:
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel
        from scipy.stats import norm
    except ImportError:
        print("\n⚠️  sklearn not installed. Install with:")
        print("   pip install scikit-learn scipy")
        print("\nFalling back to simple grid search...")
        return _fallback_optimization(S0, K, T, r, sigma, k, dt)

    print(f"\n{'='*70}")
    print(" "*15 + "ML-CALIBRATED LELAND OPTIMIZATION")
    print(" "*20 + "(Bayesian Optimization + GP)")
    print(f"{'='*70}")
    print(f"\nParameters:")
    print(f"  S0={S0:.2f}, K={K:.2f}, T={T:.2f}, σ={sigma:.4f}")
    print(f"  k={k:.4f}, dt={dt:.6f}")
    print(f"  Initial exploration: {n_initial} points")
    print(f"  BO iterations: {n_iterations}")
    print(f"  MC sims per eval: {n_simulations_per_eval:,}")
    print(f"  Acquisition: {acquisition.upper()}")

    # Classical Leland A for reference
    A_leland = (k / sigma) * np.sqrt(8 / (np.pi * dt))
    print(f"\n  Classical Leland A: {A_leland:.4f}")

    # Storage
    A_tested = []
    std_errors_tested = []
    mean_errors_tested = []

    def evaluate_A(A: float) -> float:
        """
        Evaluate objective function at A
        Returns: std of hedging error (lower is better)
        """
        errors = []

        for _ in range(n_simulations_per_eval):
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
            error, _ = simulate_hedging_with_A_ml(
                S_path, K, r, sigma, dt, k, A
            )
            errors.append(error)

        mean_err = np.mean(errors)
        std_err = np.std(errors)

        # Store
        A_tested.append(A)
        mean_errors_tested.append(mean_err)
        std_errors_tested.append(std_err)

        return std_err

    # PHASE 1: Initial Random Exploration
    print(f"\nPhase 1: Initial Random Exploration ({n_initial} points)...")
    X_train = []
    y_train = []

    for i in range(n_initial):
        A = np.random.uniform(A_bounds[0], A_bounds[1])
        std_error = evaluate_A(A)
        X_train.append([A])
        y_train.append(std_error)
        print(f"  {i+1}/{n_initial} | A={A:.4f}, Std={std_error:.4f}")

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    # PHASE 2: Bayesian Optimization with Gaussian Process
    print(f"\nPhase 2: Bayesian Optimization ({n_iterations} iterations)...")

    # Define GP kernel
    kernel = ConstantKernel(1.0) * RBF(length_scale=0.1)
    gp = GaussianProcessRegressor(
        kernel=kernel,
        n_restarts_optimizer=10,
        alpha=1e-6,
        normalize_y=True
    )

    for iteration in range(n_iterations):
        # Fit GP to current data
        gp.fit(X_train, y_train)

        # Acquisition function: Find next A to evaluate
        A_candidates = np.linspace(A_bounds[0], A_bounds[1], 100).reshape(-1, 1)

        # Predict with GP
        mu, sigma_gp = gp.predict(A_candidates, return_std=True)

        if acquisition == 'ei':
            # Expected Improvement
            best_y = np.min(y_train)
            Z = (best_y - mu) / (sigma_gp + 1e-9)
            ei = (best_y - mu) * norm.cdf(Z) + sigma_gp * norm.pdf(Z)
            next_idx = np.argmax(ei)
        else:  # ucb
            # Upper Confidence Bound (for minimization: lower bound)
            kappa = 2.0
            ucb = mu - kappa * sigma_gp
            next_idx = np.argmin(ucb)

        A_next = A_candidates[next_idx, 0]

        # Evaluate
        std_error = evaluate_A(A_next)

        # Update training data
        X_train = np.vstack([X_train, [[A_next]]])
        y_train = np.append(y_train, std_error)

        print(f"  {iteration+1}/{n_iterations} | A={A_next:.4f}, Std={std_error:.4f} "
              f"(Best so far: {np.min(y_train):.4f})")

    # Find best A
    best_idx = np.argmin(std_errors_tested)
    A_ml = A_tested[best_idx]

    print(f"\n{'='*70}")
    print(f"✓ ML OPTIMIZATION COMPLETE")
    print(f"{'='*70}")
    print(f"\n  ML-Optimal A*:       {A_ml:.4f}")
    print(f"  ML Std Error:        {std_errors_tested[best_idx]:.4f}")
    print(f"  Mean Error:          {mean_errors_tested[best_idx]:.4f}")
    print(f"  Total evaluations:   {len(A_tested)}")

    # Compare with Classical Leland
    # Find closest tested A to A_leland
    leland_idx = np.argmin(np.abs(np.array(A_tested) - A_leland))
    print(f"\n  Classical Leland A:  {A_tested[leland_idx]:.4f}")
    print(f"  Classical Std Error: {std_errors_tested[leland_idx]:.4f}")

    if std_errors_tested[leland_idx] > 0:
        improvement = (1 - std_errors_tested[best_idx]/std_errors_tested[leland_idx])*100
        print(f"  Improvement:         {improvement:.2f}%")

    print(f"{'='*70}\n")

    results = {
        'A_ml': A_ml,
        'A_tested': np.array(A_tested),
        'mean_errors': np.array(mean_errors_tested),
        'std_errors': np.array(std_errors_tested),
        'best_idx': best_idx,
        'A_leland': A_leland,
        'n_evaluations': len(A_tested),
        'method': 'Bayesian Optimization + GP'
    }

    return A_ml, results


def _fallback_optimization(S0, K, T, r, sigma, k, dt):
    """Fallback to simple grid search if sklearn not available"""
    from optimization import optimize_A_parameter

    print("Using grid search fallback (install sklearn for ML optimization)")
    A_grid = np.linspace(0, 2.0, 21)
    A_optimal, opt_results = optimize_A_parameter(S0, K, T, r, sigma, k, dt,
                                                    n_simulations=3000, A_grid=A_grid)

    # Convert to ML-compatible results format
    ml_results = {
        'A_ml': A_optimal,  # Use A_optimal as A_ml
        'A_tested': opt_results['A_grid'],
        'mean_errors': opt_results['mean_errors'],
        'std_errors': opt_results['std_errors'],
        'best_idx': opt_results['optimal_idx'],
        'A_leland': opt_results['A_leland'],
        'n_evaluations': len(opt_results['A_grid']),  # Add this key
        'method': 'Grid Search (sklearn not available)'
    }

    return A_optimal, ml_results


# Test
if __name__ == "__main__":
    print("Testing ML-Calibrated Leland Optimization...")

    # Test parameters
    S0 = 100.0
    K = 100.0
    T = 1.0
    r = 0.05
    sigma = 0.25
    k = 0.01
    dt = 1/252  # Daily

    # Run ML optimization
    A_ml, results = optimize_A_with_ML(
        S0, K, T, r, sigma, k, dt,
        n_initial=8,
        n_iterations=15,
        n_simulations_per_eval=500,  # Reduced for testing
        acquisition='ei'
    )

    print(f"\n✓ ML-Optimal A found: {A_ml:.4f}")
    print("✓ ML Optimization module working!")
