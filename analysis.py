"""
Analysis Functions
==================
Functions to analyze and compare ABM and Monte Carlo results
"""

import numpy as np
import pandas as pd


def analyze_abm_results(results):
    """
    Analyze ABM results

    Parameters:
    -----------
    results: dict from ABMModel.get_results()
    """
    print("\n" + "="*70)
    print(" "*20 + "ABM RESULTS ANALYSIS")
    print("="*70)

    # Market info
    print(f"\nMarket:")
    print(f"  Ticker:            {results['ticker']}")
    print(f"  Initial price:     ${results['real_prices'][0]:.2f}")
    print(f"  Final price:       ${results['final_price']:.2f}")
    print(f"  Price change:      {(results['final_price']/results['real_prices'][0] - 1)*100:+.2f}%")
    print(f"  Strike (K):        ${results['strike']:.2f}")

    option_payoff = max(results['final_price'] - results['strike'], 0)
    print(f"  Option payoff:     ${option_payoff:.2f}")

    # Market Makers comparison
    print(f"\n{'Strategy':<20} {'Final P&L':<15} {'Trans. Costs':<15} {'# Hedges':<10}")
    print("-"*70)

    for strategy in ['BlackScholes', 'Leland']:
        data = results['market_makers'][strategy]
        print(f"{strategy:<20} ${data['final_pnl']:>8.2f}      "
              f"${data['transaction_costs']:>8.2f}      "
              f"{data['num_hedges']:<10}")

    print("-"*70)

    # Winner
    bs_pnl = results['market_makers']['BlackScholes']['final_pnl']
    leland_pnl = results['market_makers']['Leland']['final_pnl']
    diff = leland_pnl - bs_pnl

    if diff > 0:
        print(f"\n✓ Leland performed BETTER by ${diff:.2f}")
    else:
        print(f"\n✗ Black-Scholes performed better by ${-diff:.2f}")

    # Transaction cost comparison
    bs_tc = results['market_makers']['BlackScholes']['transaction_costs']
    leland_tc = results['market_makers']['Leland']['transaction_costs']
    tc_diff = bs_tc - leland_tc

    print(f"\nTransaction Costs:")
    print(f"  Black-Scholes:  ${bs_tc:.2f}")
    print(f"  Leland:         ${leland_tc:.2f}")
    if tc_diff > 0:
        print(f"  Savings:        ${tc_diff:.2f} ({tc_diff/bs_tc*100:.1f}%)")
    else:
        print(f"  Extra cost:     ${-tc_diff:.2f}")

    print("="*70 + "\n")


def analyze_mc_results(results):
    """
    Analyze Monte Carlo results

    Parameters:
    -----------
    results: dict from run_monte_carlo()
    """
    print("\n" + "="*70)
    print(" "*20 + "MONTE CARLO RESULTS")
    print("="*70)

    print(f"\nSimulation Parameters:")
    print(f"  Initial Price:     ${results['initial_price']:.2f}")
    print(f"  Strike:            ${results['strike']:.2f}")
    print(f"  Volatility:        {results['volatility']*100:.2f}%")

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

    if leland_mean > bs_mean and leland_std < bs_std:
        print("\n✓ Leland dominates: Better return AND lower risk!")
    elif leland_std < bs_std:
        print("\n✓ Leland reduces risk significantly")

    print("="*70 + "\n")


def compare_abm_vs_mc(abm_results, mc_results):
    """
    Compare ABM and Monte Carlo results

    Shows if ABM (real data) matches Monte Carlo (theory)
    """
    print("\n" + "="*70)
    print(" "*20 + "ABM vs MONTE CARLO COMPARISON")
    print("="*70)

    print(f"\n{'Metric':<30} {'ABM (Real Data)':<20} {'Monte Carlo':<20}")
    print("-"*70)

    # Black-Scholes comparison
    abm_bs_pnl = abm_results['market_makers']['BlackScholes']['final_pnl']
    mc_bs_pnl = mc_results['strategies']['BlackScholes']['mean_pnl']

    abm_bs_tc = abm_results['market_makers']['BlackScholes']['transaction_costs']
    mc_bs_tc = mc_results['strategies']['BlackScholes']['mean_tc']

    print("BLACK-SCHOLES:")
    print(f"  {'P&L':<28} ${abm_bs_pnl:>8.2f}          ${mc_bs_pnl:>8.2f}")
    print(f"  {'Transaction Costs':<28} ${abm_bs_tc:>8.2f}          ${mc_bs_tc:>8.2f}")

    # Leland comparison
    abm_leland_pnl = abm_results['market_makers']['Leland']['final_pnl']
    mc_leland_pnl = mc_results['strategies']['Leland']['mean_pnl']

    abm_leland_tc = abm_results['market_makers']['Leland']['transaction_costs']
    mc_leland_tc = mc_results['strategies']['Leland']['mean_tc']

    print("\nLELAND:")
    print(f"  {'P&L':<28} ${abm_leland_pnl:>8.2f}          ${mc_leland_pnl:>8.2f}")
    print(f"  {'Transaction Costs':<28} ${abm_leland_tc:>8.2f}          ${mc_leland_tc:>8.2f}")

    print("-"*70)

    # Leland advantage
    abm_advantage = abm_leland_pnl - abm_bs_pnl
    mc_advantage = mc_leland_pnl - mc_bs_pnl

    print(f"\nLeland Advantage:")
    print(f"  ABM (Real):       ${abm_advantage:>8.2f}")
    print(f"  Monte Carlo:      ${mc_advantage:>8.2f}")

    if abm_advantage > 0 and mc_advantage > 0:
        print("\n✓ Leland is better in BOTH real data AND simulations!")
    elif abm_advantage > 0:
        print("\n✓ Leland works better on real data")
    elif mc_advantage > 0:
        print("\n✓ Leland works better in theory (MC)")

    print("="*70 + "\n")


def export_results_to_csv(abm_results, mc_results, filename='results.csv'):
    """
    Export results to CSV file
    """
    # Create summary DataFrame
    data = {
        'Model': ['ABM', 'ABM', 'MC', 'MC'],
        'Strategy': ['Black-Scholes', 'Leland', 'Black-Scholes', 'Leland'],
        'Final_PnL': [
            abm_results['market_makers']['BlackScholes']['final_pnl'],
            abm_results['market_makers']['Leland']['final_pnl'],
            mc_results['strategies']['BlackScholes']['mean_pnl'],
            mc_results['strategies']['Leland']['mean_pnl']
        ],
        'Transaction_Costs': [
            abm_results['market_makers']['BlackScholes']['transaction_costs'],
            abm_results['market_makers']['Leland']['transaction_costs'],
            mc_results['strategies']['BlackScholes']['mean_tc'],
            mc_results['strategies']['Leland']['mean_tc']
        ],
        'Std_Dev': [
            np.nan,  # ABM doesn't have std (single run)
            np.nan,
            mc_results['strategies']['BlackScholes']['std_pnl'],
            mc_results['strategies']['Leland']['std_pnl']
        ]
    }

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

    print(f"✓ Results exported to {filename}")


# Test
if __name__ == "__main__":
    print("Analysis module loaded successfully!")
    print("\nAvailable functions:")
    print("  - analyze_abm_results(results)")
    print("  - analyze_mc_results(results)")
    print("  - compare_abm_vs_mc(abm_results, mc_results)")
    print("  - export_results_to_csv(abm_results, mc_results, filename)")
