"""
Complete Analysis Runner
========================
Run all analyses for a given ticker:
1. Multi-run ABM (100 runs with statistical tests)
2. Adaptive sensitivity analysis (k and dt with real volatility)

Usage:
------
python run_complete_analysis.py TSLA          # Analyze TSLA
python run_complete_analysis.py AAPL 50       # Analyze AAPL with 50 ABM runs
python run_complete_analysis.py TSLA AAPL     # Analyze multiple tickers
"""

import sys
import time
from config import Config
from run_multi_abm import main as run_multi_abm_main
from sensitivity_analysis_adaptive import compare_multiple_tickers


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*80)
    print(" "*20 + "COMPLETE LELAND STRATEGY ANALYSIS")
    print(" "*15 + "Multi-Run ABM + Adaptive Sensitivity")
    print("="*80)


def analyze_ticker(ticker: str, n_abm_runs: int = 100):
    """
    Run complete analysis for a single ticker

    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    n_abm_runs : int
        Number of ABM runs (default: 100)
    """
    start_time = time.time()

    print("\n" + "="*80)
    print(f" "*25 + f"ANALYZING: {ticker}")
    print("="*80)

    # === PART 1: Multi-Run ABM ===
    print("\n" + "-"*80)
    print("PART 1: MULTI-RUN ABM ANALYSIS")
    print("-"*80)

    try:
        results_df, summary_stats, test_results = run_multi_abm_main(
            ticker=ticker,
            n_runs=n_abm_runs
        )
        print(f"\n✓ Multi-run ABM complete for {ticker}")
    except Exception as e:
        print(f"\n✗ Error in multi-run ABM: {e}")
        return

    # === PART 2: Adaptive Sensitivity ===
    print("\n" + "-"*80)
    print("PART 2: ADAPTIVE SENSITIVITY ANALYSIS")
    print("-"*80)

    try:
        config = Config()
        all_results = compare_multiple_tickers(
            tickers=[ticker],
            config=config,
            k_values=[0.005, 0.01, 0.015, 0.02],
            dt_values=[1/252, 1/126, 1/63, 1/21],
            save_logs=True
        )
        print(f"\n✓ Adaptive sensitivity complete for {ticker}")
    except Exception as e:
        print(f"\n✗ Error in sensitivity analysis: {e}")
        return

    # === Summary ===
    elapsed = time.time() - start_time

    print("\n" + "="*80)
    print(f" "*20 + f"ANALYSIS COMPLETE: {ticker}")
    print("="*80)

    print(f"\nTime elapsed: {elapsed/60:.1f} minutes")

    print(f"\nFiles created for {ticker}:")
    print(f"  ABM Results:")
    print(f"    - output_csv/multi_abm_runs_{ticker}.csv      (all {n_abm_runs} runs)")
    print(f"    - output_csv/multi_abm_summary_{ticker}.csv   (statistical summary)")
    print(f"    - output_csv/multi_abm_tests_{ticker}.csv     (t-tests)")
    print(f"  Sensitivity Results:")
    print(f"    - output_csv/sensitivity_k_{ticker}.csv       (transaction cost sensitivity)")
    print(f"    - output_csv/sensitivity_dt_{ticker}.csv      (rebalancing sensitivity)")
    print(f"  Logs:")
    print(f"    - log/sensitivity_{ticker}.txt                (sensitivity analysis log)")

    print("\n" + "="*80 + "\n")


def main():
    """Main execution"""
    print_banner()

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python run_complete_analysis.py TICKER [N_RUNS]")
        print("\nExamples:")
        print("  python run_complete_analysis.py TSLA")
        print("  python run_complete_analysis.py AAPL 50")
        print("  python run_complete_analysis.py TSLA AAPL NVDA")
        print("\nDefault: Analyzes TSLA with 100 ABM runs\n")

        # Run default
        ticker = "TSLA"
        n_runs = 100
        print(f"Running default analysis: {ticker} with {n_runs} ABM runs...\n")
        analyze_ticker(ticker, n_runs)
        return

    # Get tickers from command line
    args = sys.argv[1:]

    # Check if last arg is number (n_runs)
    try:
        n_runs = int(args[-1])
        tickers = args[:-1]
    except ValueError:
        n_runs = 100
        tickers = args

    if not tickers:
        print("\nError: No ticker specified!")
        return

    print(f"\nTickers to analyze: {', '.join(tickers)}")
    print(f"ABM runs per ticker: {n_runs}")

    total_start = time.time()

    # Analyze each ticker
    for i, ticker in enumerate(tickers, 1):
        print(f"\n{'='*80}")
        print(f" "*25 + f"TICKER {i}/{len(tickers)}: {ticker}")
        print(f"{'='*80}")

        analyze_ticker(ticker, n_runs)

    total_elapsed = time.time() - total_start

    # Final summary
    print("\n" + "="*80)
    print(" "*20 + "ALL ANALYSES COMPLETE")
    print("="*80)

    print(f"\nTotal tickers analyzed: {len(tickers)}")
    print(f"Total time: {total_elapsed/60:.1f} minutes ({total_elapsed/3600:.1f} hours)")
    print(f"\nAll results exported to CSV files")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
