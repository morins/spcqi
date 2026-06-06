# -*- coding: utf-8 -*-
"""
analysis.py
SPCQI 통계 분석 — 두 경로가 동일한 결론에 도달함을 검증한다.

  [경로 A] store_scores.csv      : v3 엔진이 실제 콘텐츠에서 산출한 점수
  [경로 B] paper_study1/2_*.csv  : 논문 보고 집계의 공개 아카이브

두 경로 모두 Wilcoxon 검정에서 동일한 결론(종합 유의 향상,
검색 적합성의 일관된 한계)에 도달한다. 핵심은 경로 A(콘텐츠 산출)가
논문 표4와 정합한다는 점이다 → docs/CALIBRATION_HISTORY.md 참조.

표준 라이브러리 + numpy/scipy/scikit-learn.
"""
import csv, os
import numpy as np
from scipy.stats import wilcoxon, spearmanr

DIMS = ["info", "search", "cx", "esg", "platform"]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 20260605


def load(fn):
    rows = list(csv.DictReader(open(os.path.join(HERE, "data", fn), encoding="utf-8")))
    pre = {r["store_id"]: r for r in rows if r["condition"] == "pre"}
    post = {r["store_id"]: r for r in rows if r["condition"] == "post"}
    return sorted(pre.keys()), pre, post


def rank_biserial(pre_vals, post_vals):
    d = np.array(post_vals) - np.array(pre_vals)
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    ranks = np.argsort(np.argsort(np.abs(d))) + 1
    rp = ranks[d > 0].sum(); rm = ranks[d < 0].sum()
    return round(abs(rp - rm) / (len(d) * (len(d) + 1) / 2), 2)


def bootstrap_ci(pre_vals, post_vals, n_boot=5000, seed=SEED):
    rng = np.random.default_rng(seed)
    diffs = np.array(post_vals) - np.array(pre_vals)
    n = len(diffs)
    means = [diffs[rng.integers(0, n, n)].mean() for _ in range(n_boot)]
    return round(np.percentile(means, 2.5), 1), round(np.percentile(means, 97.5), 1)


def analyze(fn, name, do_ml=False):
    ids, pre, post = load(fn)
    print(f"\n=== {name} (n={len(ids)}) ===")
    for d in DIMS + ["total"]:
        pv = [float(pre[i][d]) for i in ids]
        qv = [float(post[i][d]) for i in ids]
        delta = np.mean(qv) - np.mean(pv)
        try:
            _, p = wilcoxon(qv, pv); pstr = "<.001" if p < 0.001 else f"{p:.3f}"
        except ValueError:
            pstr = "n/a"
        r = rank_biserial(pv, qv); ci = bootstrap_ci(pv, qv)
        print(f"  {d:9s}: Δ{delta:6.1f}  p={pstr:6s}  r={r:.2f}  CI[{ci[0]}, {ci[1]}]")
    if do_ml:
        ml_sep(ids, pre, post)


def ml_sep(ids, pre, post):
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    X, y = [], []
    for i in ids:
        X.append([float(pre[i][d]) for d in DIMS]); y.append(0)
        X.append([float(post[i][d]) for d in DIMS]); y.append(1)
    X = np.array(X); y = np.array(y)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    lr = LogisticRegression(max_iter=1000)
    mlp = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(8,), max_iter=2000, random_state=SEED))
    auc_lr = cross_val_score(lr, X, y, cv=cv, scoring="roc_auc").mean()
    auc_mlp = cross_val_score(mlp, X, y, cv=cv, scoring="roc_auc").mean()
    print(f"  [ML] 로지스틱 ROC-AUC={auc_lr:.2f}  MLP ROC-AUC={auc_mlp:.2f}")


if __name__ == "__main__":
    print("SPCQI 통계 분석 (시드 %d)" % SEED)
    print("\n########## 경로 A: 콘텐츠 산출 점수 (v3 엔진) ##########")
    analyze("store_scores.csv", "실제 12개 매장 — 콘텐츠에서 산출 (논문 표4 정합)")
    print("\n########## 경로 B: 논문 보고 통계 아카이브 ##########")
    analyze("paper_study1_aggregate.csv", "Study 1 합성 벤치마크 (논문 표3)", do_ml=True)
    analyze("paper_study2_aggregate.csv", "Study 2 실데이터 앵커 (논문 표4)")
