# Project Architecture & Structure

## 📐 Overview

This document explains the project architecture, module relationships, and data flow.

---

## 🗂️ Directory Structure

```
leland_abm_project/
│
├── Documentation/
│   ├── README.md                      # Project overview & quick start
│   ├── RUN_PROJECT.md                 # Detailed execution guide
│   ├── PROJECT_STRUCTURE.md           # ← This file (architecture)
│   ├── OPTIMIZED_LELAND_README.md     # H1 implementation details
│   └── ML_CALIBRATED_README.md        # H2 implementation details
│
├── Configuration/
│   └── config.py                      # All project parameters
│
├── Core Modules/
│   ├── black_scholes.py               # BS pricing, Greeks, Leland volatility
│   ├── agents.py                      # All agent classes
│   ├── market.py                      # Market data & environment
│   ├── model_abm.py                   # Agent-Based Model
│   └── model_monte_carlo.py           # Monte Carlo simulation
│
├── Optimization Modules/
│   ├── optimization.py                # Grid search (H1)
│   └── ml_optimization.py             # Bayesian Optimization (H2)
│
├── Execution Scripts/
│   ├── main.py                        # Basic comparison (BS vs Leland)
│   ├── test_optimized_leland.py       # H1 test
│   ├── test_ml_leland.py              # H2 test
│   └── run_full_comparison.py         # Full comparison (all 4 strategies)
│
├── Utilities/
│   └── analysis.py                    # Analysis helper functions
│
└── Environment/
    ├── requirements.txt               # Python dependencies
    └── .venv/                         # Virtual environment
```

---

## 🧩 Module Dependencies

```
config.py
   ↓
black_scholes.py
   ↓
agents.py ←──────────────┐
   ↓                      │
market.py                 │
   ↓                      │
model_abm.py ─────────────┤
model_monte_carlo.py ─────┤
   ↓                      │
optimization.py ──────────┤
ml_optimization.py ───────┤
   ↓                      │
main.py                   │
test_optimized_leland.py ─┤
test_ml_leland.py ────────┤
run_full_comparison.py ───┘
```

---

## 📦 Module Descriptions

### **Configuration Module**

#### `config.py`
**Purpose**: Centralized configuration for all parameters

**Key Components**:
```python
@dataclass
class Config:
    # Market Data
    ticker: str = "AAPL"
    start_date: str = "2021-01-01"
    end_date: str = "2023-12-31"

    # Option Parameters
    time_to_maturity: float = 1.0
    risk_free_rate: float = 0.05
    strike_offset: float = 0.0  # ATM

    # Transaction Costs
    k_transaction: float = 0.01  # 1%

    # Rebalancing
    rebalance_frequency: int = 5  # Every 5 days

    # Agent Parameters
    n_fundamentalist_low: int = 3
    n_fundamentalist_medium: int = 3
    n_fundamentalist_high: int = 3
    n_noise_traders: int = 5

    # Monte Carlo
    mc_simulations: int = 50000
    mc_steps_per_year: int = 252
```

**Used By**: All modules

---

### **Core Modules**

#### `black_scholes.py`
**Purpose**: Black-Scholes formulas and Greeks

**Key Classes**:
```python
class BlackScholesUtils:
    def call_price(S, K, T, r, sigma)      # BS call option price
    def delta(S, K, T, r, sigma)            # ∂C/∂S
    def gamma(S, K, T, r, sigma)            # ∂²C/∂S²
    def vega(S, K, T, r, sigma)             # ∂C/∂σ
    def leland_volatility(sigma, k, dt, short_gamma)  # σ_modified
```

**Used By**: `agents.py`, `optimization.py`, `ml_optimization.py`

---

#### `agents.py`
**Purpose**: All agent types in the ABM

**Key Classes**:

1. **Agent** (Base class)
   ```python
   class Agent:
       agent_id: str
       cash: float
       stock_position: float
       action_history: list

       def get_order(market_state) → float
       def log_action(action, details)
   ```

2. **Fundamentalist** (Value trader)
   ```python
   class Fundamentalist(Agent):
       fundamental_value: float
       aggressiveness: float

       # Order = aggressiveness × (fundamental_value - price)
       def get_order(market_state) → float
   ```

3. **NoiseTrader** (Random trader)
   ```python
   class NoiseTrader(Agent):
       noise_level: float

       # Order = random.normal(0, noise_level)
       def get_order(market_state) → float
   ```

4. **MarketMaker** (Delta hedger)
   ```python
   class MarketMaker(Agent):
       use_leland: bool
       k_transaction: float
       rebalance_frequency: int

       def sell_option(price, vol) → premium
       def get_order(market_state) → delta_hedge
       def settle_option(final_price)
       def get_pnl(current_price) → float
   ```

5. **OptimizedLelandMarketMaker** (Grid-search calibrated)
   ```python
   class OptimizedLelandMarketMaker(MarketMaker):
       A_optimal: float  # From grid search

       # Uses σ_hedge = σ × √(1 + A_optimal)
   ```

6. **MLCalibratedLelandMarketMaker** (ML calibrated)
   ```python
   class MLCalibratedLelandMarketMaker(MarketMaker):
       A_ml: float  # From Bayesian Optimization

       # Uses σ_hedge = σ × √(1 + A_ml)
   ```

7. **OptionTrader** (Buyer)
   ```python
   class OptionTrader(Agent):
       strike: float
       long_option_position: int

       def buy_option(premium)
       def settle_option(final_price)
   ```

**Used By**: `model_abm.py`

---

#### `market.py`
**Purpose**: Market data download and environment

**Key Classes**:

1. **RealDataMarket**
   ```python
   class RealDataMarket:
       real_prices: np.ndarray        # Historical prices
       realized_volatility: float     # Historical volatility
       current_step: int
       n_steps: int
       trade_history: list

       def get_price() → float
       def get_volatility() → float
       def get_market_state() → dict
       def step()                     # Move to next day
       def is_finished() → bool
       def log_trade(agent_id, action, quantity, price)
   ```

2. **download_market_data()**
   ```python
   def download_market_data(ticker, start_date, end_date) → dict:
       # Returns: {
       #     'prices': np.ndarray,
       #     'returns': np.ndarray,
       #     'volatility': float
       # }
   ```

**Used By**: `model_abm.py`

---

#### `model_abm.py`
**Purpose**: Agent-Based Model implementation

**Key Class**:
```python
class ABMModel:
    config: Config
    market: RealDataMarket
    agents: List[Agent]
    A_optimal: float (optional)
    A_ml: float (optional)

    mm_blackscholes: MarketMaker
    mm_leland: MarketMaker
    mm_optimized: OptimizedLelandMarketMaker (optional)
    mm_ml: MLCalibratedLelandMarketMaker (optional)

    option_trader_bs: OptionTrader
    option_trader_leland: OptionTrader
    option_trader_optimized: OptionTrader (optional)
    option_trader_ml: OptionTrader (optional)

    def __init__(config, market_data, A_optimal=None, A_ml=None)
    def _create_agents()           # Create all agents
    def initialize()               # MMs sell options
    def run()                      # Run full simulation
    def step()                     # One time step
    def finalize()                 # Option expiration
    def get_results() → dict       # Collect results
```

**Data Flow**:
```
1. Initialize: MMs sell options to OptionTraders
2. Loop (each day):
   a. Get market state (price, volatility)
   b. All agents get_order()
   c. Market logs trades
   d. Market.step() (next day)
   e. Update MMs P&L
3. Finalize: Option expiration, settle positions
4. Return results
```

**Used By**: Execution scripts

---

#### `model_monte_carlo.py`
**Purpose**: Monte Carlo simulation for statistical testing

**Key Functions**:
```python
def simulate_stock_path(S0, r, sigma, T, dt) → np.ndarray:
    # Geometric Brownian Motion:
    # dS = r×S×dt + σ×S×dW

def run_monte_carlo(config, initial_price, strike, volatility,
                    n_simulations) → dict:
    # Returns distributions of hedging errors
```

**Data Flow**:
```
For each simulation (1 to n_simulations):
    1. Generate GBM stock path
    2. Simulate delta hedging (BS/Leland/Optimized/ML)
    3. Calculate hedging error = Portfolio - Payoff
    4. Record error and transaction costs

Aggregate:
    - Mean error (bias)
    - Std error (variance)
    - Mean transaction costs
```

**Used By**: Execution scripts

---

### **Optimization Modules**

#### `optimization.py`
**Purpose**: Grid search optimization for H1

**Key Functions**:
```python
def simulate_hedging_with_A(S_path, K, r, sigma, dt, k, A) → (error, tc):
    # Simulate hedging with given A parameter
    # Returns final hedging error and transaction costs

def optimize_A_parameter(S0, K, T, r, sigma, k, dt,
                        n_simulations, A_grid) → (A_optimal, results):
    # Grid search over A values
    # For each A:
    #     Run n_simulations Monte Carlo paths
    #     Calculate mean and std of errors
    # Return A* = argmin std(errors)
```

**Algorithm**:
```
1. Define grid: A ∈ [0, 0.1, 0.2, ..., 1.5]  (16 points)
2. For each A:
       Run 3,000 Monte Carlo simulations
       Calculate Std[Error]
3. A_optimal = A with minimum Std[Error]
```

**Used By**: `test_optimized_leland.py`, `run_full_comparison.py`

---

#### `ml_optimization.py`
**Purpose**: Bayesian Optimization for H2

**Key Functions**:
```python
def simulate_hedging_with_A_ml(S_path, K, r, sigma, dt, k, A) → (error, tc):
    # Same as optimization.py (for clarity)

def optimize_A_with_ML(S0, K, T, r, sigma, k, dt,
                       n_initial, n_iterations,
                       n_simulations_per_eval,
                       acquisition) → (A_ml, results):
    # Bayesian Optimization with Gaussian Process
    # Phase 1: Random exploration (n_initial points)
    # Phase 2: GP-guided search (n_iterations)
    # Return A_ml with lowest Std[Error]
```

**Algorithm**:
```
Phase 1: Random Exploration (10 points)
   - Sample A uniformly from [0, 2.0]
   - Evaluate Std[Error] for each A
   - Build initial GP model

Phase 2: Bayesian Optimization (20 iterations)
   For each iteration:
       1. Fit Gaussian Process to (A, Std[Error]) data
       2. Acquisition function suggests next A to try
          (Expected Improvement or UCB)
       3. Evaluate Std[Error] at new A
       4. Update GP model

Return: A_ml with minimum Std[Error] among all evaluated points
```

**Advantages over Grid Search**:
- Adaptive: Focuses on promising regions
- Efficient: ~30 evaluations vs 16-21 for grid
- Uncertainty: GP provides confidence intervals

**Fallback**: If sklearn not installed, falls back to grid search

**Used By**: `test_ml_leland.py`, `run_full_comparison.py`

---

### **Execution Scripts**

#### `main.py`
**Purpose**: Basic comparison (BS vs Leland)

**Flow**:
```
1. Load config
2. Run ABM:
   - Download AAPL data
   - Create ABMModel with BS and Leland MMs
   - Run simulation
   - Collect results
3. Run Monte Carlo:
   - 50,000 simulations
   - BS and Leland strategies
   - Collect distributions
4. Compare results
5. Export to CSV
```

**Runtime**: ~5 minutes

---

#### `test_optimized_leland.py`
**Purpose**: Test H1 (Optimized vs Classical)

**Flow**:
```
1. Calibrate Optimized Leland:
   - Grid search (16 points, 3000 sims/point)
   - Find A_optimal
2. Run Monte Carlo with 3 strategies:
   - Black-Scholes (A=0)
   - Classical Leland (A from formula)
   - Optimized Leland (A_optimal)
3. Compare Std[Error]:
   - Test H1: Is Std[Optimized] < Std[Classical]?
4. Output results
```

**Runtime**: ~10 minutes

---

#### `test_ml_leland.py`
**Purpose**: Test H2 (ML-Calibrated vs Optimized)

**Flow**:
```
1. Calibrate Optimized Leland (grid search)
2. Calibrate ML-Calibrated Leland (Bayesian Opt)
3. Run Monte Carlo with 4 strategies:
   - Black-Scholes
   - Classical Leland
   - Optimized Leland
   - ML-Calibrated Leland
4. Compare Std[Error]:
   - Test H2: Is Std[ML] < Std[Optimized]?
5. Output results
```

**Runtime**: ~15 minutes

---

#### `run_full_comparison.py` ⭐
**Purpose**: Complete project comparison (all 4 strategies)

**Flow**:
```
1. Calibrate both:
   - Optimized Leland (grid search)
   - ML-Calibrated Leland (Bayesian Opt)

2. Run ABM with ALL 4 strategies:
   - Download AAPL data
   - Create ABMModel with all 4 MMs
   - Run on real data
   - Collect results

3. Run Monte Carlo with ALL 4 strategies:
   - 50,000 simulations
   - All 4 hedging strategies
   - Collect distributions

4. Compare ABM vs Monte Carlo

5. Test both hypotheses:
   - H1: Optimized vs Classical
   - H2: ML-Calibrated vs Optimized

6. Output comprehensive results
```

**Runtime**: ~15-20 minutes

---

### **Utility Modules**

#### `analysis.py`
**Purpose**: Helper functions for analysis

**Key Functions**:
```python
def analyze_abm_results(results):
    # Print ABM results in formatted table

def calculate_statistics(errors):
    # Calculate mean, std, percentiles, etc.

def compare_strategies(strategy1_results, strategy2_results):
    # Statistical comparison
```

---

## 🔄 Data Flow Diagram

### **ABM Flow**:
```
Config
  ↓
Download Market Data (yfinance)
  ↓
Create ABMModel(config, market_data, A_optimal, A_ml)
  ↓
Initialize:
  - Create agents (Fundamentalists, NoiseTraders, MMs, OptionTraders)
  - MMs sell options
  ↓
Run Loop (each day):
  - Get market state
  - Agents decide orders
  - Log trades
  - Market step
  - Update P&L
  ↓
Finalize:
  - Option expiration
  - Settle positions
  ↓
Collect Results:
  - Final P&L per strategy
  - Transaction costs
  - Number of hedges
  - P&L history
```

### **Monte Carlo Flow**:
```
Config
  ↓
Generate Stock Path (GBM)
  ↓
For each simulation:
  For each strategy:
    1. Initialize portfolio
    2. Loop (each time step):
       - Calculate target delta
       - Rebalance portfolio
       - Pay transaction costs
    3. At expiration:
       - Calculate option payoff
       - Close position
       - Calculate hedging error
  ↓
Aggregate Results:
  - Distribution of errors
  - Mean error (bias)
  - Std error (variance)
  - Mean transaction costs
```

### **Optimization Flow (Grid Search)**:
```
Config
  ↓
Define A grid: [0, 0.1, 0.2, ..., 1.5]
  ↓
For each A in grid:
  Run Monte Carlo (3000 sims)
  Calculate Std[Error]
  ↓
Find A_optimal = argmin Std[Error]
```

### **Optimization Flow (Bayesian)**:
```
Config
  ↓
Phase 1: Random Exploration (10 points)
  Sample A uniformly
  Evaluate each A (1000 sims)
  Build GP model
  ↓
Phase 2: Bayesian Optimization (20 iterations)
  For each iteration:
    GP predicts Std[Error] for all A
    Acquisition function suggests next A
    Evaluate Std[Error] at new A
    Update GP model
  ↓
Find A_ml = argmin Std[Error]
```

---

## 🧪 Testing Strategy

### **Unit Tests** (Individual Module Testing)
- `python agents.py` - Test agents
- `python black_scholes.py` - Test BS formulas
- `python market.py` - Test data download
- `python model_monte_carlo.py` - Test GBM simulation

### **Integration Tests** (Full Workflow)
- `python main.py` - Test ABM + MC (BS vs Leland)
- `python test_optimized_leland.py` - Test H1
- `python test_ml_leland.py` - Test H2
- `python run_full_comparison.py` - Test complete system

---

## 📊 Results Structure

### **ABM Results**:
```python
{
    'config': Config,
    'ticker': 'AAPL',
    'real_prices': np.ndarray,
    'strike': float,
    'final_price': float,
    'market_makers': {
        'BlackScholes': {
            'final_pnl': float,
            'transaction_costs': float,
            'pnl_history': list,
            'num_hedges': int
        },
        'Leland': {...},
        'OptimizedLeland': {...} (if A_optimal provided),
        'MLCalibratedLeland': {...} (if A_ml provided)
    },
    'option_traders': {
        'BlackScholes': {
            'final_pnl': float,
            'premium_paid': float
        },
        ...
    },
    'trades': list
}
```

### **Monte Carlo Results**:
```python
{
    'BlackScholes': {
        'mean_error': float,
        'std_error': float,
        'mean_tc': float,
        'errors': np.ndarray (50000 values)
    },
    'Leland': {...},
    'OptimizedLeland': {...},
    'MLCalibratedLeland': {...}
}
```

---

## 🎯 Key Design Decisions

### **Why Agent-Based Model?**
- Tests strategies on **real market data** (not just GBM)
- Models **heterogeneous agents** (fundamentalists, noise traders)
- Captures **market microstructure** effects
- Complements Monte Carlo (which assumes GBM)

### **Why Monte Carlo?**
- Enables **statistical hypothesis testing** (need distributions)
- Controlled environment (no confounding factors)
- Can run 50,000 simulations (ABM runs once)
- Provides mean, std, confidence intervals

### **Why Two Optimization Methods?**
- **Grid Search (H1)**: Simple, exhaustive, guaranteed to find local minimum within grid
- **Bayesian Optimization (H2)**: Efficient, adaptive, fewer evaluations

### **Why Multiple Market Maker Types?**
- Compare **4 strategies side-by-side** in same environment
- Each MM has independent P&L tracking
- Fair comparison (same market conditions)

---

## 🔗 Dependencies Between Modules

**Critical Path**:
```
config.py → black_scholes.py → agents.py → model_abm.py → run_full_comparison.py
```

**If you change**:
- `config.py`: Affects all modules
- `black_scholes.py`: Affects agents, optimization
- `agents.py`: Affects ABM only
- `model_abm.py`: Affects execution scripts only
- Optimization modules: Independent, affect only execution scripts

---

## 📝 Summary

**Project has 3 layers**:
1. **Core Layer**: BS formulas, agents, market, models
2. **Optimization Layer**: Grid search, Bayesian optimization
3. **Execution Layer**: Scripts that tie everything together

**4 Execution Modes**:
1. `main.py` - Basic (BS vs Leland)
2. `test_optimized_leland.py` - H1 test
3. `test_ml_leland.py` - H2 test
4. `run_full_comparison.py` - Complete (⭐ recommended)

**Next Steps**: H3 (Sensitivity Analysis) - Test robustness to parameter changes

---

**Last Updated**: 2025-12-11
**Version**: 1.0
**Status**: Complete
