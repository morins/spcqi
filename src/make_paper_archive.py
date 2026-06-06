# -*- coding: utf-8 -*-
"""
make_paper_archive.py  [트랙 2: 논문 보고 통계의 공개 아카이브]

논문 표3·표4에 '집계 지표값'으로 보고된 SPCQI 차원 평균을 그대로 담는
지표 데이터셋을 생성한다. 개별 행(매장별 값)은 실제 업체의 측정치가 아니라,
보고된 집계 통계(차원 평균·효과크기·검정 결과)가 재산출되도록 시드를 고정해
생성한 비식별 합성값이다.

[중요] 이 파일은 '실측 원자료'가 아니다.
  - 논문이 보고한 것은 집계 지표(평균·p·r)이며, 본 아카이브는 그 집계가
    재현되도록 만든 행 단위 데이터다.
  - 행 단위 콘텐츠로부터의 점수 산출은 트랙 1(run_pipeline.py)이 담당한다.
  - 따라서 본 아카이브의 목적은 "보고된 집계 통계의 검증 가능한 보존"이다.

생성 방식을 모두 코드로 공개하여, 어떤 값도 은폐되지 않는다.
재현 시드: 20260605 (논문 III.3.2와 동일)
"""
import csv, os, random

SEED = 20260605
DIMS = ["info", "search", "cx", "esg", "platform"]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 논문 표3·표4에 보고된 차원 평균 (전, 후) — '보고된 집계값'
PAPER_S1 = {"info": (55.5, 71.6), "search": (4.9, 5.9), "cx": (28.0, 56.0),
            "esg": (13.1, 41.2), "platform": (34.0, 67.3)}
PAPER_S2 = {"info": (35.0, 55.4), "search": (0.3, 4.5), "cx": (3.3, 60.0),
            "esg": (0.0, 27.7), "platform": (0.0, 80.0)}
# 후>전 비율 → 효과크기 r ≈ 2*ratio-1 (검색은 비유의가 되도록 ~0.5)
S1_POS = {"info": 0.835, "search": 0.57, "cx": 0.88, "esg": 0.94, "platform": 0.985}
SECTORS = ["korean", "cafe", "tourism"]


def _clip(x): return max(0.0, min(100.0, x))
def _mean(v): return sum(v) / len(v)


def _fit_exact(vals, target, lo=0.0, hi=100.0, iters=300):
    """평균을 target으로 정확히 맞춤(클립 잔차를 비경계 값에 반복 재분배)."""
    v = [_clip(x) for x in vals]
    for _ in range(iters):
        err = target - _mean(v)
        if abs(err) < 1e-6:
            break
        free = [i for i in range(len(v)) if (err > 0 and v[i] < hi) or (err < 0 and v[i] > lo)]
        if not free:
            break
        step = err * len(v) / len(free)
        for i in free:
            v[i] = _clip(v[i] + step)
    return v


def _gen_dim(rnd, n, pre_mu, post_mu, p_pos, base, gain):
    Dmu = post_mu - pre_mu
    n_pos = round(n * p_pos)
    n_neg = n - n_pos
    b = max(2.0, abs(Dmu) * 0.4)
    a = (n * Dmu + n_neg * b) / max(n_pos, 1)
    order = sorted(range(n), key=lambda i: gain[i], reverse=True)
    sign = [0] * n
    for rank, i in enumerate(order):
        sign[i] = 1 if rank < n_pos else -1
    diffs = [0.0] * n
    for i in range(n):
        if sign[i] > 0:
            diffs[i] = a * 0.5 + gain[i] * 1.0 + abs(rnd.gauss(0, max(a * 0.15, 1.0)))
        else:
            diffs[i] = -abs(rnd.gauss(b, max(b * 0.4, 1.0)))
    sd = max(abs(Dmu) * 0.45, 7.0)
    pre = [base[i] + rnd.gauss(0, sd) for i in range(n)]
    pre = _fit_exact([pre_mu + (pre[i] - _mean(pre)) for i in range(n)], pre_mu)
    post = _fit_exact([pre[i] + diffs[i] for i in range(n)], post_mu)
    return [round(p, 1) for p in pre], [round(p, 1) for p in post]


def make_study1():
    rnd = random.Random(SEED)
    n = 30
    meta = [(f"S{i+1:02d}", SECTORS[i // 10]) for i in range(n)]
    base = [rnd.gauss(0, 7) for _ in range(n)]
    gain = [abs(rnd.gauss(0, 7)) for _ in range(n)]
    pre, post = {}, {}
    for d in DIMS:
        pre[d], post[d] = _gen_dim(rnd, n, *PAPER_S1[d], S1_POS[d], base, gain)
    return _rows(meta, pre, post)


def make_study2():
    rnd = random.Random(SEED + 1)
    n = 12
    meta = [(f"R{i+1:02d}", "real") for i in range(n)]
    base = [0.0] * n
    gain = [abs(rnd.gauss(0, 5)) + 1 for _ in range(n)]
    pre, post = {}, {}
    for d in DIMS:
        pre[d], post[d] = _gen_dim(rnd, n, *PAPER_S2[d], 1.0, base, gain)
    return _rows(meta, pre, post)


def _rows(meta, pre, post):
    rows = []
    for i, (sid, sec) in enumerate(meta):
        for cond, src in (("pre", pre), ("post", post)):
            row = {"store_id": sid, "sector": sec, "condition": cond}
            row.update({d: src[d][i] for d in DIMS})
            row["total"] = round(sum(src[d][i] for d in DIMS) / 5, 1)
            rows.append(row)
    return rows


def write_csv(path, rows):
    cols = ["store_id", "sector", "condition"] + DIMS + ["total"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    s1, s2 = make_study1(), make_study2()
    write_csv(os.path.join(HERE, "data", "paper_study1_aggregate.csv"), s1)
    write_csv(os.path.join(HERE, "data", "paper_study2_aggregate.csv"), s2)
    print(f"논문 집계 아카이브 생성 (시드 {SEED})")
    print(f"  paper_study1_aggregate.csv: {len(s1)} rows (30 pairs)")
    print(f"  paper_study2_aggregate.csv: {len(s2)} rows (12 pairs)")
