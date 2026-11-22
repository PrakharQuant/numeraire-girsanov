#!/usr/bin/env python3
"""
verify.py — single source of truth for every number on the site.

Recomputes all worked examples (chapters 0-8), Black-Scholes values, CRR
binomial convergence, practice questions, and widget defaults; writes docs/js/data.json that the
interactive widgets read. Exits non-zero if any hardcoded value baked into
the HTML (checked against EXPECTED below) mismatches.

Run:  python3 scripts/verify.py
"""
import json
import math
import os
import re
import sys

import numpy as np
from scipy.stats import norm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "docs", "js", "data.json")
INDEX_PATH = os.path.join(ROOT, "docs", "index.html")


# ---------- core functions ----------
def risk_neutral_q(S0, up, down, r=0.0, T=1.0):
    """q = (S0*e^{rT} - S_down) / (S_up - S_down)."""
    return (S0 * math.exp(r * T) - down) / (up - down)


def bs_price(S, K, r, sigma, T):
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    call = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    return {"d1": d1, "d2": d2, "Nd1": norm.cdf(d1), "Nd2": norm.cdf(d2), "call": call}


def crr_call(S0, sigma, r, T, n, K=100.0):
    """n-step CRR binomial price of a European call (u=e^{sigma*sqrt(dt)})."""
    dt = T / n
    u = math.exp(sigma * math.sqrt(dt)); d = 1.0 / u
    p = (math.exp(r * dt) - d) / (u - d)
    from scipy.stats import binom
    steps = np.arange(n + 1)
    ST = S0 * u ** steps * d ** (n - steps)
    payoff = np.maximum(ST - K, 0.0)
    return float(math.exp(-r * T) * np.dot(binom.pmf(steps, n, p), payoff))


def main():
    data = {}

    # ---- Ch.0 laptop / numeraire ----
    laptop = {"inr": 60000, "usd": 720, "fx": 60000 / 720}
    assert abs(laptop["fx"] - 83.3333333) < 1e-4
    data["ch0"] = laptop

    # ---- Ch.1 risk-neutral probabilities ----
    qA = risk_neutral_q(100, 150, 50, r=0.0)          # 0.5
    qB = risk_neutral_q(100, 130, 80, r=0.0)          # 0.4
    qA_r = risk_neutral_q(100, 150, 50, r=0.05)       # with r != 0
    ch1 = {
        "stockA": {"S0": 100, "up": 150, "down": 50, "q": qA,
                   "avg": qA * 150 + (1 - qA) * 50},
        "stockB": {"S0": 100, "up": 130, "down": 80, "q": qB,
                   "avg": qB * 130 + (1 - qB) * 80},
        "q_with_r_5pct": qA_r,
    }
    assert abs(ch1["stockA"]["q"] - 0.5) < 1e-12
    assert abs(ch1["stockB"]["q"] - 0.4) < 1e-12
    data["ch1"] = ch1

    # ---- Ch.2 CRR convergence to Black-Scholes ----
    conv = []
    for n in [2, 4, 8, 16, 32, 64, 128]:
        conv.append({"n": n, "price": crr_call(100, 0.2, 0.0, 1.0, n)})
    bs_ref = bs_price(100, 100, 0.0, 0.2, 1.0)
    data["ch2"] = {"convergence": conv, "bs_limit": bs_ref["call"]}

    # ---- Ch.3 call split (strike 100, stock A) ----
    data["ch3"] = {"pay_up": 100, "pay_down": 0, "avg_pay": 0.5 * 100 + 0.5 * 0,
                   "call_value": 0.5 * 50 + 0.5 * 0}   # E[max(S-K,0)] = 25

    # ---- Ch.4 change of numeraire, discrete ----
    p_up_stock = 0.5 * 150 / 100   # 0.75
    p_dn_stock = 0.5 * 50 / 100    # 0.25
    three = {"bank": [0.25, 0.50, 0.25], "prices": [50, 100, 150]}
    raw = [0.25 * 50, 0.50 * 100, 0.25 * 150]           # 12.5 / 50 / 37.5
    tot = sum(raw)                                       # 100
    three["stock"] = [x / tot for x in raw]              # 0.125 / 0.5 / 0.375
    three["avg_in_stock"] = sum(w * p for w, p in zip(three["stock"], three["prices"]))  # 112.5
    qB_to_stock = 0.4 * 130 / 100                        # 0.52
    data["ch4"] = {"two_state": {"bank": [0.5, 0.5], "stock": [p_up_stock, p_dn_stock]},
                   "three_state": three,
                   "stockB": {"bank": qB, "stock": qB_to_stock}}
    assert abs(qB_to_stock - 0.52) < 1e-12
    assert abs(three["avg_in_stock"] - 112.5) < 1e-9
    assert three["stock"] == [0.125, 0.5, 0.375]

    # ---- Ch.5 price invariance (stock B call, K=100) ----
    payoff_up, payoff_dn = 30.0, 0.0
    bank_way = qB * payoff_up + (1 - qB) * payoff_dn            # 12
    stock_way = (payoff_up / 130) * qB_to_stock * 100 + (payoff_dn / 80) * (1 - qB_to_stock) * 100
    data["ch5"] = {"bank_numeraire": bank_way, "stock_numeraire": stock_way}
    assert abs(bank_way - 12.0) < 1e-12 and abs(stock_way - 12.0) < 1e-12

    # ---- Ch.6 continuous time numbers ----
    flat = bs_price(100, 100, 0.0, 0.2, 1.0)
    itm = bs_price(120, 100, 0.0, 0.2, 1.0)
    data["ch6"] = {"flat_atm": flat, "itm": itm,
                   "shift": flat["d1"] - flat["d2"], "sigma_sqrtT": 0.2}
    assert abs(flat["d2"] + 0.1) < 1e-9 and abs(flat["d1"] - 0.1) < 1e-9
    assert abs(flat["Nd2"] - 0.4602) < 5e-4 and abs(flat["Nd1"] - 0.5398) < 5e-4
    assert abs(flat["call"] - 7.965) < 5e-3

    # ---- Ch.7 Girsanov preview (discrete stage) ----
    data["ch7"] = {"reweighted_avg": 0.75 * 150 + 0.25 * 50,   # 125
                   "drift_shift_note": "continuous: drift r -> r + sigma^2 under stock measure"}
    assert abs(data["ch7"]["reweighted_avg"] - 125.0) < 1e-12

    # ---- Ch.8 forward measure one-step example ----
    B0 = 0.5 * 100 / 1.04 + 0.5 * 100 / 1.06
    factors = [100 / 1.04, 100 / 1.06]
    raw = [0.5 * f for f in factors]
    tot = sum(raw)
    p_fwd = [x / tot for x in raw]
    fwd_rate = 100 / B0 - 1
    avg_under_fwd = sum(p * r for p, r in zip(p_fwd, [0.04, 0.06]))
    data["ch8"] = {
        "B0": round(B0, 4),
        "rates": [0.04, 0.06],
        "bank_probs": [0.5, 0.5],
        "fwd_probs": [round(p, 4) for p in p_fwd],
        "fwd_rate": round(fwd_rate, 6),
        "avg_rate_under_fwd": round(avg_under_fwd, 6)
    }
    assert abs(avg_under_fwd - fwd_rate) < 1e-9

    # ---- Practice set (10 questions, numbers from here) ----
    prac = []
    prac.append({"id": 1, "text": "Stock 100 → 120 or 70, r=0. Find risk-neutral q.", "answer": round(risk_neutral_q(100, 120, 70), 4)})
    prac.append({"id": 2, "text": "Stock 100 → 150/50, bank q=0.5. Stock-numeraire up-prob?", "answer": 0.75})
    prac.append({"id": 3, "text": "Call payoff 30/0 on Stock B (q=0.4). Bank-numeraire price?", "answer": 12.0})
    prac.append({"id": 4, "text": "Same call under stock numeraire (must match).", "answer": 12.0})
    prac.append({"id": 5, "text": "ATM call S=K=100, r=0, σ=0.2, T=1. Black-Scholes price.", "answer": round(bs_price(100,100,0,0.2,1)["call"], 4)})
    prac.append({"id": 6, "text": "N(d2) for that ATM call.", "answer": round(bs_price(100,100,0,0.2,1)["Nd2"], 4)})
    prac.append({"id": 7, "text": "Three-state reweight avg under stock measure.", "answer": 112.5})
    prac.append({"id": 8, "text": "Forward rate from Ch.8 bond (100/B0 - 1).", "answer": round(fwd_rate, 6)})
    prac.append({"id": 9, "text": "Stock B reweight to stock: up prob.", "answer": 0.52})
    prac.append({"id": 10, "text": "Laptop FX rate 60000/720.", "answer": round(60000/720, 2)})
    data["practice"] = prac

    # ---- Widget defaults ----
    data["widgets"] = {
        "reweight": {"S0": 100, "up": 150, "down": 50, "q_bank": 0.5, "K": 100},
        "bell": {"S": 100, "K": 100, "r": 0.0, "sigma": 0.2, "T": 1.0},
    }

    # ---- write JSON ----
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {DATA_PATH}")

    # ---- cross-check numbers printed in index.html ----
    expected_strings = [
        "83.33",      # ch0 fx
        "q = 0.5", "0.4",        # ch1
        "112.5", "0.52",         # ch4
        "12",                    # ch5 (both ways)
        "-0.1", "0.1", "0.46", "0.54", "7.96",  # ch6
        "125",                   # ch7
        "95.25", "0.0499",       # ch8 approx
        "0.6",                   # practice q
    ]
    problems = []
    if os.path.exists(INDEX_PATH):
        html = open(INDEX_PATH).read()
        for s in expected_strings:
            if s not in html:
                problems.append(f"expected string '{s}' missing from index.html")
        # KaTeX-rendered formulas: check key tokens exist
        for tok in ["S_{down}", "N(d_1)", "\\sigma\\sqrt{T}"]:
            if tok not in html:
                problems.append(f"formula token '{tok}' missing")
    else:
        problems.append("index.html not built yet")

    print(json.dumps({k: v for k, v in data.items() if k in ("ch1", "ch5", "ch6")}, indent=2)[:800])
    if problems:
        print("\nMISMATCHES:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("\nAll checks passed ✔")


if __name__ == "__main__":
    main()
