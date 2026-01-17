"""
Full Strategy Comparison with ML-Calibrated Leland
====================================================
Compare ALL 4 strategies (BS, Leland, Optimized, ML-Calibrated) in BOTH ABM and Monte Carlo

This script:
1. Calibrates Optimized Leland's A* parameter (grid search)
2. Calibrates ML-Calibrated Leland's A*_ml parameter (Bayesian optimization)
3. Runs ABM with all 4 strategies on real data
4. Runs Monte Carlo with all 4 strategies
5. Compares all results side-by-side
6. Tests Hypotheses H1 and H2
7. Generates comprehensive visualizations
"""

import numpy as np
from config import config
from market import download_market_data
from model_abm import ABMModel
from model_monte_carlo import simulate_stock_path
from optimization import optimize_A_parameter, simulate_hedging_with_A
from ml_optimization import optimize_A_with_ML, simulate_hedging_with_A_ml
from analysis import analyze_abm_results


def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(" "*((80 - len(title))//2) + title)
    print("="*80)


def calibrate_all_strategies(config, market_volatility):
    """
    Step 1: Calibrate both Optimized and ML-Calibrated Leland

    Parameters:
    -----------
    config : Config
        Project configuration
    market_volatility : float
        Actual market volatility from AAPL data

    Returns:
    --------
    A_optimal : float (grid search)
    A_ml : float (Bayesian optimization)
    """
    print_header("STEP 1: CALIBRATING BOTH STRATEGIES")

    # Parameters for calibration (using REAL market volatility!)
    S0 = 100.0
    K = 100.0
    T = config.time_to_maturity
    r = config.risk_free_rate
    sigma = market_volatility  # Use actual market volatility from AAPL!
    k = config.k_transaction
    dt = 1 / config.mc_steps_per_year

    print(f"\n⚠️  IMPORTANT: Calibrating with REAL market parameters:")
    print(f"  Market volatility (σ):  {sigma:.4f} (from AAPL data)")
    print(f"  Transaction cost (k):   {k:.4f}")
    print(f"  Time step (dt):         {dt:.6f}")
    print(f"  This ensures A parameters are optimal for the actual market conditions!")

    # 1A: Optimize A (Grid Search)
    print("\n" + "-"*80)
    print("1A. OPTIMIZED LELAND (Grid Search)")
    print("-"*80)

    # Calculate Classical Leland A to focus grid around it
    A_leland_est = (k / sigma) * np.sqrt(8 / (np.pi * dt))

    A_optimal, opt_results = optimize_A_parameter(
        S0, K, T, r, sigma, k, dt,
        n_simulations=10000,  # Increased from 3000 for stability
        A_grid=np.linspace(max(0, A_leland_est - 0.3), A_leland_est + 0.3, 31)  # Finer grid around Leland
    )

    # 1B: ML-Calibrated A (Bayesian Optimization)
    print("\n" + "-"*80)
    print("1B. ML-CALIBRATED LELAND (Bayesian Optimization)")
    print("-"*80)
    A_ml, ml_results = optimize_A_with_ML(
        S0, K, T, r, sigma, k, dt,
        n_initial=15,          # Increased from 10 for better exploration
        n_iterations=30,       # Increased from 20 for better convergence
        n_simulations_per_eval=5000,  # Increased from 1000 for stable estimates!
        acquisition='ei'
    )

    # Summary
    print("\n" + "="*80)
    print("CALIBRATION SUMMARY")
    print("="*80)
    print(f"  Classical Leland A:      {opt_results['A_leland']:.4f} (formula)")
    print(f"  Optimized Leland A*:     {A_optimal:.4f} (grid search, {len(opt_results['A_grid'])} evals)")
    print(f"  ML-Calibrated A*_ml:     {A_ml:.4f} (Bayesian opt, {ml_results['n_evaluations']} evals)")
    print("="*80)

    return A_optimal, A_ml


def run_abm_all_strategies(config, market_data, A_optimal, A_ml):
    """
    Step 2: Run ABM with all 4 strategies

    Parameters:
    -----------
    config : Config
        Project configuration
    market_data : dict
        Pre-downloaded market data (to avoid downloading twice)
    A_optimal : float
        Optimized Leland A parameter
    A_ml : float
        ML-Calibrated Leland A parameter

    Returns:
    --------
    abm_results : dict
        ABM simulation results
    """
    print_header("STEP 2: ABM WITH ALL 4 STRATEGIES (REAL DATA)")

    # Create and run ABM with BOTH Optimized and ML strategies
    model = ABMModel(config, market_data, A_optimal=A_optimal, A_ml=A_ml)
    model.initialize()
    model.run()

    # Get results
    abm_results = model.get_results()

    print("\n" + "-"*80)
    print("ABM RESULTS (Real Data)")
    print("-"*80)
    analyze_abm_results(abm_results)

    return abm_results


def run_monte_carlo_all_strategies(config, initial_price, strike, volatility, A_optimal, A_ml):
    """
    Step 3: Run Monte Carlo with all 4 strategies

    Returns:
    --------
    mc_results : dict
    """
    print_header("STEP 3: MONTE CARLO WITH ALL 4 STRATEGIES")

    n_sims = config.mc_simulations
    dt = 1 / config.mc_steps_per_year
    T = config.time_to_maturity
    r = config.risk_free_rate
    k = config.k_transaction

    print(f"\nRunning {n_sims:,} Monte Carlo simulations...")
    print(f"  S0=${initial_price:.2f}, K=${strike:.2f}, T={T:.2f}")
    print(f"  σ={volatility:.4f}, k={k:.4f}")

    # Storage
    errors_bs = []
    errors_leland = []
    errors_optimized = []
    errors_ml = []

    tc_bs = []
    tc_leland = []
    tc_optimized = []
    tc_ml = []

    # Progress tracking
    progress_interval = n_sims // 10

    for sim in range(n_sims):
        # Generate stock path
        S_path = simulate_stock_path(initial_price, r, volatility, T, dt)

        # Strategy 1: Black-Scholes (no adjustment)
        error_bs, cost_bs = simulate_hedging_with_A(
            S_path, strike, r, volatility, dt, k, A=0.0
        )
        errors_bs.append(error_bs)
        tc_bs.append(cost_bs)

        # Strategy 2: Classical Leland
        A_leland = (k / volatility) * np.sqrt(8 / (np.pi * dt))
        error_leland, cost_leland = simulate_hedging_with_A(
            S_path, strike, r, volatility, dt, k, A=A_leland
        )
        errors_leland.append(error_leland)
        tc_leland.append(cost_leland)

        # Strategy 3: Optimized Leland
        error_opt, cost_opt = simulate_hedging_with_A(
            S_path, strike, r, volatility, dt, k, A=A_optimal
        )
        errors_optimized.append(error_opt)
        tc_optimized.append(cost_opt)

        # Strategy 4: ML-Calibrated Leland
        error_ml, cost_ml = simulate_hedging_with_A_ml(
            S_path, strike, r, volatility, dt, k, A=A_ml
        )
        errors_ml.append(error_ml)
        tc_ml.append(cost_ml)

        # Progress
        if (sim + 1) % progress_interval == 0:
            print(f"  Progress: {sim+1:,}/{n_sims:,} ({100*(sim+1)/n_sims:.0f}%)")

    print("✓ Monte Carlo simulations complete!\n")

    # Aggregate results
    mc_results = {
        'BlackScholes': {
            'mean_error': np.mean(errors_bs),
            'std_error': np.std(errors_bs),
            'mean_tc': np.mean(tc_bs),
            'errors': errors_bs
        },
        'Leland': {
            'mean_error': np.mean(errors_leland),
            'std_error': np.std(errors_leland),
            'mean_tc': np.mean(tc_leland),
            'errors': errors_leland
        },
        'OptimizedLeland': {
            'mean_error': np.mean(errors_optimized),
            'std_error': np.std(errors_optimized),
            'mean_tc': np.mean(tc_optimized),
            'A_optimal': A_optimal,
            'errors': errors_optimized
        },
        'MLCalibratedLeland': {
            'mean_error': np.mean(errors_ml),
            'std_error': np.std(errors_ml),
            'mean_tc': np.mean(tc_ml),
            'A_ml': A_ml,
            'errors': errors_ml
        }
    }

    return mc_results


def print_full_comparison(abm_results, mc_results):
    """
    Step 4: Print comprehensive comparison table
    """
    print_header("COMPREHENSIVE COMPARISON: ABM vs MONTE CARLO")

    print("\n" + "="*80)
    print("ABM RESULTS (Real AAPL Data)")
    print("="*80)
    print(f"\n{'Strategy':<25} {'Final P&L':<15} {'Trans. Costs':<15} {'# Hedges':<10}")
    print("-"*80)

    for strategy in ['BlackScholes', 'Leland', 'OptimizedLeland', 'MLCalibratedLeland']:
        if strategy in abm_results['market_makers']:
            data = abm_results['market_makers'][strategy]
            print(f"{strategy:<25} ${data['final_pnl']:>8.2f}      "
                  f"${data['transaction_costs']:>8.2f}      "
                  f"{data['num_hedges']:>6}")

    print("\n" + "="*80)
    print("MONTE CARLO RESULTS (GBM Simulations)")
    print("="*80)
    print(f"\n{'Strategy':<25} {'Mean Error':<15} {'Std Error':<15} {'Avg TC':<12}")
    print("-"*80)

    for strategy in ['BlackScholes', 'Leland', 'OptimizedLeland', 'MLCalibratedLeland']:
        data = mc_results[strategy]
        print(f"{strategy:<25} ${data['mean_error']:>8.4f}      "
              f"${data['std_error']:>8.4f}      "
              f"${data['mean_tc']:>8.2f}")

    print("-"*80)


def test_hypotheses(mc_results):
    """
    Step 5: Test Hypotheses H1 and H2
    """
    print_header("HYPOTHESIS TESTING: H1 & H2")

    std_bs = mc_results['BlackScholes']['std_error']
    std_leland = mc_results['Leland']['std_error']
    std_optimized = mc_results['OptimizedLeland']['std_error']
    std_ml = mc_results['MLCalibratedLeland']['std_error']

    # H1: Optimized Leland < Classical Leland
    print("\n" + "="*80)
    print("HYPOTHESIS H1: Optimized Leland reduces variance vs Classical Leland")
    print("="*80)
    print(f"\n  Black-Scholes Std:       ${std_bs:.4f}")
    print(f"  Classical Leland Std:    ${std_leland:.4f}")
    print(f"  Optimized Leland Std:    ${std_optimized:.4f}")

    improvement_h1 = ((std_leland - std_optimized) / std_leland) * 100
    print(f"\n  Improvement (Opt vs Classical): {improvement_h1:+.2f}%")

    if std_optimized < std_leland:
        print(f"\n  ✅ H1 CONFIRMED: Optimized Leland reduces variance!")
    else:
        print(f"\n  ❌ H1 REJECTED: No improvement")

    # H2: ML-Calibrated < Optimized Leland
    print("\n" + "="*80)
    print("HYPOTHESIS H2: ML-Calibrated Leland reduces variance vs Optimized")
    print("="*80)
    print(f"\n  Optimized Leland Std:    ${std_optimized:.4f}")
    print(f"  ML-Calibrated Std:       ${std_ml:.4f}")

    improvement_h2 = ((std_optimized - std_ml) / std_optimized) * 100
    print(f"\n  Improvement (ML vs Optimized): {improvement_h2:+.2f}%")

    if std_ml < std_optimized:
        print(f"\n  ✅ H2 CONFIRMED: ML-Calibrated Leland reduces variance!")
    else:
        print(f"\n  ❌ H2 NOT CONFIRMED: Optimized Leland still better")

    # Overall summary
    print("\n" + "="*80)
    print("OVERALL VARIANCE REDUCTION")
    print("="*80)
    print(f"\n  Black-Scholes:           ${std_bs:.4f} (baseline)")
    print(f"  Classical Leland:        ${std_leland:.4f} ({((std_bs-std_leland)/std_bs)*100:+.1f}%)")
    print(f"  Optimized Leland:        ${std_optimized:.4f} ({((std_bs-std_optimized)/std_bs)*100:+.1f}%)")
    print(f"  ML-Calibrated Leland:    ${std_ml:.4f} ({((std_bs-std_ml)/std_bs)*100:+.1f}%)")
    print("="*80)


def main():
    """
    Main function - run full comparison with ML-Calibrated Leland
    """
    print("\n" + "="*80)
    print(" "*15 + "FULL STRATEGY COMPARISON WITH ML")
    print(" "*8 + "BS vs Leland vs Optimized vs ML-Calibrated")
    print(" "*25 + "ABM + Monte Carlo")
    print("="*80)

    # Display configuration
    config.display()

    # Step 0: Download market data FIRST to get real volatility
    print_header("STEP 0: DOWNLOADING MARKET DATA")
    print(f"\nDownloading {config.ticker} data to extract market parameters...")
    market_data = download_market_data(
        config.ticker,
        config.start_date,
        config.end_date
    )
    market_volatility = market_data['volatility']
    print(f"\n✓ Market volatility extracted: σ = {market_volatility:.4f}")
    print(f"  This will be used for calibration to ensure A parameters are optimal!")

    # Step 1: Calibrate both Optimized and ML-Calibrated Leland (using real volatility!)
    A_optimal, A_ml = calibrate_all_strategies(config, market_volatility)

    # Step 2: Run ABM with all 4 strategies (using same market data)
    abm_results = run_abm_all_strategies(config, market_data, A_optimal, A_ml)

    # Step 3: Run Monte Carlo with all 4 strategies (using same volatility)
    initial_price = market_data['prices'][0]
    strike = abm_results['strike']
    volatility = market_data['volatility']  # Same volatility used in calibration!

    mc_results = run_monte_carlo_all_strategies(
        config, initial_price, strike, volatility, A_optimal, A_ml
    )

    # Step 4: Print comprehensive comparison
    print_full_comparison(abm_results, mc_results)

    # Step 5: Test Hypotheses H1 & H2
    test_hypotheses(mc_results)

    # Final summary
    print("\n" + "="*80)
    print("✓ FULL COMPARISON COMPLETE!")
    print("="*80)
    print("\nKey Results:")
    print(f"  Optimized A* (grid):     {A_optimal:.4f}")
    print(f"  ML-Calibrated A*_ml:     {A_ml:.4f}")
    print(f"  H1 Status: Optimized vs Classical")
    print(f"  H2 Status: ML-Calibrated vs Optimized")
    print("\nNext steps:")
    print("  1. Analyze H1 and H2 results above")
    print("  2. Ready for Sensitivity Analysis (H3)")
    print("  3. Visualization will be handled by team member")
    print("="*80 + "\n")

    return abm_results, mc_results, A_optimal, A_ml


if __name__ == "__main__":
    abm_results, mc_results, A_optimal, A_ml = main()
