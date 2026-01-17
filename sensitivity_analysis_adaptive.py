"""
Adaptive Sensitivity Analysis
==============================
Sensitivity analysis that automatically uses real market volatility

This version:
1. Downloads real market data for specified ticker
2. Extracts actual market volatility (not fixed σ=0.25)
3. Runs sensitivity analysis with REAL market parameters
4. Tests different tickers (TSLA, AAPL, NVDA, etc.)

Key improvement: σ adapts to each ticker's actual volatility!
"""

import sys
import os
import numpy as np
import pandas as pd
from config import Config
from market import download_market_data
from optimization import optimize_A_parameter, simulate_hedging_with_A
from ml_optimization import optimize_A_with_ML, simulate_hedging_with_A_ml
from model_monte_carlo import simulate_stock_path


class TeeLogger:
    """Duplicate stdout to both console and file"""
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()


def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(" "*((80 - len(title))//2) + title)
    print("="*80)


def run_adaptive_sensitivity_k(
    ticker: str,
    config: Config,
    market_volatility: float,
    k_values: list,
    n_simulations: int = 10000
):
    """
    Sensitivity analysis varying transaction cost k
    Uses REAL market volatility from ticker data

    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    config : Config
        Project configuration
    market_volatility : float
        Actual market volatility from ticker data
    k_values : list
        Transaction cost values to test
    n_simulations : int
        Monte Carlo simulations per k value

    Returns:
    --------
    results_df : pd.DataFrame
        Results for all k values
    """
    print_header(f"SENSITIVITY TO TRANSACTION COST (k) - {ticker}")

    print(f"\nTesting k values: {k_values}")
    print(f"Real market volatility (σ): {market_volatility:.4f}")
    print(f"Fixed dt: {1/config.mc_steps_per_year:.6f} ({config.mc_steps_per_year} steps/year)")
    print(f"Monte Carlo simulations per k: {n_simulations:,}")

    results = []

    for k in k_values:
        print(f"\nRunning k={k:.4f}, σ={market_volatility:.4f}...")

        # Parameters
        S0 = 100.0
        K = 100.0
        T = config.time_to_maturity
        r = config.risk_free_rate
        sigma = market_volatility  # USE REAL VOLATILITY!
        dt = 1 / config.mc_steps_per_year

        # Calibrate strategies
        print(f"  Calibrating Optimized Leland (grid search)...")
        A_leland = (k / sigma) * np.sqrt(8 / (np.pi * dt))
        A_optimal, opt_results = optimize_A_parameter(
            S0, K, T, r, sigma, k, dt,
            n_simulations=2000,
            A_grid=np.linspace(max(0, A_leland - 0.3), A_leland + 0.3, 11)
        )

        print(f"  Calibrating ML-Calibrated Leland (Bayesian)...")
        A_ml, ml_results = optimize_A_with_ML(
            S0, K, T, r, sigma, k, dt,
            n_initial=6,
            n_iterations=12,
            n_simulations_per_eval=500,
            acquisition='ei'
        )

        # Run Monte Carlo comparison
        print(f"  Running {n_simulations:,} Monte Carlo simulations...")

        errors_bs, errors_leland, errors_opt, errors_ml = [], [], [], []
        tc_bs, tc_leland, tc_opt, tc_ml = [], [], [], []

        for _ in range(n_simulations):
            # Generate stock path
            S_path = simulate_stock_path(S0, r, sigma, T, dt)

            # Test all strategies
            err_bs, cost_bs = simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A=0.0)
            err_leland, cost_leland = simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A=A_leland)
            err_opt, cost_opt = simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A=A_optimal)
            err_ml, cost_ml = simulate_hedging_with_A_ml(S_path, K, r, sigma, dt, k, A=A_ml)

            errors_bs.append(err_bs)
            errors_leland.append(err_leland)
            errors_opt.append(err_opt)
            errors_ml.append(err_ml)

            tc_bs.append(cost_bs)
            tc_leland.append(cost_leland)
            tc_opt.append(cost_opt)
            tc_ml.append(cost_ml)

        # Store results
        results.append({
            'ticker': ticker,
            'k': k,
            'dt': dt,
            'sigma': sigma,
            'steps_per_year': config.mc_steps_per_year,
            'A_leland': A_leland,
            'A_optimal': A_optimal,
            'A_ml': A_ml,
            'BS_mean': np.mean(errors_bs),
            'BS_std': np.std(errors_bs),
            'BS_tc': np.mean(tc_bs),
            'Leland_mean': np.mean(errors_leland),
            'Leland_std': np.std(errors_leland),
            'Leland_tc': np.mean(tc_leland),
            'Opt_mean': np.mean(errors_opt),
            'Opt_std': np.std(errors_opt),
            'Opt_tc': np.mean(tc_opt),
            'ML_mean': np.mean(errors_ml),
            'ML_std': np.std(errors_ml),
            'ML_tc': np.mean(tc_ml)
        })

        print(f"  ✓ Complete | BS: {np.std(errors_bs):.4f}, Leland: {np.std(errors_leland):.4f}, "
              f"Opt: {np.std(errors_opt):.4f}, ML: {np.std(errors_ml):.4f}")

    results_df = pd.DataFrame(results)

    # Print summary
    print_summary_table(results_df, f"Transaction Cost (k) - {ticker}")

    # Ensure output_csv directory exists
    import os
    os.makedirs('output_csv', exist_ok=True)

    # Export
    filename = f'output_csv/sensitivity_k_{ticker}.csv'
    results_df.to_csv(filename, index=False)
    print(f"\n✓ Results exported to: {filename}")

    return results_df


def run_adaptive_sensitivity_dt(
    ticker: str,
    config: Config,
    market_volatility: float,
    dt_values: list,
    n_simulations: int = 10000
):
    """
    Sensitivity analysis varying rebalancing frequency dt
    Uses REAL market volatility from ticker data
    """
    print_header(f"SENSITIVITY TO REBALANCING FREQUENCY (Δt) - {ticker}")

    print(f"\nTesting dt values: {[f'{dt:.6f}' for dt in dt_values]}")
    print(f"Real market volatility (σ): {market_volatility:.4f}")
    print(f"Fixed k: {config.k_transaction:.4f}")
    print(f"Monte Carlo simulations per dt: {n_simulations:,}")

    results = []

    for dt in dt_values:
        steps_per_year = int(1 / dt)
        print(f"\nRunning dt={dt:.6f} ({steps_per_year} steps/year), σ={market_volatility:.4f}...")

        # Parameters
        S0 = 100.0
        K = 100.0
        T = config.time_to_maturity
        r = config.risk_free_rate
        sigma = market_volatility  # USE REAL VOLATILITY!
        k = config.k_transaction

        # Calibrate strategies
        print(f"  Calibrating Optimized Leland (grid search)...")
        A_leland = (k / sigma) * np.sqrt(8 / (np.pi * dt))
        A_optimal, opt_results = optimize_A_parameter(
            S0, K, T, r, sigma, k, dt,
            n_simulations=2000,
            A_grid=np.linspace(max(0, A_leland - 0.3), A_leland + 0.3, 11)
        )

        print(f"  Calibrating ML-Calibrated Leland (Bayesian)...")
        A_ml, ml_results = optimize_A_with_ML(
            S0, K, T, r, sigma, k, dt,
            n_initial=6,
            n_iterations=12,
            n_simulations_per_eval=500,
            acquisition='ei'
        )

        # Run Monte Carlo
        print(f"  Running {n_simulations:,} Monte Carlo simulations...")

        errors_bs, errors_leland, errors_opt, errors_ml = [], [], [], []
        tc_bs, tc_leland, tc_opt, tc_ml = [], [], [], []

        for _ in range(n_simulations):
            S_path = simulate_stock_path(S0, r, sigma, T, dt)

            err_bs, cost_bs = simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A=0.0)
            err_leland, cost_leland = simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A=A_leland)
            err_opt, cost_opt = simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A=A_optimal)
            err_ml, cost_ml = simulate_hedging_with_A_ml(S_path, K, r, sigma, dt, k, A=A_ml)

            errors_bs.append(err_bs)
            errors_leland.append(err_leland)
            errors_opt.append(err_opt)
            errors_ml.append(err_ml)

            tc_bs.append(cost_bs)
            tc_leland.append(cost_leland)
            tc_opt.append(cost_opt)
            tc_ml.append(cost_ml)

        # Store results
        results.append({
            'ticker': ticker,
            'k': k,
            'dt': dt,
            'sigma': sigma,
            'steps_per_year': steps_per_year,
            'A_leland': A_leland,
            'A_optimal': A_optimal,
            'A_ml': A_ml,
            'BS_mean': np.mean(errors_bs),
            'BS_std': np.std(errors_bs),
            'BS_tc': np.mean(tc_bs),
            'Leland_mean': np.mean(errors_leland),
            'Leland_std': np.std(errors_leland),
            'Leland_tc': np.mean(tc_leland),
            'Opt_mean': np.mean(errors_opt),
            'Opt_std': np.std(errors_opt),
            'Opt_tc': np.mean(tc_opt),
            'ML_mean': np.mean(errors_ml),
            'ML_std': np.std(errors_ml),
            'ML_tc': np.mean(tc_ml)
        })

        print(f"  ✓ Complete | BS: {np.std(errors_bs):.4f}, Leland: {np.std(errors_leland):.4f}, "
              f"Opt: {np.std(errors_opt):.4f}, ML: {np.std(errors_ml):.4f}")

    results_df = pd.DataFrame(results)

    # Print summary
    print_summary_table(results_df, f"Rebalancing Frequency (Δt) - {ticker}")

    # Ensure output_csv directory exists
    import os
    os.makedirs('output_csv', exist_ok=True)

    # Export
    filename = f'output_csv/sensitivity_dt_{ticker}.csv'
    results_df.to_csv(filename, index=False)
    print(f"\n✓ Results exported to: {filename}")

    return results_df


def print_summary_table(results_df: pd.DataFrame, title: str):
    """Print formatted summary table"""
    print_header(f"RESULTS: {title}")

    print(f"\n{'k':<8} {'dt':<10} {'σ':<8} {'Steps/Y':<10} {'BS σ':<10} {'Leland σ':<10} {'Opt σ':<10} {'ML σ':<10} {'Winner':<10}")
    print("-"*100)

    for _, row in results_df.iterrows():
        # Determine winner (lowest std)
        stds = [row['BS_std'], row['Leland_std'], row['Opt_std'], row['ML_std']]
        winner_idx = np.argmin(stds)
        winners = ['BS', 'Leland', 'Opt', 'ML']
        winner = winners[winner_idx]

        print(f"{row['k']:<8.4f} {row['dt']:<10.6f} {row['sigma']:<8.4f} {int(row['steps_per_year']):<10} "
              f"{row['BS_std']:<10.4f} {row['Leland_std']:<10.4f} {row['Opt_std']:<10.4f} {row['ML_std']:<10.4f} "
              f"{winner:<10}")


def compare_multiple_tickers(
    tickers: list,
    config: Config,
    k_values: list = None,
    dt_values: list = None,
    save_logs: bool = True
):
    """
    Compare sensitivity across multiple tickers
    Each ticker uses its own real volatility!

    Parameters:
    -----------
    tickers : list
        List of ticker symbols (e.g., ['TSLA', 'AAPL', 'NVDA'])
    config : Config
        Project configuration
    k_values : list
        Transaction costs to test (default: [0.005, 0.01, 0.015, 0.02])
    dt_values : list
        Rebalancing frequencies to test (default: [1/252, 1/126, 1/63, 1/21])
    save_logs : bool
        Save logs to log/ directory (default: True)

    Returns:
    --------
    all_results : dict
        Results for all tickers
    """
    if k_values is None:
        k_values = [0.005, 0.01, 0.015, 0.02]

    if dt_values is None:
        dt_values = [1/252, 1/126, 1/63, 1/21]

    print_header(f"MULTI-TICKER SENSITIVITY ANALYSIS")
    print(f"\nTickers to analyze: {', '.join(tickers)}")
    print(f"Transaction costs: {k_values}")
    print(f"Rebalancing frequencies: {[f'1/{int(1/dt)}' for dt in dt_values]}")

    if save_logs:
        os.makedirs('log', exist_ok=True)
        print(f"Logs will be saved to: log/sensitivity_{{ticker}}.txt")

    all_results = {}

    for ticker in tickers:
        # Setup logging for this ticker
        if save_logs:
            log_file = f'log/sensitivity_{ticker}.txt'
            logger = TeeLogger(log_file)
            original_stdout = sys.stdout
            sys.stdout = logger
            print(f"\n{'='*80}")
            print(f"Sensitivity Analysis Log - {ticker}")
            print(f"Log file: {log_file}")
            print(f"{'='*80}\n")

        print("\n" + "="*80)
        print(f" "*30 + f"ANALYZING {ticker}")
        print("="*80)

        # Download market data
        print(f"\nDownloading {ticker} data...")
        market_data = download_market_data(
            ticker,
            config.start_date,
            config.end_date
        )

        market_volatility = market_data['volatility']
        print(f"✓ {ticker} volatility: σ = {market_volatility:.4f}")

        # Run sensitivity on k
        print(f"\n--- Testing Transaction Costs (k) for {ticker} ---")
        results_k = run_adaptive_sensitivity_k(
            ticker, config, market_volatility, k_values, n_simulations=10000
        )

        # Run sensitivity on dt
        print(f"\n--- Testing Rebalancing Frequency (Δt) for {ticker} ---")
        results_dt = run_adaptive_sensitivity_dt(
            ticker, config, market_volatility, dt_values, n_simulations=10000
        )

        all_results[ticker] = {
            'volatility': market_volatility,
            'results_k': results_k,
            'results_dt': results_dt
        }

        # Close log for this ticker
        if save_logs:
            print(f"\n{'='*80}")
            print(f"✓ Analysis complete for {ticker}")
            print(f"✓ Log saved to: {log_file}")
            print(f"{'='*80}\n")
            sys.stdout = original_stdout
            logger.close()

    # Comparative summary
    print_header("COMPARATIVE SUMMARY ACROSS TICKERS")

    print(f"\n{'Ticker':<10} {'σ (Vol)':<12} {'Best Strategy (k)':<25} {'Best Strategy (dt)':<25}")
    print("-"*80)

    for ticker, data in all_results.items():
        # Most common winner for k sensitivity
        k_results = data['results_k']
        k_winners = []
        for _, row in k_results.iterrows():
            stds = [row['Leland_std'], row['Opt_std'], row['ML_std']]
            k_winners.append(['Leland', 'Opt', 'ML'][np.argmin(stds)])
        k_winner = max(set(k_winners), key=k_winners.count)

        # Most common winner for dt sensitivity
        dt_results = data['results_dt']
        dt_winners = []
        for _, row in dt_results.iterrows():
            stds = [row['Leland_std'], row['Opt_std'], row['ML_std']]
            dt_winners.append(['Leland', 'Opt', 'ML'][np.argmin(stds)])
        dt_winner = max(set(dt_winners), key=dt_winners.count)

        print(f"{ticker:<10} {data['volatility']:<12.4f} {k_winner:<25} {dt_winner:<25}")

    return all_results


def main():
    """Main execution"""
    config = Config()

    # Test multiple tickers with their real volatilities
    tickers = ['TSLA', 'AAPL', 'NVDA']  # Can add more: 'SPY', 'GME', 'MSFT', etc.

    k_values = [0.005, 0.01, 0.015, 0.02]
    dt_values = [1/252, 1/126, 1/63, 1/21]

    all_results = compare_multiple_tickers(
        tickers, config, k_values, dt_values, save_logs=True
    )

    print_header("ANALYSIS COMPLETE")
    print(f"\n✓ Analyzed {len(tickers)} tickers")
    print(f"✓ Each ticker tested with its REAL market volatility")
    print(f"✓ Results exported to CSV files")
    print(f"✓ Logs saved to log/ directory")
    print("\nFiles created:")
    for ticker in tickers:
        print(f"  CSV:")
        print(f"    - output_csv/sensitivity_k_{ticker}.csv")
        print(f"    - output_csv/sensitivity_dt_{ticker}.csv")
        print(f"  Log:")
        print(f"    - log/sensitivity_{ticker}.txt")

    return all_results


if __name__ == "__main__":
    # Can specify tickers via command line
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
        config = Config()

        print(f"Running adaptive sensitivity for: {', '.join(tickers)}")

        all_results = compare_multiple_tickers(
            tickers, config,
            k_values=[0.005, 0.01, 0.015, 0.02],
            dt_values=[1/252, 1/126, 1/63, 1/21],
            save_logs=True
        )

        # Print summary
        print_header("ANALYSIS COMPLETE")
        print(f"\n✓ Analyzed {len(tickers)} tickers")
        print(f"✓ Results exported to CSV and log files")
        print("\nFiles created:")
        for ticker in tickers:
            print(f"  {ticker}:")
            print(f"    - output_csv/sensitivity_k_{ticker}.csv")
            print(f"    - output_csv/sensitivity_dt_{ticker}.csv")
            print(f"    - log/sensitivity_{ticker}.txt")
    else:
        # Default: TSLA, AAPL, NVDA
        all_results = main()
