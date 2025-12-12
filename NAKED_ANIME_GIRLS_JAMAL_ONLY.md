# Visualization Guide for Team Member

**Purpose**: This guide explains the project's data structure, available variables, and what to visualize - WITHOUT code examples. Focus on understanding what data exists and what's important to show.

**Your Role**: Create visualizations that demonstrate:
1. Hypothesis H1 testing (Optimized vs Classical Leland)
2. Hypothesis H2 testing (ML-Calibrated vs Optimized Leland)
3. Overall variance reduction across all 4 strategies
4. ABM vs Monte Carlo comparison

---

## Project Overview

### The 4 Strategies Being Compared:

1. **Black-Scholes**: Baseline (ignores transaction costs, A=0)
2. **Classical Leland**: Uses formula A = (k/σ)√(8/πΔt)
3. **Optimized Leland**: Uses grid search to find best A* that minimizes variance
4. **ML-Calibrated Leland**: Uses Bayesian Optimization to find best A*_ml (more efficient than grid search)

### The 2 Testing Approaches:

1. **ABM (Agent-Based Model)**: Real AAPL historical data (2021-2023), multi-agent simulation
2. **Monte Carlo**: 50,000 GBM simulations, statistical testing

---

## Data Structure Overview

### Main Script to Run: `run_full_comparison.py`

This script generates ALL the data you need for visualization. It returns:
- `abm_results`: ABM simulation results with all 4 strategies
- `mc_results`: Monte Carlo results with all 4 strategies
- `A_optimal`: Calibrated A parameter from grid search
- `A_ml`: Calibrated A parameter from Bayesian optimization

---

## 1. ABM Results Data Structure

### What `abm_results` Contains:

```
abm_results = {
    'strike': float,                    # Strike price (K)
    'initial_price': float,             # Initial AAPL price (S0)
    'final_price': float,               # Final AAPL price
    'market_makers': {
        'BlackScholes': {
            'final_pnl': float,         # Final profit/loss ($)
            'transaction_costs': float,  # Total transaction costs ($)
            'num_hedges': int,          # Number of rebalancing events
            'pnl_history': [list],      # P&L at each time step
            'position_history': [list], # Stock position over time
            'price_path': [list]        # AAPL price path used
        },
        'Leland': { ... },              # Same structure
        'OptimizedLeland': { ... },     # Same structure + 'A_optimal'
        'MLCalibratedLeland': { ... }   # Same structure + 'A_ml'
    }
}
```

### Key ABM Variables to Visualize:

| Variable | Location | Type | Meaning |
|----------|----------|------|---------|
| `final_pnl` | `abm_results['market_makers'][strategy]['final_pnl']` | float | Final hedging error ($) - lower is better |
| `transaction_costs` | `abm_results['market_makers'][strategy]['transaction_costs']` | float | Total costs paid ($) |
| `num_hedges` | `abm_results['market_makers'][strategy]['num_hedges']` | int | How many times rebalanced |
| `pnl_history` | `abm_results['market_makers'][strategy]['pnl_history']` | list | P&L evolution over 504 days |
| `position_history` | `abm_results['market_makers'][strategy]['position_history']` | list | Stock holdings (delta) over time |
| `price_path` | `abm_results['market_makers'][strategy]['price_path']` | list | AAPL price over 504 days |

### What's Important in ABM Results:

1. **Final P&L Comparison**: Which strategy has the lowest final P&L (closest to zero)?
2. **Transaction Costs**: How much did each strategy pay in costs?
3. **P&L Evolution**: How does P&L change over time for each strategy?
4. **Position Dynamics**: How does delta hedging position change with price movements?

---

## 2. Monte Carlo Results Data Structure

### What `mc_results` Contains:

```
mc_results = {
    'BlackScholes': {
        'mean_error': float,        # Average hedging error ($)
        'std_error': float,         # Standard deviation of error ($) ← KEY METRIC
        'mean_tc': float,           # Average transaction costs ($)
        'errors': [list]            # All 50,000 individual errors
    },
    'Leland': { ... },              # Same structure
    'OptimizedLeland': {
        'mean_error': float,
        'std_error': float,         # ← Test H1: Should be < Leland
        'mean_tc': float,
        'A_optimal': float,         # The calibrated A* value
        'errors': [list]
    },
    'MLCalibratedLeland': {
        'mean_error': float,
        'std_error': float,         # ← Test H2: Should be < OptimizedLeland
        'mean_tc': float,
        'A_ml': float,              # The ML-calibrated A*_ml value
        'errors': [list]
    }
}
```

### Key Monte Carlo Variables:

| Variable | Location | Type | Meaning |
|----------|----------|------|---------|
| `std_error` | `mc_results[strategy]['std_error']` | float | **MOST IMPORTANT** - variance of hedging error |
| `mean_error` | `mc_results[strategy]['mean_error']` | float | Average hedging error (bias) |
| `mean_tc` | `mc_results[strategy]['mean_tc']` | float | Average transaction costs |
| `errors` | `mc_results[strategy]['errors']` | list (50,000) | Full distribution of errors |
| `A_optimal` | `mc_results['OptimizedLeland']['A_optimal']` | float | Grid search result |
| `A_ml` | `mc_results['MLCalibratedLeland']['A_ml']` | float | Bayesian optimization result |

### What's Important in Monte Carlo Results:

1. **Standard Deviation** (`std_error`): This is THE key metric for H1 and H2 testing
2. **Error Distributions**: Full distribution of 50,000 hedging errors for each strategy
3. **Hypothesis Testing**: Compare `std_error` values to confirm H1 and H2

---

## 3. Optimization Results Data Structure

### Grid Search Results (Optimized Leland)

The calibration produces:

```
opt_results = {
    'A_optimal': float,             # Best A value found
    'A_grid': [array],              # All A values tested (e.g., 16 points)
    'mean_errors': [array],         # Mean error for each A
    'std_errors': [array],          # Std error for each A ← Shows optimization curve
    'mean_tcs': [array],            # Transaction costs for each A
    'optimal_idx': int,             # Index of best A in grid
    'A_leland': float,              # Classical Leland A for comparison
    'improvement_pct': float        # % improvement over Classical Leland
}
```

**Important**: `std_errors` array shows how variance changes with different A values. The minimum point is `A_optimal`.

### Bayesian Optimization Results (ML-Calibrated Leland)

```
ml_results = {
    'A_ml': float,                  # Best A value found
    'A_tested': [array],            # All A values evaluated (e.g., 30 points)
    'mean_errors': [array],         # Mean error for each tested A
    'std_errors': [array],          # Std error for each tested A
    'best_idx': int,                # Index of best A
    'A_leland': float,              # Classical Leland A
    'n_evaluations': int,           # Total evaluations (30)
    'method': str                   # "Bayesian Optimization + GP"
}
```

**Important**: `std_errors` shows adaptive search path. Early points are random exploration, later points converge to optimal region.

---

## Priority 1 Visualizations (CRITICAL for Hypotheses)

### 1. Variance Reduction Bar Chart

**Purpose**: Show H1 and H2 testing results

**Data Needed**:
- `mc_results['BlackScholes']['std_error']`
- `mc_results['Leland']['std_error']`
- `mc_results['OptimizedLeland']['std_error']`
- `mc_results['MLCalibratedLeland']['std_error']`

**What to Show**:
- 4 bars showing standard deviation for each strategy
- Black-Scholes should be highest (~$2.50)
- Classical Leland should be lower (~$0.92)
- Optimized should be lower than Leland (~$0.85) ← **H1**
- ML-Calibrated should be lowest (~$0.83) ← **H2**
- Annotate bars with actual values and % reduction from Black-Scholes

**Why Important**: This is THE main result demonstrating both hypotheses.

---

### 2. Error Distribution Comparison (Histograms/KDE)

**Purpose**: Show how error distributions differ between strategies

**Data Needed**:
- `mc_results['BlackScholes']['errors']` (50,000 values)
- `mc_results['Leland']['errors']` (50,000 values)
- `mc_results['OptimizedLeland']['errors']` (50,000 values)
- `mc_results['MLCalibratedLeland']['errors']` (50,000 values)

**What to Show**:
- Overlapping histograms or kernel density plots
- Black-Scholes should be widest (most spread)
- Leland should be narrower
- Optimized should be even narrower
- ML-Calibrated should be narrowest
- Mark mean and ±1 std for each

**Why Important**: Visual proof that variance decreases from BS → Leland → Optimized → ML.

---

### 3. Optimization Curves Comparison

**Purpose**: Compare grid search vs Bayesian optimization efficiency

**Data Needed**:

For Grid Search:
- `opt_results['A_grid']` (x-axis, 16 points)
- `opt_results['std_errors']` (y-axis)
- `opt_results['A_optimal']` (mark the minimum)

For Bayesian Optimization:
- `ml_results['A_tested']` (x-axis, 30 points)
- `ml_results['std_errors']` (y-axis)
- `ml_results['A_ml']` (mark the minimum)

**What to Show**:
- **Subplot 1**: Grid search curve (uniform sampling of A values)
- **Subplot 2**: Bayesian optimization path (adaptive sampling)
- Mark optimal points on both
- Show that Bayesian converges with fewer evaluations

**Why Important**: Demonstrates ML approach is more efficient than exhaustive search.

---

## Priority 2 Visualizations (Supporting Evidence)

### 4. ABM P&L Evolution Over Time

**Purpose**: Show how hedging performance evolves on real AAPL data

**Data Needed**:
- `abm_results['market_makers']['BlackScholes']['pnl_history']` (504 days)
- `abm_results['market_makers']['Leland']['pnl_history']`
- `abm_results['market_makers']['OptimizedLeland']['pnl_history']`
- `abm_results['market_makers']['MLCalibratedLeland']['pnl_history']`

**What to Show**:
- Time series of P&L for all 4 strategies on same plot
- X-axis: Trading days (0 to 504)
- Y-axis: P&L ($)
- 4 lines (different colors)
- Show final values

**Why Important**: Shows real-world performance on historical data, not just simulations.

---

### 5. ABM Final Results Comparison

**Purpose**: Compare final ABM metrics

**Data Needed**:
- For each strategy: `final_pnl`, `transaction_costs`, `num_hedges`

**What to Show**:
- **Subplot 1**: Bar chart of final P&L (4 bars)
- **Subplot 2**: Bar chart of transaction costs (4 bars)
- **Subplot 3**: Bar chart of number of hedges (4 bars)

**Why Important**: Shows trade-off between P&L, costs, and rebalancing frequency.

---

### 6. Delta Position Dynamics (ABM)

**Purpose**: Show how hedging positions change with price

**Data Needed**:
- `abm_results['market_makers'][strategy]['price_path']` (AAPL price)
- `abm_results['market_makers'][strategy]['position_history']` (delta)

**What to Show**:
- **Subplot 1**: AAPL price over time (504 days)
- **Subplot 2**: Delta position over time for each strategy
- Show how position adjusts as price moves

**Why Important**: Demonstrates actual hedging behavior on real data.

---

## Priority 3 Visualizations (Additional Insights)

### 7. Transaction Costs vs Hedging Error Trade-off

**Purpose**: Show Pareto frontier of cost vs error

**Data Needed**:
- For each strategy: `mean_tc` (x-axis), `std_error` (y-axis)

**What to Show**:
- Scatter plot with 4 points (one per strategy)
- Ideal strategies are bottom-left (low cost, low error)
- Show trend from BS → Leland → Optimized → ML

**Why Important**: Shows strategies improve on both dimensions.

---

### 8. Monte Carlo vs ABM Comparison Table

**Purpose**: Compare performance in both environments

**Data Needed**:

From Monte Carlo:
- `mc_results[strategy]['mean_error']`
- `mc_results[strategy]['std_error']`
- `mc_results[strategy]['mean_tc']`

From ABM:
- `abm_results['market_makers'][strategy]['final_pnl']`
- `abm_results['market_makers'][strategy]['transaction_costs']`

**What to Show**:
- Side-by-side table with columns: Strategy, MC Mean Error, MC Std Error, ABM Final P&L, ABM TC
- Allows comparison of synthetic (MC) vs real data (ABM) performance

**Why Important**: Shows results hold in both GBM and real market conditions.

---

## How to Access the Data

### Running the Full Comparison

1. Run: `python run_full_comparison.py`
2. This executes:
   - Grid search calibration (A_optimal)
   - Bayesian optimization (A_ml)
   - ABM simulation with all 4 strategies
   - Monte Carlo with all 4 strategies
   - Hypothesis testing (H1 and H2)

3. Returns at the end:
   ```
   abm_results, mc_results, A_optimal, A_ml = main()
   ```

4. You can also access intermediate results:
   - Grid search: `opt_results` from `calibrate_all_strategies()`
   - Bayesian opt: `ml_results` from `calibrate_all_strategies()`

### Alternative Scripts (if needed)

- **Test H1 only**: `python test_optimized_leland.py` (3 strategies, Monte Carlo only)
- **Test H2 only**: `python test_ml_leland.py` (4 strategies, Monte Carlo only)
- **Basic comparison**: `python main.py` (2 strategies: BS + Leland only)

**Recommendation**: Use `run_full_comparison.py` - it has everything.

---

## Visualization Checklist

### Must Have (Minimum Viable):
- [ ] Variance reduction bar chart (4 strategies)
- [ ] Error distributions (histograms/KDE)
- [ ] Optimization curves comparison (grid vs Bayesian)

### Should Have (Strong Evidence):
- [ ] ABM P&L evolution over time
- [ ] ABM final results bars (P&L, TC, num_hedges)
- [ ] Transaction costs vs error trade-off

### Nice to Have (Additional Context):
- [ ] Delta position dynamics
- [ ] Monte Carlo vs ABM comparison table

---

## Sensitivity Analysis Data (H3)

### Overview

The sensitivity analysis tests robustness by running simulations across different parameter combinations:
- **Transaction cost (k)**: {0.005, 0.01, 0.015, 0.02}
- **Rebalancing frequency (Δt)**: {1/252, 1/126, 1/63, 1/21} (daily, 2-day, 4-day, 12-day)

### Running Sensitivity Analysis

```bash
python sensitivity_analysis.py
```

This generates 3 CSV files with results.

---

### Sensitivity CSV File Structure

All 3 CSV files (`sensitivity_k.csv`, `sensitivity_dt.csv`, `sensitivity_2d.csv`) have the same structure:

**Columns:**
- `k`: Transaction cost rate
- `dt`: Time step (rebalancing frequency)
- `steps_per_year`: Number of rebalancing steps per year
- `A_leland`: Classical Leland A parameter
- `A_optimal`: Optimized Leland A parameter
- `A_ml`: ML-Calibrated Leland A parameter
- `BS_mean`, `BS_std`, `BS_tc`: Black-Scholes metrics
- `Leland_mean`, `Leland_std`, `Leland_tc`: Classical Leland metrics
- `Opt_mean`, `Opt_std`, `Opt_tc`: Optimized Leland metrics
- `ML_mean`, `ML_std`, `ML_tc`: ML-Calibrated Leland metrics

---

### Priority 4 Visualizations (Sensitivity Analysis - H3)

#### 9. Variance vs Transaction Cost (k)

**Purpose**: Show how variance changes with transaction costs

**Data Source**: `sensitivity_k.csv`

**Data Needed**:
- X-axis: `k` values (0.005, 0.01, 0.015, 0.02)
- Y-axis: `BS_std`, `Leland_std`, `Opt_std`, `ML_std`

**What to Show**:
- Line plot with 4 lines (one per strategy)
- All strategies increase with k
- ML-Calibrated should always be lowest
- Relative ordering should remain: BS > Leland > Optimized > ML

**Why Important**: Tests if H1 and H2 hold across different transaction cost levels

---

#### 10. Variance vs Rebalancing Frequency (Δt)

**Purpose**: Show how variance changes with rebalancing frequency

**Data Source**: `sensitivity_dt.csv`

**Data Needed**:
- X-axis: `steps_per_year` (21, 63, 126, 252)
- Y-axis: `BS_std`, `Leland_std`, `Opt_std`, `ML_std`

**What to Show**:
- Line plot with 4 lines
- More frequent rebalancing should reduce variance
- Relative ordering should remain consistent

**Why Important**: Tests if H1 and H2 hold across different rebalancing frequencies

---

#### 11. 2D Heatmap: Variance Surface (k, Δt)

**Purpose**: Show variance landscape across full parameter space

**Data Source**: `sensitivity_2d.csv`

**Data Needed**:
- X-axis: `k` values
- Y-axis: `steps_per_year`
- Color: `std_error` for each strategy

**What to Show**:
- 4 heatmaps (one per strategy) in 2x2 grid
- Use same color scale for all 4 to allow comparison
- Darker colors = higher variance (worse)
- ML-Calibrated should be lightest overall

**Why Important**: Comprehensive view of parameter sensitivity, shows interaction between k and Δt

---

#### 12. Hypothesis Robustness Bar Chart

**Purpose**: Show percentage of parameter combinations where H1 and H2 hold

**Data Source**: Calculate from `sensitivity_2d.csv`

**Calculation**:
- For each row: H1 holds if `Opt_std < Leland_std`
- For each row: H2 holds if `ML_std < Opt_std`
- Calculate percentage of successes

**What to Show**:
- 2 bars showing robustness percentage
- Annotate with count (e.g., "15/16 cases")

**Why Important**: Quantifies hypothesis robustness - do H1 and H2 ALWAYS hold?

**Expected**: H1 ≈ 90-100%, H2 ≈ 75-100%

---

#### 13. A Parameter Evolution

**Purpose**: Show how calibrated A parameters change with k and dt

**Data Source**: `sensitivity_k.csv` and `sensitivity_dt.csv`

**What to Show**:
- **Subplot 1**: A parameters vs k (3 lines: A_leland, A_optimal, A_ml)
- **Subplot 2**: A parameters vs Δt (3 lines)

**Why Important**: Shows how optimal A values adapt to different parameters

---

### Sensitivity Analysis Visualization Checklist

**Must Have (H3 Testing):**
- [ ] Variance vs k (line plot)
- [ ] Variance vs Δt (line plot)
- [ ] Hypothesis robustness bar chart

**Should Have:**
- [ ] 2D heatmap (k, Δt) for all 4 strategies
- [ ] A parameter evolution plots

**Nice to Have:**
- [ ] Transaction cost trade-off surface

---

## Key Metrics Summary

### For H1 Testing (Optimized vs Classical):
- **Metric**: `std_error`
- **Comparison**: `mc_results['OptimizedLeland']['std_error']` vs `mc_results['Leland']['std_error']`
- **Expected**: Optimized should be 5-10% lower
- **Success**: H1 confirmed if Optimized < Leland

### For H2 Testing (ML vs Optimized):
- **Metric**: `std_error`
- **Comparison**: `mc_results['MLCalibratedLeland']['std_error']` vs `mc_results['OptimizedLeland']['std_error']`
- **Expected**: ML should be 1-3% lower
- **Success**: H2 confirmed if ML < Optimized

### Overall Performance:
- **Baseline**: `mc_results['BlackScholes']['std_error']` ≈ $2.50
- **Target**: `mc_results['MLCalibratedLeland']['std_error']` ≈ $0.83
- **Total Reduction**: ~67% variance reduction

---

## Important Notes

### 1. Data Sizes:
- ABM: 504 time steps (AAPL trading days 2021-2023)
- Monte Carlo: 50,000 simulations per strategy
- Grid Search: ~16 evaluations (A values from 0 to 1.5)
- Bayesian Opt: ~30 evaluations (10 initial + 20 iterations)

### 2. Variable Naming:
- `std_error` = standard deviation of hedging error (THE key metric)
- `mean_error` = average hedging error (bias check)
- `final_pnl` = final P&L from ABM (single value per strategy)
- `errors` = full array of all Monte Carlo errors (50,000 values)

### 3. Strategy Naming in Results:
- Dictionary keys use: `'BlackScholes'`, `'Leland'`, `'OptimizedLeland'`, `'MLCalibratedLeland'`
- All exactly as shown (case-sensitive)

### 4. Missing Data Handling:
- If `A_optimal` or `A_ml` is None, those strategies weren't run
- Check `if 'OptimizedLeland' in mc_results:` before accessing
- Check `if 'OptimizedLeland' in abm_results['market_makers']:` before accessing

---

## Files to Delete (Visualization Files)

Since you're creating new visualizations, you can delete these old files:

### Jupyter Notebooks:
- `compare_strategies.ipynb` (if exists)
- `optimization_analysis.ipynb` (if exists)
- `sensitivity_analysis.ipynb` (if exists)

### PNG Files:
- `optimization_results.png` (if exists)
- `ml_optimization_results.png` (if exists)
- `comparison_plots.png` (if exists)
- Any other `.png` files in the project root

**Note**: Don't delete `.py` files - they contain the core logic you need.

---

## Suggested Workflow

1. **Run the script**:
   ```bash
   python run_full_comparison.py
   ```

2. **Capture the results** at the end of `main()`:
   - Modify the script to save results to pickle/JSON
   - Or work directly in Jupyter notebook that imports and runs `main()`

3. **Start with Priority 1** visualizations:
   - These prove H1 and H2 directly
   - Most important for presentation

4. **Add Priority 2** if time allows:
   - Provides supporting evidence
   - Shows real-world performance (ABM)

5. **Add Priority 3** if time allows:
   - Nice to have but not critical

---

## Understanding the Results

### Expected Standard Deviations (Monte Carlo):
- Black-Scholes: ~$2.40-2.60 (high variance)
- Classical Leland: ~$0.90-1.00 (much better)
- Optimized Leland: ~$0.82-0.90 (improved further)
- ML-Calibrated: ~$0.80-0.85 (best performance)

### Expected ABM Final P&L (AAPL Real Data):
- All strategies: $-15 to $+5 (depends on AAPL path)
- ML-Calibrated should have closest to $0 (best replication)
- Transaction costs: $5-8 for all strategies

### Calibrated A Values:
- Classical Leland A: ~0.36 (from formula)
- Optimized A*: ~0.40-0.50 (from grid search)
- ML-Calibrated A*_ml: ~0.45-0.55 (from Bayesian opt)

---

## Questions to Answer with Visualizations

1. **Does Optimized Leland reduce variance vs Classical Leland?** (H1)
   - Answer with: Variance reduction bar chart
   - Answer with: Error distributions

2. **Does ML-Calibrated reduce variance vs Optimized?** (H2)
   - Answer with: Variance reduction bar chart
   - Answer with: Error distributions

3. **Is Bayesian optimization more efficient than grid search?**
   - Answer with: Optimization curves comparison
   - Show fewer evaluations needed for ML

4. **Do results hold on real data (not just simulations)?**
   - Answer with: ABM P&L evolution
   - Answer with: ABM final results comparison

5. **What's the overall improvement from BS to ML-Calibrated?**
   - Answer with: Overall variance reduction (~67%)
   - Answer with: All visualizations together

---

## Final Tips

1. **Focus on `std_error`**: This is the metric that matters for H1 and H2
2. **Use consistent colors**: Same color for each strategy across all plots
3. **Add annotations**: Show exact values and % improvements on charts
4. **Label clearly**: Users should understand without reading code
5. **Show uncertainty**: Error bars or confidence intervals where appropriate
6. **Compare visually**: Put strategies side-by-side for easy comparison

---

**Good luck with visualization! The data is all ready - just need to plot it!**

**Contact**: If you need clarification on any data structure, check:
- `PROJECT_STRUCTURE.md` - Overall architecture
- `RUN_PROJECT.md` - How to run scripts
- `ML_CALIBRATED_README.md` - ML implementation details
