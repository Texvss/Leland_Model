"""
Black-Scholes Utilities
=======================
Greeks calculation and Leland's modified volatility
"""

import numpy as np
from scipy.stats import norm


class BlackScholesUtils:
    """Black-Scholes pricing and Greeks"""

    @staticmethod
    def d1(S, K, T, r, sigma):
        """Helper function d1"""
        if T <= 1e-10:
            return 0.0
        return (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))

    @staticmethod
    def d2(S, K, T, r, sigma):
        """Helper function d2"""
        if T <= 1e-10:
            return 0.0
        return BlackScholesUtils.d1(S, K, T, r, sigma) - sigma*np.sqrt(T)

    @staticmethod
    def call_price(S, K, T, r, sigma):
        """European call option price"""
        if T <= 1e-10:
            return float(max(S - K, 0))

        d1 = BlackScholesUtils.d1(S, K, T, r, sigma)
        d2 = BlackScholesUtils.d2(S, K, T, r, sigma)

        price = S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)

        # Ensure scalar return (not numpy array)
        if isinstance(price, np.ndarray):
            return float(price.item())
        return float(price)

    @staticmethod
    def delta(S, K, T, r, sigma):
        """Delta (∂V/∂S)"""
        if T <= 1e-10:
            return 1.0 if S > K else 0.0

        d1 = BlackScholesUtils.d1(S, K, T, r, sigma)
        delta_val = norm.cdf(d1)

        # Ensure scalar return
        if isinstance(delta_val, np.ndarray):
            return float(delta_val.item())
        return float(delta_val)

    @staticmethod
    def gamma(S, K, T, r, sigma):
        """Gamma (∂²V/∂S²)"""
        if T <= 1e-10:
            return 0.0

        d1 = BlackScholesUtils.d1(S, K, T, r, sigma)
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))

    @staticmethod
    def vega(S, K, T, r, sigma):
        """Vega (∂V/∂σ)"""
        if T <= 1e-10:
            return 0.0

        d1 = BlackScholesUtils.d1(S, K, T, r, sigma)
        return S * norm.pdf(d1) * np.sqrt(T)

    @staticmethod
    def theta(S, K, T, r, sigma):
        """Theta (∂V/∂t)"""
        if T <= 1e-10:
            return 0.0

        d1 = BlackScholesUtils.d1(S, K, T, r, sigma)
        d2 = BlackScholesUtils.d2(S, K, T, r, sigma)

        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        term2 = r * K * np.exp(-r*T) * norm.cdf(d2)

        return term1 - term2

    @staticmethod
    def leland_volatility(sigma, k, dt, short_gamma=True):
        """
        Leland's modified volatility

        From Zakamouline (2005):
        σ_m = σ * sqrt(1 ± A)
        where A = (k/σ) * sqrt(8/(π*dt))
        """
        A = (k / sigma) * np.sqrt(8 / (np.pi * dt))

        if short_gamma:
            sigma_m = sigma * np.sqrt(1 + A)
        else:
            sigma_m = sigma * np.sqrt(max(1 - A, 0.01))

        return sigma_m


# Quick test
if __name__ == "__main__":
    bs = BlackScholesUtils()

    S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.25

    print("Black-Scholes Test:")
    print(f"  Call Price: ${bs.call_price(S, K, T, r, sigma):.4f}")
    print(f"  Delta:      {bs.delta(S, K, T, r, sigma):.4f}")
    print(f"  Gamma:      {bs.gamma(S, K, T, r, sigma):.6f}")

    sigma_leland = bs.leland_volatility(sigma, 0.01, 1/252)
    print(f"\n  Original σ: {sigma:.4f}")
    print(f"  Leland σ:   {sigma_leland:.4f}")
