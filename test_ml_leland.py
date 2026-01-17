"""
Test ML-Calibrated Leland Strategy
===================================
Tests Hypothesis H2: ML-Calibrated Leland < Optimized Leland (variance)

Compares 4 strategies:
1. Black-Scholes (baseline)
2. Classical Leland (formula-based A)
3. Optimized Leland (grid-search A*)
4. ML-Calibrated Leland (Bayesian Opt A*_ml)

Tests on Monte Carlo simulations (not ABM, for statistical comparison)
"""

import numpy as np
from config import Config
from optimization import optimize_A_parameter, simulate_hedging_with_A
from ml_optimization import optimize_A_with_ML, simulate_hedging_with_A_ml


def run_monte_carlo_comparison(
    config: Config,
    A_optimal: float,
    A_ml: float,
    n_simulations: int = 50000
):
    """
    Run Monte Carlo with all 4 strategies

    Parameters:
    -----------
    config : Config
        Project configuration
    A_optimal : float
        Optimized A from grid search
    A_ml : float
        ML-calibrated A
    n_simulations : int
        Number of Monte Carlo paths

    Returns:
    --------
    results : dict
        Results for all strategies
    """
    print(f"\n{'='*70}")
    print("  MONTE CARLO COMPARISON: 4 STRATEGIES")
    print(f"{'='*70}")
    print(f"  Simulations: {n_simulations:,}")
    print(f"  Classical Leland A: Calculated from formula")
    print(f"  Optimized Leland A*: {A_optimal:.4f} (grid search)")
    print(f"  ML-Calibrated A*_ml: {A_ml:.4f} (Bayesian Opt)")

    # Parameters
    S0 = 100.0
    K = 100.0
    T = config.time_to_maturity
    r = config.risk_free_rate
    sigma = 0.25  # Assumed volatility
    k = config.k_transaction
    dt = 1 / config.mc_steps_per_year
    n_steps = int(T / dt)

    # Classical Leland A
    A_leland = (k / sigma) * np.sqrt(8 / (np.pi * dt))

    print(f"\nRunning {n_simulations:,} Monte Carlo simulations...")

    # Storage
    results = {
        'BlackScholes': {'errors': [], 'tcs': []},
        'ClassicalLeland': {'errors': [], 'tcs': []},
        'OptimizedLeland': {'errors': [], 'tcs': []},
        'MLCalibratedLeland': {'errors': [], 'tcs': []}
    }

    # Progress tracking
    progress_points = [int(n_simulations * p) for p in [0.25, 0.5, 0.75, 1.0]]

    for sim in range(n_simulations):
        # Generate stock path (GBM)
        S_path = np.zeros(n_steps + 1)
        S_path[0] = S0

        for i in range(n_steps):
            epsilon = np.random.normal(0, 1)
            S_path[i+1] = S_path[i] * np.exp(
                (r - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*epsilon
            )

        # Strategy 1: Black-Scholes (A=0)
        error, tc = simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A=0)
        results['BlackScholes']['errors'].append(error)
        results['BlackScholes']['tcs'].append(tc)

        # Strategy 2: Classical Leland
        error, tc = simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A_leland)
        results['ClassicalLeland']['errors'].append(error)
        results['ClassicalLeland']['tcs'].append(tc)

        # Strategy 3: Optimized Leland
        error, tc = simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A_optimal)
        results['OptimizedLeland']['errors'].append(error)
        results['OptimizedLeland']['tcs'].append(tc)

        # Strategy 4: ML-Calibrated Leland
        error, tc = simulate_hedging_with_A_ml(S_path, K, r, sigma, dt, k, A_ml)
        results['MLCalibratedLeland']['errors'].append(error)
        results['MLCalibratedLeland']['tcs'].append(tc)

        # Progress
        if (sim + 1) in progress_points:
            pct = ((sim + 1) / n_simulations) * 100
            print(f"  Progress: {pct:.0f}% ({sim+1:,}/{n_simulations:,})")

    # Convert to arrays and calculate statistics
    for strategy in results:
        results[strategy]['errors'] = np.array(results[strategy]['errors'])
        results[strategy]['tcs'] = np.array(results[strategy]['tcs'])
        results[strategy]['mean_error'] = np.mean(results[strategy]['errors'])
        results[strategy]['std_error'] = np.std(results[strategy]['errors'])
        results[strategy]['mean_tc'] = np.mean(results[strategy]['tcs'])

    # Store A values
    results['A_values'] = {
        'BlackScholes': 0.0,
        'ClassicalLeland': A_leland,
        'OptimizedLeland': A_optimal,
        'MLCalibratedLeland': A_ml
    }

    print(f"\n✓ Monte Carlo simulations complete!")

    return results


def test_hypothesis_H2(results: dict):
    """
    Test H2: ML-Calibrated Leland has lower variance than Optimized Leland

    Parameters:
    -----------
    results : dict
        Results from run_monte_carlo_comparison

    Returns:
    --------
    hypothesis_confirmed : bool
    """
    print(f"\n{'='*70}")
    print("            HYPOTHESIS H2 TEST")
    print(f"{'='*70}")
    print("H2: ML-Calibrated Leland has lower variance than Optimized Leland")

    std_bs = results['BlackScholes']['std_error']
    std_classical = results['ClassicalLeland']['std_error']
    std_optimized = results['OptimizedLeland']['std_error']
    std_ml = results['MLCalibratedLeland']['std_error']

    print(f"\n  Hedging Error Standard Deviations:")
    print(f"  {'='*66}")
    print(f"  Black-Scholes:           ${std_bs:8.4f}")
    print(f"  Classical Leland:        ${std_classical:8.4f}")
    print(f"  Optimized Leland:        ${std_optimized:8.4f}")
    print(f"  ML-Calibrated Leland:    ${std_ml:8.4f}")

    print(f"\n  Improvements:")
    print(f"  {'='*66}")

    # ML vs Optimized
    improvement_ml_vs_opt = ((std_optimized - std_ml) / std_optimized) * 100
    print(f"  ML vs Optimized:         {improvement_ml_vs_opt:+.2f}%")

    # ML vs Classical
    improvement_ml_vs_classical = ((std_classical - std_ml) / std_classical) * 100
    print(f"  ML vs Classical:         {improvement_ml_vs_classical:+.2f}%")

    # ML vs BS
    improvement_ml_vs_bs = ((std_bs - std_ml) / std_bs) * 100
    print(f"  ML vs Black-Scholes:     {improvement_ml_vs_bs:+.2f}%")

    # Test H2
    hypothesis_confirmed = std_ml < std_optimized

    print(f"\n  {'='*66}")
    if hypothesis_confirmed:
        print(f"  ✅ H2 CONFIRMED: ML-Calibrated Leland reduces variance!")
        print(f"     ML has {improvement_ml_vs_opt:.2f}% lower std than Optimized")
    else:
        print(f"  ❌ H2 NOT CONFIRMED: Optimized Leland has lower variance")
        print(f"     Optimized has {-improvement_ml_vs_opt:.2f}% lower std than ML")

    print(f"  {'='*66}\n")

    return hypothesis_confirmed


def print_summary_table(results: dict):
    """Print summary table of all strategies"""
    print(f"\n{'='*70}")
    print("                    SUMMARY TABLE")
    print(f"{'='*70}")
    print(f"{'Strategy':<20} {'Mean Error':<12} {'Std Error':<12} {'Mean TC':<12}")
    print(f"{'-'*70}")

    strategies = ['BlackScholes', 'ClassicalLeland', 'OptimizedLeland', 'MLCalibratedLeland']
    display_names = ['Black-Scholes', 'Classical Leland', 'Optimized Leland', 'ML-Calibrated']

    for strategy, display_name in zip(strategies, display_names):
        mean_err = results[strategy]['mean_error']
        std_err = results[strategy]['std_error']
        mean_tc = results[strategy]['mean_tc']
        print(f"{display_name:<20} ${mean_err:>10.4f}  ${std_err:>10.4f}  ${mean_tc:>10.2f}")

    print(f"{'='*70}\n")


def main():
    """Main execution"""
    print("\n" + "="*70)
    print(" "*15 + "TESTING ML-CALIBRATED LELAND")
    print(" "*20 + "Hypothesis H2 Test")
    print("="*70)

    # Load config
    config = Config()

    # Parameters for calibration
    S0 = 100.0
    K = 100.0
    T = config.time_to_maturity
    r = config.risk_free_rate
    sigma = 0.25
    k = config.k_transaction
    dt = 1 / config.mc_steps_per_year

    # STEP 1: Calibrate Optimized Leland (Grid Search)
    print("\nSTEP 1: CALIBRATING OPTIMIZED LELAND (Grid Search)")
    print("="*70)
    A_optimal, opt_results = optimize_A_parameter(
        S0, K, T, r, sigma, k, dt,
        n_simulations=3000,
        A_grid=np.linspace(0, 1.5, 16)
    )

    # STEP 2: Calibrate ML Leland (Bayesian Optimization)
    print("\nSTEP 2: CALIBRATING ML-CALIBRATED LELAND (Bayesian Opt)")
    print("="*70)
    A_ml, ml_results = optimize_A_with_ML(
        S0, K, T, r, sigma, k, dt,
        n_initial=10,
        n_iterations=20,
        n_simulations_per_eval=1000,
        acquisition='ei'
    )

    # STEP 3: Monte Carlo Comparison
    print("\nSTEP 3: MONTE CARLO COMPARISON OF ALL 4 STRATEGIES")
    print("="*70)
    mc_results = run_monte_carlo_comparison(
        config, A_optimal, A_ml,
        n_simulations=config.mc_simulations
    )

    # STEP 4: Test H2 and Print Results
    print_summary_table(mc_results)
    hypothesis_confirmed = test_hypothesis_H2(mc_results)

    # Final summary
    print(f"\n{'='*70}")
    print("                    FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"  Optimized Leland A* (Grid):      {A_optimal:.4f}")
    print(f"  ML-Calibrated A*_ml (Bayes):     {A_ml:.4f}")
    print(f"  ML Evaluations:                  {ml_results['n_evaluations']}")
    print(f"  H2 Confirmed:                    {'✅ YES' if hypothesis_confirmed else '❌ NO'}")
    print(f"{'='*70}\n")

    print("✓ ALL TESTS COMPLETE!")
    print("\nNext steps:")
    print("  1. Visualization handled by team member")
    print("  2. Run sensitivity_analysis.py for H3 testing")


if __name__ == "__main__":
    main()
