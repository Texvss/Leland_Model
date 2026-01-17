"""
Sensitivity Analysis (Hypothesis H3)
=====================================
Test robustness of all 4 strategies to parameter changes

Research Question (H3):
How robust are the strategies to changes in:
1. Transaction cost rate (k)
2. Rebalancing frequency (Δt)

Method:
- Vary k ∈ {0.005, 0.01, 0.015, 0.02}
- Vary Δt ∈ {1/252, 1/126, 1/63, 1/21} (daily, 2-day, 4-day, 12-day)
- For each (k, Δt) combination:
  * Recalibrate A_optimal and A_ml
  * Run Monte Carlo (10,000 sims per combination for speed)
  * Compute std_error for all 4 strategies
- Analyze:
  * Do H1 and H2 still hold across all parameter combinations?
  * How sensitive is performance to k and Δt?
  * Which strategy is most robust?
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from black_scholes import BlackScholesUtils
from optimization import optimize_A_parameter, simulate_hedging_with_A
from ml_optimization import optimize_A_with_ML, simulate_hedging_with_A_ml
from model_monte_carlo import simulate_stock_path


def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(" "*((80 - len(title))//2) + title)
    print("="*80)


def run_single_parameter_set(
    k: float,
    dt: float,
    S0: float = 100.0,
    K: float = 100.0,
    T: float = 1.0,
    r: float = 0.05,
    sigma: float = 0.25,
    n_simulations: int = 10000,
    recalibrate: bool = True
) -> Dict:
    """
    Run all 4 strategies for a single (k, Δt) parameter combination

    Parameters:
    -----------
    k : float
        Transaction cost rate
    dt : float
        Time step (rebalancing frequency)
    S0, K, T, r, sigma : float
        Option parameters
    n_simulations : int
        Number of Monte Carlo paths
    recalibrate : bool
        If True, recalibrate A_optimal and A_ml for this (k, dt)
        If False, use classical Leland formula for comparison

    Returns:
    --------
    results : dict
        Results for all 4 strategies
    """
    print(f"\nRunning k={k:.4f}, dt={dt:.6f} ({int(1/dt)} steps/year)...")

    # Classical Leland A (always calculated)
    A_leland = (k / sigma) * np.sqrt(8 / (np.pi * dt))

    if recalibrate:
        # Calibrate Optimized Leland (grid search)
        print(f"  Calibrating Optimized Leland (grid search)...")
        A_optimal, _ = optimize_A_parameter(
            S0, K, T, r, sigma, k, dt,
            n_simulations=2000,
            A_grid=np.linspace(0, min(2.0, 1.5*A_leland), 11)  # Fewer points for speed
        )

        # Calibrate ML-Calibrated Leland (Bayesian optimization)
        print(f"  Calibrating ML-Calibrated Leland (Bayesian)...")
        A_ml, _ = optimize_A_with_ML(
            S0, K, T, r, sigma, k, dt,
            n_initial=6,
            n_iterations=12,
            n_simulations_per_eval=500,
            acquisition='ei'
        )
    else:
        A_optimal = A_leland
        A_ml = A_leland

    # Storage
    errors_bs = []
    errors_leland = []
    errors_optimized = []
    errors_ml = []

    tc_bs = []
    tc_leland = []
    tc_optimized = []
    tc_ml = []

    # Monte Carlo simulations
    print(f"  Running {n_simulations:,} Monte Carlo simulations...")

    for sim in range(n_simulations):
        # Generate stock path
        S_path = simulate_stock_path(S0, r, sigma, T, dt)

        # Strategy 1: Black-Scholes
        error_bs, cost_bs = simulate_hedging_with_A(
            S_path, K, r, sigma, dt, k, A=0.0
        )
        errors_bs.append(error_bs)
        tc_bs.append(cost_bs)

        # Strategy 2: Classical Leland
        error_leland, cost_leland = simulate_hedging_with_A(
            S_path, K, r, sigma, dt, k, A=A_leland
        )
        errors_leland.append(error_leland)
        tc_leland.append(cost_leland)

        # Strategy 3: Optimized Leland
        error_opt, cost_opt = simulate_hedging_with_A(
            S_path, K, r, sigma, dt, k, A=A_optimal
        )
        errors_optimized.append(error_opt)
        tc_optimized.append(cost_opt)

        # Strategy 4: ML-Calibrated Leland
        error_ml, cost_ml = simulate_hedging_with_A_ml(
            S_path, K, r, sigma, dt, k, A=A_ml
        )
        errors_ml.append(error_ml)
        tc_ml.append(cost_ml)

    # Aggregate results
    results = {
        'k': k,
        'dt': dt,
        'steps_per_year': int(1/dt),
        'A_leland': A_leland,
        'A_optimal': A_optimal,
        'A_ml': A_ml,
        'BlackScholes': {
            'mean_error': np.mean(errors_bs),
            'std_error': np.std(errors_bs),
            'mean_tc': np.mean(tc_bs)
        },
        'Leland': {
            'mean_error': np.mean(errors_leland),
            'std_error': np.std(errors_leland),
            'mean_tc': np.mean(tc_leland)
        },
        'OptimizedLeland': {
            'mean_error': np.mean(errors_optimized),
            'std_error': np.std(errors_optimized),
            'mean_tc': np.mean(tc_optimized)
        },
        'MLCalibratedLeland': {
            'mean_error': np.mean(errors_ml),
            'std_error': np.std(errors_ml),
            'mean_tc': np.mean(tc_ml)
        }
    }

    print(f"  ✓ Complete | BS: {results['BlackScholes']['std_error']:.4f}, "
          f"Leland: {results['Leland']['std_error']:.4f}, "
          f"Opt: {results['OptimizedLeland']['std_error']:.4f}, "
          f"ML: {results['MLCalibratedLeland']['std_error']:.4f}")

    return results


def sensitivity_analysis_k(
    k_values: List[float],
    dt_fixed: float = 1/252,
    n_simulations: int = 10000
) -> List[Dict]:
    """
    Sensitivity analysis: vary transaction cost k

    Parameters:
    -----------
    k_values : list
        Transaction cost rates to test
    dt_fixed : float
        Fixed time step
    n_simulations : int
        Monte Carlo simulations per k value

    Returns:
    --------
    results_list : list of dict
        Results for each k value
    """
    print_header("SENSITIVITY ANALYSIS: TRANSACTION COST (k)")
    print(f"\nTesting k values: {k_values}")
    print(f"Fixed dt: {dt_fixed:.6f} ({int(1/dt_fixed)} steps/year)")
    print(f"Monte Carlo simulations per k: {n_simulations:,}")

    results_list = []

    for k in k_values:
        result = run_single_parameter_set(
            k=k, dt=dt_fixed, n_simulations=n_simulations, recalibrate=True
        )
        results_list.append(result)

    return results_list


def sensitivity_analysis_dt(
    dt_values: List[float],
    k_fixed: float = 0.01,
    n_simulations: int = 10000
) -> List[Dict]:
    """
    Sensitivity analysis: vary rebalancing frequency (dt)

    Parameters:
    -----------
    dt_values : list
        Time steps to test
    k_fixed : float
        Fixed transaction cost rate
    n_simulations : int
        Monte Carlo simulations per dt value

    Returns:
    --------
    results_list : list of dict
        Results for each dt value
    """
    print_header("SENSITIVITY ANALYSIS: REBALANCING FREQUENCY (Δt)")
    print(f"\nTesting dt values: {[f'{dt:.6f} ({int(1/dt)}/year)' for dt in dt_values]}")
    print(f"Fixed k: {k_fixed:.4f}")
    print(f"Monte Carlo simulations per dt: {n_simulations:,}")

    results_list = []

    for dt in dt_values:
        result = run_single_parameter_set(
            k=k_fixed, dt=dt, n_simulations=n_simulations, recalibrate=True
        )
        results_list.append(result)

    return results_list


def sensitivity_analysis_2d(
    k_values: List[float],
    dt_values: List[float],
    n_simulations: int = 5000
) -> List[Dict]:
    """
    Full 2D sensitivity analysis: vary both k and dt

    Parameters:
    -----------
    k_values : list
        Transaction cost rates to test
    dt_values : list
        Time steps to test
    n_simulations : int
        Monte Carlo simulations per (k, dt) combination

    Returns:
    --------
    results_list : list of dict
        Results for each (k, dt) combination
    """
    print_header("FULL 2D SENSITIVITY ANALYSIS: (k, Δt)")
    print(f"\nTesting k values: {k_values}")
    print(f"Testing dt values: {[f'{dt:.6f}' for dt in dt_values]}")
    print(f"Total combinations: {len(k_values)} × {len(dt_values)} = {len(k_values)*len(dt_values)}")
    print(f"Monte Carlo simulations per combination: {n_simulations:,}")

    results_list = []

    for i, k in enumerate(k_values):
        for j, dt in enumerate(dt_values):
            print(f"\n[{i*len(dt_values)+j+1}/{len(k_values)*len(dt_values)}] ", end="")
            result = run_single_parameter_set(
                k=k, dt=dt, n_simulations=n_simulations, recalibrate=True
            )
            results_list.append(result)

    return results_list


def analyze_sensitivity_results(results_list: List[Dict], analysis_type: str = 'k'):
    """
    Analyze and print sensitivity analysis results

    Parameters:
    -----------
    results_list : list of dict
        Results from sensitivity analysis
    analysis_type : str
        'k', 'dt', or '2d'
    """
    print_header(f"SENSITIVITY ANALYSIS RESULTS: {analysis_type.upper()}")

    # Create summary table
    print("\n" + "="*120)
    print("VARIANCE (STD ERROR) COMPARISON")
    print("="*120)

    if analysis_type == 'k':
        print(f"\n{'k':<10} {'Steps/Y':<10} {'A_Leland':<12} {'A_Opt':<12} {'A_ML':<12} "
              f"{'BS Std':<10} {'Leland':<10} {'Opt':<10} {'ML':<10}")
        print("-"*120)
        for r in results_list:
            print(f"{r['k']:<10.4f} {r['steps_per_year']:<10} "
                  f"{r['A_leland']:<12.4f} {r['A_optimal']:<12.4f} {r['A_ml']:<12.4f} "
                  f"{r['BlackScholes']['std_error']:<10.4f} "
                  f"{r['Leland']['std_error']:<10.4f} "
                  f"{r['OptimizedLeland']['std_error']:<10.4f} "
                  f"{r['MLCalibratedLeland']['std_error']:<10.4f}")

    elif analysis_type == 'dt':
        print(f"\n{'dt':<12} {'Steps/Y':<10} {'A_Leland':<12} {'A_Opt':<12} {'A_ML':<12} "
              f"{'BS Std':<10} {'Leland':<10} {'Opt':<10} {'ML':<10}")
        print("-"*120)
        for r in results_list:
            print(f"{r['dt']:<12.6f} {r['steps_per_year']:<10} "
                  f"{r['A_leland']:<12.4f} {r['A_optimal']:<12.4f} {r['A_ml']:<12.4f} "
                  f"{r['BlackScholes']['std_error']:<10.4f} "
                  f"{r['Leland']['std_error']:<10.4f} "
                  f"{r['OptimizedLeland']['std_error']:<10.4f} "
                  f"{r['MLCalibratedLeland']['std_error']:<10.4f}")

    else:  # 2d
        print(f"\n{'k':<10} {'dt':<12} {'Steps/Y':<10} {'A_Leland':<10} {'A_Opt':<10} {'A_ML':<10} "
              f"{'BS':<8} {'Leland':<8} {'Opt':<8} {'ML':<8}")
        print("-"*120)
        for r in results_list:
            print(f"{r['k']:<10.4f} {r['dt']:<12.6f} {r['steps_per_year']:<10} "
                  f"{r['A_leland']:<10.4f} {r['A_optimal']:<10.4f} {r['A_ml']:<10.4f} "
                  f"{r['BlackScholes']['std_error']:<8.4f} "
                  f"{r['Leland']['std_error']:<8.4f} "
                  f"{r['OptimizedLeland']['std_error']:<8.4f} "
                  f"{r['MLCalibratedLeland']['std_error']:<8.4f}")

    print("-"*120)

    # Test H1 and H2 robustness
    print("\n" + "="*120)
    print("HYPOTHESIS ROBUSTNESS CHECK")
    print("="*120)

    h1_confirmed = 0
    h2_confirmed = 0
    total = len(results_list)

    print(f"\n{'Parameter':<25} {'H1 (Opt<Leland)':<20} {'H2 (ML<Opt)':<20} {'Best Strategy':<15}")
    print("-"*120)

    for r in results_list:
        if analysis_type == 'k':
            param_str = f"k={r['k']:.4f}"
        elif analysis_type == 'dt':
            param_str = f"dt={r['dt']:.6f} ({r['steps_per_year']}/y)"
        else:
            param_str = f"k={r['k']:.4f}, dt={r['dt']:.6f}"

        std_leland = r['Leland']['std_error']
        std_opt = r['OptimizedLeland']['std_error']
        std_ml = r['MLCalibratedLeland']['std_error']

        h1_holds = std_opt < std_leland
        h2_holds = std_ml < std_opt

        h1_str = "✅ YES" if h1_holds else "❌ NO"
        h2_str = "✅ YES" if h2_holds else "❌ NO"

        # Determine best strategy
        stds = {
            'BS': r['BlackScholes']['std_error'],
            'Leland': std_leland,
            'Opt': std_opt,
            'ML': std_ml
        }
        best = min(stds, key=stds.get)

        print(f"{param_str:<25} {h1_str:<20} {h2_str:<20} {best:<15}")

        if h1_holds:
            h1_confirmed += 1
        if h2_holds:
            h2_confirmed += 1

    print("-"*120)
    print(f"\nH1 confirmed in {h1_confirmed}/{total} cases ({100*h1_confirmed/total:.1f}%)")
    print(f"H2 confirmed in {h2_confirmed}/{total} cases ({100*h2_confirmed/total:.1f}%)")

    if h1_confirmed == total:
        print("\n✅ H1 is ROBUST across all tested parameters!")
    else:
        print(f"\n⚠️  H1 fails in {total - h1_confirmed} cases")

    if h2_confirmed == total:
        print("✅ H2 is ROBUST across all tested parameters!")
    else:
        print(f"⚠️  H2 fails in {total - h2_confirmed} cases")

    print("="*120)


def export_sensitivity_results(results_list: List[Dict], filename: str = 'sensitivity_results.csv'):
    """
    Export sensitivity analysis results to CSV

    Parameters:
    -----------
    results_list : list of dict
        Results from sensitivity analysis
    filename : str
        Output CSV filename
    """
    rows = []

    for r in results_list:
        row = {
            'k': r['k'],
            'dt': r['dt'],
            'steps_per_year': r['steps_per_year'],
            'A_leland': r['A_leland'],
            'A_optimal': r['A_optimal'],
            'A_ml': r['A_ml'],
            'BS_mean': r['BlackScholes']['mean_error'],
            'BS_std': r['BlackScholes']['std_error'],
            'BS_tc': r['BlackScholes']['mean_tc'],
            'Leland_mean': r['Leland']['mean_error'],
            'Leland_std': r['Leland']['std_error'],
            'Leland_tc': r['Leland']['mean_tc'],
            'Opt_mean': r['OptimizedLeland']['mean_error'],
            'Opt_std': r['OptimizedLeland']['std_error'],
            'Opt_tc': r['OptimizedLeland']['mean_tc'],
            'ML_mean': r['MLCalibratedLeland']['mean_error'],
            'ML_std': r['MLCalibratedLeland']['std_error'],
            'ML_tc': r['MLCalibratedLeland']['mean_tc']
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    print(f"\n✓ Results exported to {filename}")


def main():
    """
    Main function - run full sensitivity analysis
    """
    print_header("HYPOTHESIS H3: SENSITIVITY ANALYSIS")
    print("\nThis script tests robustness of all 4 strategies to parameter changes")
    print("Testing parameters:")
    print("  - Transaction cost k ∈ {0.005, 0.01, 0.015, 0.02}")
    print("  - Rebalancing frequency Δt ∈ {1/252, 1/126, 1/63, 1/21}")
    print("\nChoose analysis type:")
    print("  1. Vary k only (fixed dt=1/252)")
    print("  2. Vary dt only (fixed k=0.01)")
    print("  3. Full 2D analysis (vary both k and dt)")

    # For automated testing, run all 3
    print("\nRunning all 3 analyses...\n")

    # Analysis 1: Vary k
    k_values = [0.005, 0.01, 0.015, 0.02]
    results_k = sensitivity_analysis_k(k_values, n_simulations=10000)
    analyze_sensitivity_results(results_k, analysis_type='k')
    export_sensitivity_results(results_k, filename='sensitivity_k.csv')

    # Analysis 2: Vary dt
    dt_values = [1/252, 1/126, 1/63, 1/21]
    results_dt = sensitivity_analysis_dt(dt_values, n_simulations=10000)
    analyze_sensitivity_results(results_dt, analysis_type='dt')
    export_sensitivity_results(results_dt, filename='sensitivity_dt.csv')

    # Analysis 3: Full 2D
    print("\n" + "="*80)
    print("WARNING: Full 2D analysis will take significant time!")
    print(f"Total runs: {len(k_values)} × {len(dt_values)} = {len(k_values)*len(dt_values)}")
    print("Each run includes calibration + 5,000 Monte Carlo simulations")
    print("Estimated time: 30-45 minutes")
    print("="*80)

    # Reduced simulations for 2D to save time
    results_2d = sensitivity_analysis_2d(k_values, dt_values, n_simulations=5000)
    analyze_sensitivity_results(results_2d, analysis_type='2d')
    export_sensitivity_results(results_2d, filename='sensitivity_2d.csv')

    # Final summary
    print_header("SENSITIVITY ANALYSIS COMPLETE")
    print("\n✓ Analysis 1 (k): Complete")
    print("✓ Analysis 2 (dt): Complete")
    print("✓ Analysis 3 (2D): Complete")
    print("\nOutput files:")
    print("  - sensitivity_k.csv")
    print("  - sensitivity_dt.csv")
    print("  - sensitivity_2d.csv")
    print("\nNext steps:")
    print("  1. Review hypothesis robustness (H1 and H2 across parameters)")
    print("  2. Visualize results (heatmaps, line plots)")
    print("  3. Identify parameter ranges where strategies work best")
    print("="*80 + "\n")

    return results_k, results_dt, results_2d


if __name__ == "__main__":
    results_k, results_dt, results_2d = main()
