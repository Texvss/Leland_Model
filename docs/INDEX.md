# Leland ABM Project - Documentation Index

This directory contains all supplementary documentation for the Leland ABM project.

## 📚 Documentation Files

### **Main Project Documentation**
- **[../README.md](../README.md)** - Main project README (in root directory)
  - Complete project overview
  - All four hedging strategies
  - Hypothesis testing results
  - Quick start guide

### **Analysis Tools Documentation**
- **[README_ANALYSIS.md](README_ANALYSIS.md)** - Enhanced Analysis Tools Guide
  - Multi-run ABM analysis (statistical significance)
  - Adaptive sensitivity analysis (real volatility)
  - Complete analysis runner
  - Usage examples and scenarios

### **Hypothesis-Specific Documentation**

#### H1: Optimized Leland
- **[OPTIMIZED_LELAND_README.md](OPTIMIZED_LELAND_README.md)** - Optimized Leland Strategy
  - Grid search calibration methodology
  - Implementation details
  - **Actual Results**: ❌ H1 Not Confirmed
  - Why Classical Leland remains optimal

#### H2: ML-Calibrated Leland
- **[ML_CALIBRATED_README.md](ML_CALIBRATED_README.md)** - ML-Calibrated Strategy
  - Bayesian optimization with Gaussian Process
  - Implementation details
  - **Actual Results**: ❌ H2 Not Confirmed
  - Value of negative results

### **Project Structure & Quick Start**
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Detailed Architecture
  - File organization
  - Module descriptions
  - Code structure

- **[RUN_PROJECT.md](RUN_PROJECT.md)** - Quick Start Guide
  - Installation instructions
  - Running different analyses
  - Troubleshooting

---

## 🎯 Quick Navigation by Topic

### **Getting Started**
1. Start with [../README.md](../README.md) - Project overview
2. Read [RUN_PROJECT.md](RUN_PROJECT.md) - Installation & quick start
3. Check [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Understand code organization

### **Running Analysis**
1. **Basic test**: See [../README.md](../README.md) Quick Start section
2. **Advanced analysis**: Read [README_ANALYSIS.md](README_ANALYSIS.md)
3. **Multi-run ABM**: `python run_multi_abm.py TSLA 100`
4. **Complete analysis**: `python run_complete_analysis.py TSLA AAPL`

### **Understanding Results**
1. **Main findings**: See [../README.md](../README.md) - "Actual Results" section
2. **H1 results**: [OPTIMIZED_LELAND_README.md](OPTIMIZED_LELAND_README.md) - Actual Results section
3. **H2 results**: [ML_CALIBRATED_README.md](ML_CALIBRATED_README.md) - Actual Results section
4. **Statistical details**: Check CSV files in project root

### **Technical Details**
- **Calibration methods**: [OPTIMIZED_LELAND_README.md](OPTIMIZED_LELAND_README.md) & [ML_CALIBRATED_README.md](ML_CALIBRATED_README.md)
- **Multi-run statistics**: [README_ANALYSIS.md](README_ANALYSIS.md)
- **Code architecture**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

## 📊 Key Results Summary

### **Hypothesis Testing Results**
- **H1 (Optimized Leland)**: ❌ Not Confirmed - Classical Leland optimal
- **H2 (ML-Calibrated)**: ❌ Not Confirmed - Classical Leland optimal
- **H3 (Robustness)**: ✅ Confirmed - All strategies robust to parameter changes

### **Best Strategy**
**Classical Leland** - Use Leland's (1985) analytical formula:
- Mathematically optimal
- Empirically validated (TSLA, AAPL)
- No calibration needed
- Simple and fast

### **Performance**
```
Classical Leland (BEST)
    ↑  $15-46 better (TSLA) / $0.30-0.40 (AAPL)
Optimized / ML-Calibrated (both worse)
    ↑  $32-46 better (TSLA) / $3-4 (AAPL)
Black-Scholes (worst)
```

---

## 🔄 Document Status

| Document | Created | Updated | Status |
|----------|---------|---------|--------|
| README.md | 2025-12-10 | 2025-12-14 | ✅ Current |
| README_ANALYSIS.md | 2025-12-14 | 2025-12-14 | ✅ Current |
| OPTIMIZED_LELAND_README.md | 2025-12-10 | 2025-12-14 | ✅ Updated with results |
| ML_CALIBRATED_README.md | 2025-12-11 | 2025-12-14 | ✅ Updated with results |
| PROJECT_STRUCTURE.md | 2025-12-11 | 2025-12-11 | ✅ Current |
| RUN_PROJECT.md | 2025-12-11 | 2025-12-11 | ✅ Current |

---

**Last Updated**: 2025-12-14
**Project Status**: All hypotheses tested, analysis complete
**Next Step**: Report writing and presentation
