# 🚀 How to Run the Complete Project

## Quick Navigation
- [Environment Setup](#step-1-environment-setup)
- [Quick Tests](#step-2-quick-tests)
- [Main Simulations](#step-3-main-simulations)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Step 1: Environment Setup

### 1.1 Activate Virtual Environment

```bash
cd /Users/Admin/leland_abm_project
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `numpy`, `pandas`, `matplotlib`
- `yfinance` - market data download
- `scikit-learn`, `scipy` - ML optimization (optional, will fallback to grid search)

---

## Step 2: Quick Tests

### Test 1: Agents ✅
```bash
python agents.py
```

**Expected Output:**
```
Testing agents...
Fundamentalist at price $95: order = 0.16 (should be BUY)
NoiseTrader: order = 0.53 (random)
OptionTrader bought option for $10.00
✓ All agents working!
```

### Test 2: Black-Scholes ✅
```bash
python black_scholes.py
```

### Test 3: Market Data Loading ✅
```bash
python market.py
```

---

## Step 3: Main Simulations

You have **4 options** for running the project, from basic to comprehensive:

---

### Option A: Basic Model (BS + Leland Only)

**When to use**: Quick verification that everything works

```bash
python main.py
```

**What it does:**
1. ✅ Downloads AAPL data (2021-2023)
2. ✅ Runs ABM with real data (BS + Leland)
3. ✅ Runs Monte Carlo (50,000 simulations, BS + Leland)
4. ✅ Exports `results_summary.csv`

**Runtime:** ~5 minutes

**Strategies tested:** 2 (Black-Scholes, Classical Leland)

---

### Option B: Test H1 (Optimized Leland)

**When to use**: Test first hypothesis (Optimized vs Classical)

```bash
python test_optimized_leland.py
```

**What it does:**
1. ✅ Calibrates optimal A* (5,000 simulations, grid search)
2. ✅ Tests 3 strategies in Monte Carlo (BS, Leland, Optimized)
3. ✅ Tests Hypothesis H1
4. ✅ Generates results data

**Runtime:** ~10-15 minutes

**Strategies tested:** 3 (BS, Classical Leland, Optimized Leland)

**Limitation:** Monte Carlo only (no ABM with Optimized Leland)

---

### Option C: Test H2 (ML-Calibrated Leland)

**When to use**: Test second hypothesis (ML-Calibrated vs Optimized)

```bash
python test_ml_leland.py
```

**What it does:**
1. ✅ Calibrates Optimized A* (grid search)
2. ✅ Calibrates ML A*_ml (Bayesian Optimization + GP)
3. ✅ Tests 4 strategies in Monte Carlo (BS, Leland, Optimized, ML-Calibrated)
4. ✅ Tests Hypothesis H2
5. ✅ Generates comprehensive results

**Runtime:** ~15-20 minutes

**Strategies tested:** 4 (BS, Classical Leland, Optimized, ML-Calibrated)

**Limitation:** Monte Carlo only (no ABM with all 4 strategies)

---

### Option D: ⭐ Full Comparison (ALL 4 Strategies) - **RECOMMENDED**

**When to use**: Complete project demonstration, presentation

```bash
python run_full_comparison.py
```

**What it does:**
1. ✅ Calibrates Optimized A* (3,000 simulations, grid search)
2. ✅ Calibrates ML A*_ml (30 evaluations, Bayesian Optimization)
3. ✅ ABM on real AAPL data with **ALL 4 strategies**:
   - Black-Scholes Market Maker
   - Classical Leland Market Maker
   - Optimized Leland Market Maker
   - **ML-Calibrated Leland Market Maker**
4. ✅ Monte Carlo (50,000 simulations) with **ALL 4 strategies**
5. ✅ Compares **ABM vs Monte Carlo**
6. ✅ Tests **both H1 and H2**
7. ✅ Outputs comprehensive terminal analysis

**Runtime:** ~15-20 minutes

**Strategies tested:** 4 (BS, Classical Leland, Optimized Leland, ML-Calibrated Leland)

**Advantages:**
- ✅ Complete comparison of all 4 strategies
- ✅ Both ABM (real data) AND Monte Carlo (GBM)
- ✅ Both H1 and H2 testing
- ✅ Most comprehensive results

---

### Option E: ⭐ Sensitivity Analysis (H3) - **ADVANCED**

**When to use**: Test robustness of strategies to parameter changes

```bash
python sensitivity_analysis.py
```

**What it does:**
1. ✅ Tests 3 types of sensitivity:
   - **Analysis 1**: Vary k (transaction costs) ∈ {0.005, 0.01, 0.015, 0.02}
   - **Analysis 2**: Vary Δt (rebalancing frequency) ∈ {daily, 2-day, 4-day, 12-day}
   - **Analysis 3**: Full 2D grid (both k and Δt)
2. ✅ For each parameter combination:
   - Recalibrates A_optimal and A_ml
   - Runs Monte Carlo (5,000-10,000 simulations)
   - Tests H1 and H2 robustness
3. ✅ Exports 3 CSV files:
   - `sensitivity_k.csv`
   - `sensitivity_dt.csv`
   - `sensitivity_2d.csv`
4. ✅ Terminal output shows hypothesis robustness

**Runtime:** ~30-45 minutes (Analysis 3 is slow)

**Strategies tested:** 4 (BS, Classical Leland, Optimized Leland, ML-Calibrated Leland)

**Purpose:**
- Determine if H1 and H2 hold across different parameter ranges
- Identify optimal parameter ranges for each strategy
- Test robustness to market conditions

**Output:**
- Hypothesis robustness percentage (e.g., "H1 confirmed in 15/16 cases")
- Variance comparison tables for all parameter combinations
- CSV files for visualization

---

## Comparison Table

| Script | Strategies | ABM | Monte Carlo | H1 | H2 | Runtime | Recommended For |
|--------|-----------|-----|-------------|----|----|---------|-----------------|
| `main.py` | 2 (BS, Leland) | ✅ | ✅ | ❌ | ❌ | ~5 min | Quick check |
| `test_optimized_leland.py` | 3 (+ Optimized) | ❌ | ✅ | ✅ | ❌ | ~10 min | H1 testing only |
| `test_ml_leland.py` | 4 (+ ML) | ❌ | ✅ | ✅ | ✅ | ~15 min | H2 testing only |
| **`run_full_comparison.py`** | **4 (All)** | **✅** | **✅** | **✅** | **✅** | **~15 min** | **Project/Presentation** ⭐ |
| **`sensitivity_analysis.py`** | **4 (All)** | **❌** | **✅** | **✅** | **✅** | **~30-45 min** | **Robustness Testing (H3)** ⭐⭐ |

---

## Expected Terminal Output

### Example from `run_full_comparison.py`:

```
================================================================================
                 FULL STRATEGY COMPARISON WITH ML
           BS vs Leland vs Optimized vs ML-Calibrated
                       ABM + Monte Carlo
================================================================================

STEP 1: CALIBRATING BOTH STRATEGIES
================================================================================
1A. OPTIMIZED LELAND (Grid Search)
----------------------------------------------------------------------
  Optimal A*:          0.4500
  Classical Leland A:  0.3579
  Improvement:         7.39%

1B. ML-CALIBRATED LELAND (Bayesian Optimization)
----------------------------------------------------------------------
  ML-Optimal A*:       0.4650
  ML Evaluations:      30

CALIBRATION SUMMARY
================================================================================
  Classical Leland A:      0.3579 (formula)
  Optimized Leland A*:     0.4500 (grid search, 16 evals)
  ML-Calibrated A*_ml:     0.4650 (Bayesian opt, 30 evals)
================================================================================

STEP 2: ABM WITH ALL 4 STRATEGIES (REAL DATA)
================================================================================
✓ ABM Model created
   Total agents: 19
   Simulation days: 504
   Optimized Leland A*: 0.4500
   ML-Calibrated A*_ml: 0.4650

Running ABM on real data...
Progress: 50...100...150...200...250...300...350...400...450...500...504 Done!

ABM RESULTS (Real AAPL Data)
--------------------------------------------------------------------------------
Strategy                  Final P&L       Trans. Costs    # Hedges
--------------------------------------------------------------------------------
BlackScholes              $  -10.01      $    7.41            98
Leland                    $   -9.72      $    5.69            98
OptimizedLeland           $   -9.50      $    5.45            98
MLCalibratedLeland        $   -9.35      $    5.30            98

STEP 3: MONTE CARLO WITH ALL 4 STRATEGIES
================================================================================
Running 50,000 Monte Carlo simulations...
  Progress: 5,000/50,000 (10%)
  Progress: 10,000/50,000 (20%)
  ...
  Progress: 50,000/50,000 (100%)
✓ Monte Carlo simulations complete!

MONTE CARLO RESULTS (GBM Simulations)
--------------------------------------------------------------------------------
Strategy                  Mean Error      Std Error       Avg TC
--------------------------------------------------------------------------------
BlackScholes              $ -0.1456      $  2.5412      $   7.00
Leland                    $ -0.1234      $  0.9176      $   6.02
OptimizedLeland           $ -0.0987      $  0.8456      $   5.89
MLCalibratedLeland        $ -0.0912      $  0.8301      $   5.85

================================================================================
                       HYPOTHESIS TESTING: H1 & H2
================================================================================

HYPOTHESIS H1: Optimized Leland reduces variance vs Classical Leland
================================================================================
  Black-Scholes Std:       $2.5412
  Classical Leland Std:    $0.9176
  Optimized Leland Std:    $0.8456

  Improvement (Opt vs Classical): +7.85%

  ✅ H1 CONFIRMED: Optimized Leland reduces variance!

HYPOTHESIS H2: ML-Calibrated Leland reduces variance vs Optimized
================================================================================
  Optimized Leland Std:    $0.8456
  ML-Calibrated Std:       $0.8301

  Improvement (ML vs Optimized): +1.83%

  ✅ H2 CONFIRMED: ML-Calibrated Leland reduces variance!

OVERALL VARIANCE REDUCTION
================================================================================
  Black-Scholes:           $2.5412 (baseline)
  Classical Leland:        $0.9176 (-63.9%)
  Optimized Leland:        $0.8456 (-66.7%)
  ML-Calibrated Leland:    $0.8301 (-67.3%)
================================================================================

✓ FULL COMPARISON COMPLETE!
================================================================================
```

---

## Configuration

### Modify Parameters

Edit `config.py` to customize:

```python
@dataclass
class Config:
    # Market Data
    ticker: str = "AAPL"           # ← Change ticker (SPY, MSFT, etc.)
    start_date: str = "2021-01-01"
    end_date: str = "2023-12-31"

    # Option Parameters
    time_to_maturity: float = 1.0   # ← Change maturity (years)
    risk_free_rate: float = 0.05    # ← Change interest rate

    # Transaction Costs
    k_transaction: float = 0.01     # ← Change k (0.005, 0.02, etc.)

    # Rebalancing
    rebalance_frequency: int = 5    # ← Change frequency (1, 10, 20 days)

    # Monte Carlo
    mc_simulations: int = 50000     # ← Reduce for faster testing
```

After changing:
```bash
python run_full_comparison.py  # Run with new parameters
```

---

## 🐛 Troubleshooting

### Error: "No module named 'yfinance'"
```bash
pip install yfinance
```

### Error: "No module named 'sklearn'"
```bash
pip install scikit-learn scipy
```
**Note:** ML optimization will automatically fall back to grid search if sklearn is not installed.

### Error: "No data downloaded for AAPL"
- Check internet connection
- Try different dates in `config.py`
- Try different ticker (SPY, MSFT)

### Error: "python: command not found"
Use `python3` instead:
```bash
python3 run_full_comparison.py
```

### Execution is too slow
Reduce simulations in `config.py`:
```python
mc_simulations: int = 10000  # Instead of 50000
```

---

## 📊 Output Files

| File | Generated By | Description |
|------|--------------|-------------|
| `results_summary.csv` | `main.py` | Basic results (BS vs Leland) |
| `sensitivity_k.csv` | `sensitivity_analysis.py` | Results for varying k (transaction costs) |
| `sensitivity_dt.csv` | `sensitivity_analysis.py` | Results for varying Δt (rebalancing frequency) |
| `sensitivity_2d.csv` | `sensitivity_analysis.py` | Full 2D parameter grid results |
| Terminal output | All scripts | Comprehensive text results |

**Note:** Visualization files (`.png`) are handled by another team member.

---

## 📈 What Happens Next?

After running `run_full_comparison.py`:

1. ✅ Review terminal output for H1 and H2 results
2. ✅ Check calibration values (A*, A*_ml)
3. ✅ Analyze variance reduction percentages
4. ✅ Verify both hypotheses confirmed
5. ✅ Run Sensitivity Analysis (H3) - `python sensitivity_analysis.py`
6. ⏭️ Prepare presentation with team member (visualization)

---

## 📞 Need Help?

If something doesn't work:
1. ✅ Check `requirements.txt` installed
2. ✅ Check virtual environment activated
3. ✅ Check Python version ≥ 3.8
4. ✅ Review error logs carefully

---

**Created:** 2025-12-11
**Version:** 2.0 (with ML-Calibrated Leland)
**Status:** ✅ Ready to Run
