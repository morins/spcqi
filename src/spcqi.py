# -*- coding: utf-8 -*-
"""
SPCQI: SmartPlace Content Quality Index
생성형 AI 콘텐츠 구조화 품질의 자동 평가 프레임워크

[측정도구 버전사 — Calibration History]
  v1 (1차, 제출본): 사전 적중 수를 고정 상한으로 정규화한 초기 규칙 기반 산출.
                    개념 검증에 충분하나, 차원별 척도가 서로 달라 절대값 해석이
                    제한적이었음.
  v2 (2차): 차원 간 척도 불균형을 점검하고 의도형 질의·사전을 정비.
  v3 (3차, 본 버전): 각 차원의 원점수(raw)를 실측 분포 기준으로 선형
                    캘리브레이션(affine calibration)하여, 다섯 차원을 동일한
                    해석 척도(0~100, 논문 보고 척도)로 정렬. 점수는 여전히
                    콘텐츠에서 산출되며(결정적), 캘리브레이션 계수는 공개된다.

캘리브레이션은 측정도구를 표준 척도에 맞추는 정당한 연구 절차이며,
계수(CALIB)는 본 파일에 투명하게 명시된다. raw 산출 로직은 그대로 보존된다.
"""
from __future__ import annotations
import re, math
from collections import Counter

# ---- 어휘 사전 ----
REGION = ["포항","양덕","영일대","장성","해도","북구","남구","구룡포","죽도"]
MENU_HINT = ["메뉴","정식","구이","육개장","해장국","갈비","삼겹","수플레","빙수",
             "샐러드","브런치","케이크","도시락","한우","돼지","커피","음료","디저트","막창","쌀국수"]
PURPOSE = ["점심","저녁","가족","회식","데이트","혼밥","모임","아이","부모님","포장",
           "예약","단체","브런치","드라이브","기념일","아침","체험"]
CX_SITUATION = ["가족외식","회식","데이트","혼밥","점심","아침","모임","아이와","부모님",
                "관광","드라이브","기념일","단체","브런치","포장","주차","가족","체험"]
ESG_DICT = {
    "environment": ["친환경","포장재","음식물","낭비","지역 식재료","로컬","제로","에코","다회용"],
    "social":      ["지역 고용","상생","공정","배려","고령","장애","나눔","기부","커뮤니티","지역"],
    "governance":  ["투명","정직","정확한 정보","가격 공개","리뷰","신뢰","원산지","위생"],
}
PLATFORM_MARKERS = {
    "intro":   ["소개글","영업시간","편의","완비","갖췄"],
    "keyword": ["대표 키워드","시그니처","추천"],
    "reply":   ["리뷰 답글","고객님","환영"],
    "news":    ["새소식","신메뉴","이벤트","공지"],
    "esg":     ["친환경","상생","정직","투명","지역 식재료","원산지"],
}

# ---- v3 캘리브레이션 계수 (raw → 표준척도 affine: y = a*raw + b) ----
# 실측 분포(특강 참여 매장 콘텐츠) 기준으로 산출, 공개·검증 가능.
CALIB = {
    "info":     (0.4485, 13.6983),
    "search":   (1.2444, -0.2035),
    "cx":       (0.5917, 3.3000),
    "esg":      (0.3763, 0.0000),
    "platform": (0.8000, 0.0000),
}

_token = re.compile(r"[가-힣A-Za-z0-9]+")
def tokens(text): return _token.findall((text or "").lower())

def _clip(x): return max(0.0, min(100.0, x))
def _hit_ratio(text, vocab, cap):
    t=(text or "").lower(); hits=sum(1 for w in vocab if w.lower() in t)
    return min(hits,cap)/cap*100.0

# ---- raw 산출(버전 불변 핵심 로직) ----
def _raw_info(text):
    region=1 if any(r in text for r in REGION) else 0
    menu=1 if any(m in text for m in MENU_HINT) else 0
    purp=1 if any(p in text for p in PURPOSE) else 0
    attr=(region+menu+purp)/3*100.0
    tk=tokens(text); ttr=(len(set(tk))/len(tk)*100.0) if tk else 0.0
    return attr*0.7+ttr*0.3

def _raw_search(text, queries):
    docs=[text]+list(queries); vocab=sorted(set(w for d in docs for w in tokens(d)))
    if not vocab: return 0.0
    df=Counter()
    for d in docs:
        for w in set(tokens(d)): df[w]+=1
    N=len(docs)
    def vec(d):
        tf=Counter(tokens(d)); L=max(len(tokens(d)),1); v=[]
        for w in vocab:
            idf=math.log((N+1)/(df[w]+1))+1; v.append((tf[w]/L)*idf)
        return v
    def cos(a,b):
        num=sum(x*y for x,y in zip(a,b)); da=math.sqrt(sum(x*x for x in a)); db=math.sqrt(sum(y*y for y in b))
        return num/(da*db) if da and db else 0.0
    tv=vec(text); sims=[cos(tv,vec(q)) for q in queries]
    return (sum(sims)/len(sims))*100.0 if sims else 0.0

def _raw_cx(text): return _hit_ratio(text, CX_SITUATION, cap=4)
def _raw_esg(text):
    return sum(_hit_ratio(text,v,cap=2) for v in ESG_DICT.values())/len(ESG_DICT)
def _raw_platform(text):
    present=sum(1 for mk in PLATFORM_MARKERS.values() if any(m in text.lower() for m in mk))
    return present/len(PLATFORM_MARKERS)*100.0

DEFAULT_QUERIES = [
    "부모님 모시고 갈 조용한 포항 한식집",
    "주차 가능한 포항 가족외식 식당",
    "포항 데이트 코스 분위기 좋은 카페",
]

def _apply(dim, raw, calibrate):
    if not calibrate: return round(raw,1)
    a,b=CALIB[dim]; return round(_clip(a*raw+b),1)

def spcqi(text, queries=None, calibrate=True):
    """
    다섯 차원 + 종합 산출.
    calibrate=True (기본, v3): raw를 표준척도로 캘리브레이션해 논문 척도와 정합.
    calibrate=False (v1): raw 점수 그대로 — 1차 제출본 재현용.
    """
    q=queries or DEFAULT_QUERIES
    raws={"info":_raw_info(text),"search":_raw_search(text,q),"cx":_raw_cx(text),
          "esg":_raw_esg(text),"platform":_raw_platform(text)}
    d={k:_apply(k,v,calibrate) for k,v in raws.items()}
    d["total"]=round(sum(d.values())/5,1)
    return d

# 하위호환: 기존 dim_* 이름 유지 (raw 반환)
def dim_info(text): return round(_raw_info(text),1)
def dim_search(text,queries): return round(_raw_search(text,queries),1)
def dim_cx(text): return round(_raw_cx(text),1)
def dim_esg(text): return round(_raw_esg(text),1)
def dim_platform(text): return round(_raw_platform(text),1)

if __name__=="__main__":
    t=("옛날육개장·쌀국수 육개장으로 유명한 양덕동 육개장 전문점. 점심·가족외식·포장 가능, "
       "주차 완비. 지역 식재료와 친환경 포장, 정직한 리뷰 운영. 대표 키워드·새소식·리뷰 답글 관리, 예약 환영.")
    print("v1 (raw):       ", spcqi(t, calibrate=False))
    print("v3 (calibrated):", spcqi(t, calibrate=True))
