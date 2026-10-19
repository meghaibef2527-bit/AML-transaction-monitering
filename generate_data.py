"""Generates SYNTHETIC customers and 100,000+ transactions with injected suspicious patterns. No real data."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
N_CUST, N_TXN = 2000, 100_000
COUNTRIES = ["IN", "GB", "US", "AE", "SG", "DE", "HK", "CH", "KP", "IR", "MM"]
HIGH_RISK = {"KP", "IR", "MM"}  # configurable assumption, see src/rules.py

cust = pd.DataFrame({
    "customer_id": [f"C{i:05d}" for i in range(N_CUST)],
    "entity_type": rng.choice(["individual", "business"], N_CUST, p=[0.7, 0.3]),
    "country": rng.choice(COUNTRIES, N_CUST, p=[0.5, 0.12, 0.1, 0.08, 0.06, 0.04, 0.03, 0.03, 0.01, 0.015, 0.015]),
    "pep": rng.random(N_CUST) < 0.02,
    "id_doc_missing": rng.random(N_CUST) < 0.06,
    "address_proof_missing": rng.random(N_CUST) < 0.08,
    "beneficial_owner_missing": False,
})
cust.loc[cust.entity_type == "business", "beneficial_owner_missing"] = rng.random((cust.entity_type == "business").sum()) < 0.15
cust.to_csv("data/customers.csv", index=False)

ts = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 180 * 24 * 3600, N_TXN), unit="s")
txn = pd.DataFrame({
    "txn_id": [f"T{i:07d}" for i in range(N_TXN)],
    "customer_id": rng.choice(cust.customer_id, N_TXN),
    "timestamp": ts,
    "amount": np.round(rng.lognormal(7.0, 1.0, N_TXN), 2),
    "direction": rng.choice(["in", "out"], N_TXN),
    "counterparty_country": rng.choice(COUNTRIES[:8], N_TXN, p=[0.35, 0.2, 0.15, 0.1, 0.08, 0.05, 0.04, 0.03]),
})
txn["suspicious_injected"] = False

# Injected pattern 1: structuring - repeated deposits just under 10,000 within a week
for cid in rng.choice(cust.customer_id, 25, replace=False):
    base = pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(rng.integers(0, 170)))
    k = int(rng.integers(4, 8))
    idx = txn.sample(k, random_state=int(rng.integers(0, 10**6))).index
    txn.loc[idx, ["customer_id", "direction", "suspicious_injected"]] = [cid, "in", True]
    txn.loc[idx, "amount"] = np.round(rng.uniform(9000, 9990, k), 2)
    txn.loc[idx, "timestamp"] = base + pd.to_timedelta(rng.integers(0, 6 * 24 * 3600, k), unit="s")

# Injected pattern 2: rapid in-out movement to high-risk jurisdictions
for cid in rng.choice(cust.customer_id, 20, replace=False):
    base = pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(rng.integers(0, 170)))
    idx = txn.sample(6, random_state=int(rng.integers(0, 10**6))).index
    txn.loc[idx, ["customer_id", "suspicious_injected"]] = [cid, True]
    txn.loc[idx, "amount"] = np.round(rng.uniform(25_000, 80_000, 6), 2)
    txn.loc[idx, "direction"] = ["in", "out", "in", "out", "in", "out"]
    txn.loc[idx, "counterparty_country"] = rng.choice(sorted(HIGH_RISK), 6)
    txn.loc[idx, "timestamp"] = base + pd.to_timedelta(np.sort(rng.integers(0, 20 * 3600, 6)), unit="s")

txn.to_csv("data/transactions.csv", index=False)
print(len(cust), "customers,", len(txn), "transactions,", int(txn.suspicious_injected.sum()), "injected")
