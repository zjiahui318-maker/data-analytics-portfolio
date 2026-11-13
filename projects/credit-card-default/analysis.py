"""Compare two review queues at the same fixed credit-risk review capacity."""

from hashlib import sha256
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path(__file__).resolve().parent / "data/uci-credit-card-default.csv"
SOURCE = "https://doi.org/10.24432/C55S3H"
MIRROR = "https://huggingface.co/datasets/scikit-learn/credit-card-clients/blob/f809522/UCI_Credit_Card.csv"
DIGEST = "a0f0ab49d6326671d6cd83be5c88dcf18007025fe9a53ecd699119c871176ca1"
TARGET = "default.payment.next.month"
STATUSES = ["PAY_0", *(f"PAY_{i}" for i in range(2, 7))]
BILLS = [f"BILL_AMT{i}" for i in range(1, 7)]
PAYMENTS = [f"PAY_AMT{i}" for i in range(1, 7)]
RULE, MODEL = "Delinquency rule", "Logistic regression"
SEED = 42
REVIEW_FRACTION = 0.10


def load_data():
    if sha256(DATA.read_bytes()).hexdigest() != DIGEST:
        raise ValueError("The dataset does not match the recorded source snapshot.")
    raw = pd.read_csv(DATA).sort_values("ID").set_index("ID", verify_integrity=True)
    if (raw.shape != (30000, 24) or raw[TARGET].value_counts().to_dict() != {0: 23364, 1: 6636}
            or raw.isna().any().any() or (raw["LIMIT_BAL"] <= 0).any()
            or (raw[PAYMENTS] < 0).any().any()
            or not raw[STATUSES].isin(range(-2, 10)).all().all()):
        raise ValueError("Unexpected UCI data shape, labels or feature values.")
    return raw


def build_features(raw):
    delays = raw[STATUSES].clip(lower=0)
    older = delays.iloc[:, 1:]
    utilisation = raw[BILLS].div(raw["LIMIT_BAL"], axis=0).clip(-1, 3)
    return pd.DataFrame({
        "Recent status -2": raw["PAY_0"].eq(-2),
        "Recent status -1": raw["PAY_0"].eq(-1),
        "Recent delay 1 month": delays["PAY_0"].eq(1),
        "Recent delay 2 months": delays["PAY_0"].eq(2),
        "Recent delay 3+ months": delays["PAY_0"].ge(3),
        "Older late months": older.gt(0).sum(axis=1),
        "Older maximum delay": older.max(axis=1),
        "Recent bill to limit": utilisation.iloc[:, 0],
        "Mean bill to limit": utilisation.mean(axis=1),
        "Log credit limit": np.log1p(raw["LIMIT_BAL"]),
        "Log mean payment": np.log1p(raw[PAYMENTS].mean(axis=1)),
        "Months with zero payment": raw[PAYMENTS].eq(0).sum(axis=1),
    }, index=raw.index)


def delinquency_score(raw):
    delays = raw[STATUSES].clip(lower=0)
    late_months = delays.gt(0).sum(axis=1)
    # Positional weights preserve priority across the documented value ranges.
    return 70 * delays["PAY_0"] + 10 * late_months + delays.max(axis=1)


def review_order(scores, tie_break):
    return np.lexsort((tie_break, -np.asarray(scores)))


def evaluate_queue(actual, order, size):
    found = int(actual[order[:size]].sum())
    defaults = int(actual.sum())
    return {
        "Reviewed": size,
        "Defaults found": found,
        "Defaults missed": defaults - found,
        "Non-defaults reviewed": size - found,
        "Precision": found / size,
        "Recall": found / defaults,
    }


def run_experiment(raw):
    train, test = train_test_split(raw, test_size=0.20, random_state=SEED,
                                   stratify=raw[TARGET])
    assert not train.index.intersection(test.index).size
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
    model.fit(build_features(train), train[TARGET])
    scores = {
        RULE: delinquency_score(test).to_numpy(),
        MODEL: model.predict_proba(build_features(test))[:, 1],
    }
    actual = test[TARGET].to_numpy()
    ties = np.random.default_rng(SEED).permutation(len(test))
    orders = {name: review_order(values, ties) for name, values in scores.items()}
    size = int(len(test) * REVIEW_FRACTION)
    results = pd.DataFrame.from_dict({
        name: evaluate_queue(actual, order, size) for name, order in orders.items()
    }, orient="index")
    assert (results["Defaults found"] + results["Defaults missed"]).eq(actual.sum()).all()
    assert (results["Defaults found"] + results["Non-defaults reviewed"]).eq(size).all()
    assert all(len(set(order[:size])) == size for order in orders.values())
    return train, test, model, scores, orders, results


def paired_bootstrap(actual, orders, size, draws=1500):
    """Resample held-out accounts and rerank both queues with the original fitted scores."""
    rank_positions = {name: np.argsort(order) for name, order in orders.items()}
    rng = np.random.default_rng(911)
    differences = np.empty(draws)
    for draw in range(draws):
        sample = rng.integers(0, len(actual), size=len(actual))
        rule = sample[np.argpartition(rank_positions[RULE][sample], size - 1)[:size]]
        model = sample[np.argpartition(rank_positions[MODEL][sample], size - 1)[:size]]
        differences[draw] = actual[model].sum() - actual[rule].sum()
    return tuple(np.quantile(differences, [0.025, 0.975]))


def ranking_metrics(train, test, scores):
    actual = test[TARGET]
    return pd.DataFrame({
        name: {
            "ROC AUC": roc_auc_score(actual, values),
            "Average precision": average_precision_score(actual, values),
            "Brier score": brier_score_loss(actual, values) if name == MODEL else np.nan,
        }
        for name, values in scores.items()
    }).T.assign(**{"Constant-probability Brier": [
        np.nan, brier_score_loss(actual, np.repeat(train[TARGET].mean(), len(test)))
    ]})


def queue_breakdown(test, orders, size):
    selected = {name: set(order[:size]) for name, order in orders.items()}
    actual = test[TARGET].to_numpy()
    model, rule = selected[MODEL], selected[RULE]
    rows = {"Both": model & rule, "Logistic only": model - rule, "Rule only": rule - model}
    return pd.DataFrame({
        name: {"Reviewed": len(indices), "Defaults found": int(actual[list(sorted(indices))].sum())}
        for name, indices in rows.items()
    }).T


def subgroup_results(test, orders, size):
    actual = test[TARGET].to_numpy()
    groups = test["SEX"].to_numpy()
    result = []
    for method, order in orders.items():
        reviewed = order[:size]
        for code, label in ((1, "Male (recorded)"), (2, "Female (recorded)")):
            mask = groups == code
            members = reviewed[mask[reviewed]]
            defaults = int(actual[mask].sum())
            found = int(actual[members].sum())
            result.append({
                "Method": method, "Group": label, "Clients": int(mask.sum()),
                "Defaults": defaults, "Reviewed": len(members), "Defaults found": found,
                "Recall": found / defaults, "Precision": found / len(members),
            })
    return pd.DataFrame(result).set_index(["Method", "Group"])


def plot_capacity(actual, orders):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(7.5, 4.2), layout="constrained")
    upper = int(0.30 * len(actual))
    budgets = np.arange(upper + 1) / len(actual)
    for name, colour, style in ((RULE, "#99542d", "--"), (MODEL, "#126e71", "-")):
        capture = np.r_[0, np.cumsum(actual[orders[name]][:upper])] / actual.sum()
        ax.plot(budgets, capture, label=name, color=colour, linestyle=style, linewidth=2)
    ax.plot(budgets, budgets, label="Random review (expected)", color="#677681", linestyle=":")
    ax.axvline(REVIEW_FRACTION, color="#677681", linewidth=0.9, alpha=0.65)
    ax.set(xlabel="Share of held-out clients reviewed", ylabel="Share of held-out defaults found",
           title="Default coverage by review capacity", xlim=(0, 0.30), ylim=(0, 0.70))
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.grid(axis="y", color="#dbe2e3", linewidth=0.7)
    ax.legend(frameon=False, loc="upper left")
    return fig
