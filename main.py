"""
Main Entry Point
================
Run ABM and Monte Carlo simulations
"""

from config import config
from model_abm import run_abm
from model_monte_carlo import run_monte_carlo, print_mc_results
from analysis import analyze_abm_results, analyze_mc_results, compare_abm_vs_mc, export_results_to_csv


def main():
    """
    Main function - runs both ABM and Monte Carlo
    """
    print("\n" + "="*70)
    print(" "*15 + "LELAND MODEL: ABM + MONTE CARLO")
    print("="*70)

    # Display configuration
    config.display()

    # ===== RUN ABM (Real Data) =====
    print("\n" + "="*70)
    print("PART 1: AGENT-BASED MODEL (REAL DATA)")
    print("="*70)

    abm_results, market_data = run_abm(config)
    analyze_abm_results(abm_results)

    # ===== RUN MONTE CARLO =====
    print("\n" + "="*70)
    print("PART 2: MONTE CARLO SIMULATION")
    print("="*70)

    # Use parameters from real data
    initial_price = market_data['prices'][0]
    strike = abm_results['strike']
    volatility = market_data['volatility']

    mc_results = run_monte_carlo(config, initial_price, strike, volatility)
    analyze_mc_results(mc_results)

    # ===== COMPARE =====
    compare_abm_vs_mc(abm_results, mc_results)

    # ===== EXPORT =====
    export_results_to_csv(abm_results, mc_results, 'results_summary.csv')

    print("\n" + "="*70)
    print("✓ SIMULATION COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    # print("  1. Open 'visualization' in PyCharm/Jupyter")
    print("  1. Run all cells to see visualizations")
    print("  2. Check 'results_summary.csv' for exported data")
    print("\n" + "="*70 + "\n")

    return abm_results, mc_results


if __name__ == "__main__":
    abm_results, mc_results = main()
