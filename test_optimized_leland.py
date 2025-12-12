"""
Test Optimized Leland Strategy
================================
Compare three strategies:
1. Black-Scholes (no adjustment)
2. Classical Leland (fixed A formula)
3. Optimized Leland (calibrated A*)

Tests Hypothesis H1
"""

import numpy as np
from config import Config
from optimization import optimize_A_parameter
from model_monte_carlo import simulate_stock_path, simulate_hedging


def compare_three_strategies(config: Config):
    """
    Compare BS, Leland, and Optimized Leland strategies

    Returns:
    --------
    results : dict
    """
    print("\n" + "="*70)
    print(" "*15 + "COMPARING THREE HEDGING STRATEGIES")
    print("="*70)

    # Parameters
    S0 = 100.0
    K = 100.0
    T = config.time_to_maturity
    r = config.risk_free_rate
    sigma = 0.25  # Assumed volatility
    k = config.k_transaction
    dt = 1 / config.mc_steps_per_year
    n_sims = 10000  # Monte Carlo simulations

    print(f"\nParameters:")
    print(f"  S0={S0:.2f}, K={K:.2f}, T={T:.2f}")
    print(f"  σ={sigma:.4f}, r={r:.4f}, k={k:.4f}")
    print(f"  dt={dt:.6f} ({config.mc_steps_per_year} steps/year)")
    print(f"  Monte Carlo sims: {n_sims:,}")

    # ===== STEP 1: CALIBRATE OPTIMIZED LELAND =====
    print(f"\n{'='*70}")
    print("STEP 1: CALIBRATING OPTIMIZED LELAND")
    print(f"{'='*70}")

    A_optimal, opt_results = optimize_A_parameter(
        S0, K, T, r, sigma, k, dt,
        n_simulations=5000,  # Calibration simulations
        A_grid=np.linspace(0, 1.5, 16)
    )

    # Plot optimization
    plot_optimization_results(opt_results, save_path='optimization_A_results.png')

    # ===== STEP 2: COMPARE STRATEGIES =====
    print(f"\n{'='*70}")
    print("STEP 2: COMPARING STRATEGIES ON TEST SET")
    print(f"{'='*70}")

    # Storage
    errors_bs = []
    errors_leland = []
    errors_optimized = []

    tc_bs = []
    tc_leland = []
    tc_optimized = []

    print(f"\nRunning {n_sims:,} test simulations...")

    for sim in range(n_sims):
        # Generate stock path
        S_path = simulate_stock_path(S0, r, sigma, T, dt)

        # Test 1: Black-Scholes
        error_bs, cost_bs = simulate_hedging(
            S_path, K, r, sigma, dt, k, strategy='BS'
        )
        errors_bs.append(error_bs)
        tc_bs.append(cost_bs)

        # Test 2: Classical Leland
        error_leland, cost_leland = simulate_hedging(
            S_path, K, r, sigma, dt, k, strategy='Leland'
        )
        errors_leland.append(error_leland)
        tc_leland.append(cost_leland)

        # Test 3: Optimized Leland (manual simulation with A*)
        from optimization import simulate_hedging_with_A
        error_opt, cost_opt = simulate_hedging_with_A(
            S_path, K, r, sigma, dt, k, A_optimal
        )
        errors_optimized.append(error_opt)
        tc_optimized.append(cost_opt)

        # Progress
        if (sim + 1) % 2000 == 0:
            print(f"  Progress: {sim+1:,}/{n_sims:,}")

    print("✓ Test simulations complete!\n")

    # ===== STEP 3: RESULTS =====
    results = {
        'BlackScholes': {
            'mean_error': np.mean(errors_bs),
            'std_error': np.std(errors_bs),
            'mean_tc': np.mean(tc_bs),
            'errors': errors_bs
        },
        'ClassicalLeland': {
            'mean_error': np.mean(errors_leland),
            'std_error': np.std(errors_leland),
            'mean_tc': np.mean(tc_leland),
            'A_value': (k / sigma) * np.sqrt(8 / (np.pi * dt)),
            'errors': errors_leland
        },
        'OptimizedLeland': {
            'mean_error': np.mean(errors_optimized),
            'std_error': np.std(errors_optimized),
            'mean_tc': np.mean(tc_optimized),
            'A_optimal': A_optimal,
            'errors': errors_optimized
        }
    }

    # Print comparison
    print(f"{'='*70}")
    print(" "*20 + "RESULTS COMPARISON")
    print(f"{'='*70}")

    print(f"\n{'Strategy':<25} {'Mean Error':<15} {'Std Error':<15} {'Avg TC':<12}")
    print("-"*70)

    for name in ['BlackScholes', 'ClassicalLeland', 'OptimizedLeland']:
        data = results[name]
        print(f"{name:<25} ${data['mean_error']:>8.4f}      "
              f"${data['std_error']:>8.4f}      "
              f"${data['mean_tc']:>8.2f}")

    print("-"*70)

    # Test Hypothesis H1
    std_classical = results['ClassicalLeland']['std_error']
    std_optimized = results['OptimizedLeland']['std_error']
    improvement = (1 - std_optimized / std_classical) * 100

    print(f"\n{'='*70}")
    print(" "*18 + "HYPOTHESIS H1 TEST")
    print(f"{'='*70}")

    print(f"\nH1: Optimized Leland has lower variance than Classical Leland")
    print(f"\n  Classical Leland Std:  ${std_classical:.4f}")
    print(f"  Optimized Leland Std:  ${std_optimized:.4f}")
    print(f"  Improvement:           {improvement:+.2f}%")

    if std_optimized < std_classical:
        print(f"\n  ✅ H1 CONFIRMED: Optimized Leland reduces variance!")
    else:
        print(f"\n  ❌ H1 REJECTED: No improvement")

    # Also compare to BS
    std_bs = results['BlackScholes']['std_error']
    print(f"\nBonus comparison:")
    print(f"  Black-Scholes Std:     ${std_bs:.4f}")
    print(f"  Optimized vs BS:       {(1 - std_optimized/std_bs)*100:+.2f}%")

    print(f"\n{'='*70}\n")

    return results


def plot_comparison(results: dict, save_path: str = 'strategy_comparison.png'):
    """Plot comparison of three strategies"""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not available")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    strategies = ['BlackScholes', 'ClassicalLeland', 'OptimizedLeland']
    colors = ['blue', 'orange', 'green']
    labels = ['Black-Scholes', 'Classical Leland', 'Optimized Leland']

    # Plot 1: Error distributions
    for strategy, color, label in zip(strategies, colors, labels):
        errors = results[strategy]['errors']
        axes[0].hist(errors, bins=50, alpha=0.5, color=color,
                     label=f"{label} (σ={results[strategy]['std_error']:.3f})",
                     density=True)

    axes[0].axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.7)
    axes[0].set_xlabel('Hedging Error (P&L)', fontsize=12)
    axes[0].set_ylabel('Density', fontsize=12)
    axes[0].set_title('Distribution of Hedging Errors', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Risk-Return
    means = [results[s]['mean_error'] for s in strategies]
    stds = [results[s]['std_error'] for s in strategies]

    for i, (mean, std, label, color) in enumerate(zip(means, stds, labels, colors)):
        axes[1].scatter(std, mean, s=200, color=color, alpha=0.7,
                        label=label, edgecolors='black', linewidth=2)
        axes[1].annotate(label, (std, mean), xytext=(10, 10),
                        textcoords='offset points', fontsize=10)

    axes[1].axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    axes[1].set_xlabel('Risk (Std Dev of Error)', fontsize=12)
    axes[1].set_ylabel('Return (Mean Error)', fontsize=12)
    axes[1].set_title('Risk-Return Tradeoff', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"✓ Comparison plot saved to {save_path}")
    plt.show()


if __name__ == "__main__":
    from config import config

    print("\n" + "="*70)
    print(" "*10 + "OPTIMIZED LELAND: TESTING HYPOTHESIS H1")
    print("="*70)

    # Run comparison
    results = compare_three_strategies(config)

    # Plot
    plot_comparison(results)

    print("\n✓ Test complete!")
    print("\nNext steps:")
    print("  1. Check 'optimization_A_results.png' - optimization curve")
    print("  2. Check 'strategy_comparison.png' - performance comparison")
    print("  3. If H1 confirmed → use Optimized Leland in main ABM model")
