"""
Multi-Run ABM Analysis
=======================
Run ABM multiple times with different random seeds to get statistical significance

This script:
1. Downloads market data for specified ticker
2. Calibrates A parameters with real market volatility
3. Runs ABM N times with different seeds
4. Collects statistics (mean, std, confidence intervals)
5. Performs statistical tests (t-tests)
6. Exports results to CSV
"""

import numpy as np
import pandas as pd
from scipy import stats
from config import Config
from market import download_market_data
from model_abm import ABMModel
from optimization import optimize_A_parameter
from ml_optimization import optimize_A_with_ML


def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(" "*((80 - len(title))//2) + title)
    print("="*80)


def run_multi_abm(
    config: Config,
    market_data: dict,
    A_optimal: float,
    A_ml: float,
    n_runs: int = 100,
    base_seed: int = 42
):
    """
    Run ABM multiple times with different random seeds

    Parameters:
    -----------
    config : Config
        Project configuration
    market_data : dict
        Market data (prices, volatility)
    A_optimal : float
        Optimized Leland A parameter
    A_ml : float
        ML-Calibrated A parameter
    n_runs : int
        Number of ABM runs (default: 100)
    base_seed : int
        Base random seed (default: 42)

    Returns:
    --------
    results_df : pd.DataFrame
        Results for all runs
    summary_stats : dict
        Statistical summary
    """
    print_header(f"MULTI-RUN ABM ANALYSIS ({n_runs} runs)")

    print(f"\nConfiguration:")
    print(f"  Ticker:           {config.ticker}")
    print(f"  Market Vol:       {market_data['volatility']:.4f}")
    print(f"  Transaction Cost: {config.k_transaction:.4f}")
    print(f"  Runs:             {n_runs}")
    print(f"  Optimized A*:     {A_optimal:.4f}")
    print(f"  ML A*_ml:         {A_ml:.4f}")

    # Storage for all runs
    all_results = {
        'run_id': [],
        'seed': [],
        'BS_pnl': [],
        'Leland_pnl': [],
        'Optimized_pnl': [],
        'ML_pnl': [],
        'BS_tc': [],
        'Leland_tc': [],
        'Optimized_tc': [],
        'ML_tc': [],
        'BS_hedges': [],
        'Leland_hedges': [],
        'Optimized_hedges': [],
        'ML_hedges': []
    }

    print(f"\nRunning {n_runs} ABM simulations...")
    print("Progress: ", end='', flush=True)

    progress_points = [int(n_runs * p) for p in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]

    for run in range(n_runs):
        # Set unique seed for this run
        seed = base_seed + run
        np.random.seed(seed)

        # Create and run ABM
        model = ABMModel(config, market_data, A_optimal, A_ml)
        model.initialize()
        model.run()

        # Get results
        results = model.get_results()

        # Store results
        all_results['run_id'].append(run)
        all_results['seed'].append(seed)

        # P&L
        all_results['BS_pnl'].append(results['market_makers']['BlackScholes']['final_pnl'])
        all_results['Leland_pnl'].append(results['market_makers']['Leland']['final_pnl'])
        all_results['Optimized_pnl'].append(results['market_makers']['OptimizedLeland']['final_pnl'])
        all_results['ML_pnl'].append(results['market_makers']['MLCalibratedLeland']['final_pnl'])

        # Transaction Costs
        all_results['BS_tc'].append(results['market_makers']['BlackScholes']['transaction_costs'])
        all_results['Leland_tc'].append(results['market_makers']['Leland']['transaction_costs'])
        all_results['Optimized_tc'].append(results['market_makers']['OptimizedLeland']['transaction_costs'])
        all_results['ML_tc'].append(results['market_makers']['MLCalibratedLeland']['transaction_costs'])

        # Number of hedges
        all_results['BS_hedges'].append(results['market_makers']['BlackScholes']['num_hedges'])
        all_results['Leland_hedges'].append(results['market_makers']['Leland']['num_hedges'])
        all_results['Optimized_hedges'].append(results['market_makers']['OptimizedLeland']['num_hedges'])
        all_results['ML_hedges'].append(results['market_makers']['MLCalibratedLeland']['num_hedges'])

        # Progress indicator
        if (run + 1) in progress_points:
            pct = ((run + 1) / n_runs) * 100
            print(f"{pct:.0f}%...", end='', flush=True)

    print(" Done!\n")

    # Convert to DataFrame
    results_df = pd.DataFrame(all_results)

    return results_df


def compute_statistics(results_df: pd.DataFrame):
    """
    Compute statistical summary from multi-run results

    Parameters:
    -----------
    results_df : pd.DataFrame
        Results from all runs

    Returns:
    --------
    summary_stats : dict
        Statistical summary for each strategy
    """
    strategies = ['BS', 'Leland', 'Optimized', 'ML']

    summary_stats = {}

    for strategy in strategies:
        pnl_col = f'{strategy}_pnl'
        tc_col = f'{strategy}_tc'

        # Basic statistics
        summary_stats[strategy] = {
            'mean_pnl': results_df[pnl_col].mean(),
            'std_pnl': results_df[pnl_col].std(),
            'median_pnl': results_df[pnl_col].median(),
            'min_pnl': results_df[pnl_col].min(),
            'max_pnl': results_df[pnl_col].max(),
            'mean_tc': results_df[tc_col].mean(),
            'std_tc': results_df[tc_col].std(),
            # Confidence intervals (95%)
            'ci_lower': results_df[pnl_col].mean() - 1.96 * results_df[pnl_col].std() / np.sqrt(len(results_df)),
            'ci_upper': results_df[pnl_col].mean() + 1.96 * results_df[pnl_col].std() / np.sqrt(len(results_df)),
        }

    return summary_stats


def perform_statistical_tests(results_df: pd.DataFrame):
    """
    Perform pairwise t-tests between strategies

    Parameters:
    -----------
    results_df : pd.DataFrame
        Results from all runs

    Returns:
    --------
    test_results : dict
        T-test results for all pairs
    """
    strategies = ['BS', 'Leland', 'Optimized', 'ML']
    test_results = {}

    # All pairwise comparisons
    for i, strat1 in enumerate(strategies):
        for strat2 in strategies[i+1:]:
            pnl1 = results_df[f'{strat1}_pnl']
            pnl2 = results_df[f'{strat2}_pnl']

            # Paired t-test (same runs for both strategies)
            t_stat, p_value = stats.ttest_rel(pnl1, pnl2)

            # Effect size (Cohen's d)
            mean_diff = pnl1.mean() - pnl2.mean()
            pooled_std = np.sqrt((pnl1.std()**2 + pnl2.std()**2) / 2)
            cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

            test_results[f'{strat1}_vs_{strat2}'] = {
                't_statistic': t_stat,
                'p_value': p_value,
                'mean_diff': mean_diff,
                'cohens_d': cohens_d,
                'significant': p_value < 0.05
            }

    return test_results


def print_results(summary_stats: dict, test_results: dict):
    """Print formatted results"""

    print_header("STATISTICAL SUMMARY")

    print(f"\n{'Strategy':<15} {'Mean P&L':<15} {'Std P&L':<15} {'95% CI':<30} {'Mean TC':<12}")
    print("-"*90)

    for strategy in ['BS', 'Leland', 'Optimized', 'ML']:
        stats_dict = summary_stats[strategy]
        ci = f"[{stats_dict['ci_lower']:.2f}, {stats_dict['ci_upper']:.2f}]"
        print(f"{strategy:<15} ${stats_dict['mean_pnl']:>8.2f}      "
              f"${stats_dict['std_pnl']:>8.2f}      "
              f"{ci:<30} "
              f"${stats_dict['mean_tc']:>8.2f}")

    print("\n" + "="*90)

    # Statistical tests
    print_header("PAIRWISE STATISTICAL TESTS (Paired t-tests)")

    print(f"\n{'Comparison':<25} {'Mean Diff':<15} {'t-stat':<12} {'p-value':<12} {'Significant':<15}")
    print("-"*90)

    for comparison, results in test_results.items():
        sig = "✓ YES" if results['significant'] else "✗ NO"
        print(f"{comparison:<25} ${results['mean_diff']:>10.2f}     "
              f"{results['t_statistic']:>8.4f}    "
              f"{results['p_value']:>8.6f}    "
              f"{sig:<15}")

    print("\n" + "="*90)

    # Key findings
    print_header("KEY FINDINGS")

    # Best strategy
    best_strategy = min(summary_stats.items(), key=lambda x: x[1]['mean_pnl'])
    print(f"\n✓ Best Strategy: {best_strategy[0]}")
    print(f"  Mean P&L: ${best_strategy[1]['mean_pnl']:.2f} ± ${best_strategy[1]['std_pnl']:.2f}")

    # Leland vs BS
    leland_vs_bs = test_results['BS_vs_Leland']
    savings = -leland_vs_bs['mean_diff']
    pct_savings = (savings / abs(summary_stats['BS']['mean_pnl'])) * 100 if summary_stats['BS']['mean_pnl'] != 0 else 0

    print(f"\n✓ Leland vs Black-Scholes:")
    print(f"  Average savings: ${savings:.2f} ({pct_savings:.1f}%)")
    print(f"  Statistically significant: {'YES' if leland_vs_bs['significant'] else 'NO'} (p={leland_vs_bs['p_value']:.4f})")

    # Optimized vs Leland
    if 'Leland_vs_Optimized' in test_results:
        opt_vs_leland = test_results['Leland_vs_Optimized']
        improvement = -opt_vs_leland['mean_diff']

        print(f"\n✓ Optimized vs Classical Leland:")
        print(f"  Average improvement: ${improvement:.2f}")
        print(f"  Statistically significant: {'YES' if opt_vs_leland['significant'] else 'NO'} (p={opt_vs_leland['p_value']:.4f})")

    # ML vs Optimized
    if 'Optimized_vs_ML' in test_results:
        ml_vs_opt = test_results['Optimized_vs_ML']
        improvement = -ml_vs_opt['mean_diff']

        print(f"\n✓ ML-Calibrated vs Optimized:")
        print(f"  Average improvement: ${improvement:.2f}")
        print(f"  Statistically significant: {'YES' if ml_vs_opt['significant'] else 'NO'} (p={ml_vs_opt['p_value']:.4f})")

    print("\n" + "="*90)


def export_results(results_df: pd.DataFrame, summary_stats: dict, test_results: dict, ticker: str):
    """Export results to CSV files"""

    # Ensure output_csv directory exists
    import os
    os.makedirs('output_csv', exist_ok=True)

    # All runs
    filename_runs = f'output_csv/multi_abm_runs_{ticker}.csv'
    results_df.to_csv(filename_runs, index=False)
    print(f"\n✓ Individual runs exported to: {filename_runs}")

    # Summary statistics
    summary_df = pd.DataFrame(summary_stats).T
    filename_summary = f'output_csv/multi_abm_summary_{ticker}.csv'
    summary_df.to_csv(filename_summary)
    print(f"✓ Summary statistics exported to: {filename_summary}")

    # Statistical tests
    test_df = pd.DataFrame(test_results).T
    filename_tests = f'output_csv/multi_abm_tests_{ticker}.csv'
    test_df.to_csv(filename_tests)
    print(f"✓ Statistical tests exported to: {filename_tests}")


def main(ticker: str = None, n_runs: int = 100):
    """
    Main function - Run multi-ABM analysis

    Parameters:
    -----------
    ticker : str
        Stock ticker (default: use config.ticker)
    n_runs : int
        Number of ABM runs (default: 100)
    """
    # Load config
    config = Config()

    # Override ticker if provided
    if ticker is not None:
        config.ticker = ticker

    print("\n" + "="*80)
    print(" "*20 + f"MULTI-RUN ABM ANALYSIS: {config.ticker}")
    print(" "*25 + f"{n_runs} Monte Carlo Runs")
    print("="*80)

    # Download market data
    print_header("DOWNLOADING MARKET DATA")
    print(f"\nTicker: {config.ticker}")
    print(f"Period: {config.start_date} to {config.end_date}")

    market_data = download_market_data(
        config.ticker,
        config.start_date,
        config.end_date
    )

    market_volatility = market_data['volatility']
    print(f"\n✓ Market volatility: σ = {market_volatility:.4f}")

    # Calibrate strategies
    print_header("CALIBRATING STRATEGIES")

    S0 = 100.0
    K = 100.0
    T = config.time_to_maturity
    r = config.risk_free_rate
    sigma = market_volatility
    k = config.k_transaction
    dt = 1 / config.mc_steps_per_year

    # Classical Leland A
    A_leland = (k / sigma) * np.sqrt(8 / (np.pi * dt))

    print(f"\nCalibrating with market parameters:")
    print(f"  σ = {sigma:.4f} (from {config.ticker} data)")
    print(f"  k = {k:.4f}")
    print(f"  dt = {dt:.6f}")

    # Optimized Leland (grid search)
    print(f"\nOptimizing Leland A (grid search)...")
    A_optimal, opt_results = optimize_A_parameter(
        S0, K, T, r, sigma, k, dt,
        n_simulations=10000,
        A_grid=np.linspace(max(0, A_leland - 0.3), A_leland + 0.3, 31)
    )

    # ML-Calibrated Leland (Bayesian optimization)
    print(f"\nOptimizing Leland A (Bayesian)...")
    A_ml, ml_results = optimize_A_with_ML(
        S0, K, T, r, sigma, k, dt,
        n_initial=15,
        n_iterations=30,
        n_simulations_per_eval=5000,
        acquisition='ei'
    )

    print(f"\n✓ Calibration complete:")
    print(f"  Classical Leland A:  {A_leland:.4f}")
    print(f"  Optimized A*:        {A_optimal:.4f}")
    print(f"  ML-Calibrated A*_ml: {A_ml:.4f}")

    # Run multi-ABM
    results_df = run_multi_abm(
        config, market_data, A_optimal, A_ml,
        n_runs=n_runs
    )

    # Compute statistics
    summary_stats = compute_statistics(results_df)

    # Statistical tests
    test_results = perform_statistical_tests(results_df)

    # Print results
    print_results(summary_stats, test_results)

    # Export results
    export_results(results_df, summary_stats, test_results, config.ticker)

    print_header("ANALYSIS COMPLETE")

    print(f"\n✓ Completed {n_runs} ABM runs for {config.ticker}")
    print(f"✓ Results exported to CSV files")
    print(f"✓ Statistical significance tested")

    return results_df, summary_stats, test_results


if __name__ == "__main__":
    import sys

    # Command line arguments
    ticker = sys.argv[1] if len(sys.argv) > 1 else None
    n_runs = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    # Run analysis
    results_df, summary_stats, test_results = main(ticker=ticker, n_runs=n_runs)
