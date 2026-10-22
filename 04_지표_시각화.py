# -*- coding: utf-8 -*-
"""
04. 탐지 결과를 생활 지표로 바꾸고, 나라별로 비교하는 그림을 만든다

장면(프레임)마다 아래 다섯 가지가 '보였는지'를 판정하고, 나라별로 그런 장면의 비율(%)을 낸다.
영상 하나가 결과를 끌고 가지 않도록 영상별 비율을 먼저 구하고 그 평균을 나라 값으로 쓴다.

  좌석      의자·벤치·소파·테이블이 하나라도 보임
  착석      사람 박스의 아래쪽 절반이 의자·테이블 박스와 20% 이상 겹침(앉아 있다고 추정)
  무리      사람 2명 이상이 서로 가까이 있음(중심 거리 < 두 사람 평균 박스 너비 × 1.5)
  (테이블 위 음식: 사람 검수에서 음식·음료 박스 12개가 모두 진열 상품·포장 그림 오인이라 지표에서 뺌)
  (공부: 노트북·책은 매대의 잡지·책까지 잡혀 지표에서 뺌)
  오토바이·자전거  오토바이·자전거(입구·유리창 밖 포함)

산출: output/지표_영상별.csv, output/지표_요약.csv, output/그림_*.png, output/검수/*.jpg
"""

import csv
import os
import random
import sys
from collections import defaultdict

import cv2
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

matplotlib.use("Agg")
HERE = os.path.dirname(os.path.abspath(__file__))
DET = os.path.join(HERE, "data", "탐지결과.csv")
FR = os.path.join(HERE, "data", "frames")
OUT = os.path.join(HERE, "output")
os.makedirs(os.path.join(OUT, "검수"), exist_ok=True)

# TDS 느낌: Pretendard(사용자 글꼴 폴더에 설치). 없으면 맑은 고딕으로 대체
_FD = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
FONT = os.path.join(_FD, "Pretendard-Medium.otf")
FONT_B = os.path.join(_FD, "Pretendard-Bold.otf")
if not os.path.exists(FONT):
    FONT, FONT_B = "C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"
font_manager.fontManager.addfont(FONT)
font_manager.fontManager.addfont(FONT_B)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

CC = ["KR", "JP", "VN"]
NAME = {"KR": "한국", "JP": "일본", "VN": "베트남"}
COL = {"KR": "#3182F6", "JP": "#F04452", "VN": "#03B26C"}   # TDS blue500 · red500 · green500
GRAY, INK, SUB, GRID = "#8B95A1", "#191F28", "#4E5968", "#E5E8EB"

SEAT = {"chair", "bench", "couch", "dining table"}
TABLE = {"dining table"}
FOOD = {"cup", "bowl", "bottle", "wine glass", "fork", "spoon", "knife", "sandwich", "hot dog", "pizza",
        "donut", "cake", "banana", "apple", "orange"}
STUDY = {"laptop", "book"}
RIDE = {"motorcycle", "bicycle"}
IND = [("seat", "좌석"), ("sit", "착석"), ("group", "무리"),
       ("ride", "오토바이·자전거")]


def load():
    with open(DET, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    frames = defaultdict(list)
    meta = {}
    for r in rows:
        meta[r["file"]] = (r["country"], r["video"], r["scene"])
        if r["cls"]:
            frames[r["file"]].append((r["cls"], float(r["conf"]),
                                      [float(r[k]) for k in ("x1", "y1", "x2", "y2")]))
    return frames, meta


def inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0, w) * max(0, h)


def judge(boxes):
    """한 장면의 박스 목록 → 여섯 지표 판정(0/1)과 설명용 표시."""
    persons = [b for c, _, b in boxes if c == "person"]
    seats = [b for c, _, b in boxes if c in SEAT]
    tables = [b for c, _, b in boxes if c in TABLE]
    sit = []
    for p in persons:
        low = [p[0], (p[1] + p[3]) / 2, p[2], p[3]]
        area = (low[2] - low[0]) * (low[3] - low[1]) or 1
        if any(inter(low, s) / area >= 0.2 for s in seats):
            sit.append(p)
    group = False
    for i in range(len(persons)):
        for j in range(i + 1, len(persons)):
            a, b = persons[i], persons[j]
            ca = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)
            cb = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
            wbar = ((a[2] - a[0]) + (b[2] - b[0])) / 2
            if np.hypot(ca[0] - cb[0], ca[1] - cb[1]) < wbar * 1.5:
                group = True
    food = any(c in FOOD and any(inter(b, t) > 0 for t in tables) for c, _, b in boxes)
    return {
        "seat": int(bool(seats)),
        "sit": int(bool(sit)),
        "group": int(group),
        "food": int(food),
        "study": int(any(c in STUDY for c, _, _ in boxes)),
        "ride": int(any(c in RIDE for c, _, _ in boxes)),
        "persons": len(persons),
        "sit_boxes": sit,
    }


# 사람 검수(output/검수결과.csv)에서 '좌석이 없는데 좌석으로 잡힌' 장면 — 좌석 판정을 0으로 고친다
FALSE_SEAT = {"JP/NB7ekcQLnM8_00212.jpg", "JP/ZoBYb-ScMxI_00088.jpg", "JP/ZoBYb-ScMxI_00089.jpg",
              "JP/ZoBYb-ScMxI_00128.jpg", "KR/Clk_LUphBy8_00026.jpg", "KR/nSPy-zS7-yg_00060.jpg"}


def per_video(frames, meta):
    vids = defaultdict(list)
    for f, (cc, v, _) in meta.items():
        j = judge(frames.get(f, []))
        if f in FALSE_SEAT:
            j["seat"] = 0
        vids[(cc, v)].append(j)
    rows = []
    for (cc, v), js in sorted(vids.items()):
        row = {"country": cc, "video": v, "n": len(js)}
        for k, _ in IND:
            row[k] = round(100 * np.mean([j[k] for j in js]), 1)
        row["persons"] = round(float(np.mean([j["persons"] for j in js])), 2)
        rows.append(row)
    return rows


def summary(vrows):
    out = []
    for cc in CC:
        rs = [r for r in vrows if r["country"] == cc]
        row = {"country": cc, "영상 수": len(rs), "장면 수": sum(r["n"] for r in rs)}
        for k, name in IND:
            vals = [r[k] for r in rs]
            row[name] = round(float(np.mean(vals)), 1) if vals else 0
            row[name + "_최소"] = min(vals) if vals else 0
            row[name + "_최대"] = max(vals) if vals else 0
        out.append(row)
    return out


def save_csv(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# ─────────────────────────── 그림 ───────────────────────────
def fig_radar(summ):
    labels = [n for _, n in IND]
    ang = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    ang += ang[:1]
    top = max(10, max(r[n] for r in summ for n in labels))
    top = int(np.ceil(top / 10) * 10)
    fig = plt.figure(figsize=(6.2, 6.2), dpi=200)
    ax = fig.add_subplot(polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    for r in summ:
        v = [r[n] for n in labels]
        v += v[:1]
        ax.plot(ang, v, color=COL[r["country"]], lw=2.8, label=NAME[r["country"]], solid_joinstyle="round")
        ax.fill(ang, v, color=COL[r["country"]], alpha=0.10)
        ax.scatter(ang[:-1], v[:-1], s=22, color=COL[r["country"]], zorder=3)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(labels, fontsize=13, color=INK, fontproperties=font_manager.FontProperties(fname=FONT_B))
    ax.tick_params(axis="x", pad=12)
    ax.set_ylim(0, top)
    ax.set_yticks(np.linspace(0, top, 5)[1:])
    ax.set_yticklabels(["{:g}%".format(t) for t in np.linspace(0, top, 5)[1:]], fontsize=9, color=GRAY)
    ax.spines["polar"].set_visible(False)
    ax.grid(color=GRID, lw=1)
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1), frameon=False, fontsize=12, labelcolor=SUB)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "그림_레이더.png"), transparent=False, facecolor="white")
    plt.close(fig)


def fig_dots(vrows, summ):
    fig, axes = plt.subplots(1, len(IND), figsize=(11.5, 3.8), dpi=200, sharey=False)
    fb = font_manager.FontProperties(fname=FONT_B)
    for ax, (k, name) in zip(axes, IND):
        top = 0
        for i, cc in enumerate(CC):
            s = next(r for r in summ if r["country"] == cc)[name]
            vals = [r[k] for r in vrows if r["country"] == cc]
            top = max(top, s, max(vals) if vals else 0)
        top = top * 1.18 or 1
        for i, cc in enumerate(CC):
            s = next(r for r in summ if r["country"] == cc)[name]
            h = max(s, top * 0.01)
            ax.bar(i, h, width=0.56, color=COL[cc], lw=0, zorder=2)
            vals = [r[k] for r in vrows if r["country"] == cc]
            if vals:
                jit = np.linspace(-0.16, 0.16, len(vals)) if len(vals) > 1 else np.zeros(1)
                ax.scatter(jit + i, vals, s=14, color="white", edgecolor=SUB, lw=0.8, zorder=4)
            ax.text(i, h + top * 0.02, "{:.1f}".format(s), ha="center", va="bottom", fontsize=10, color=INK, fontproperties=fb)
        ax.set_xlim(-0.6, len(CC) - 0.4)
        ax.set_ylim(0, top)
        ax.set_title(name, fontsize=13, color=INK, fontproperties=fb, pad=10)
        ax.set_xticks(range(len(CC)))
        ax.set_xticklabels([NAME[c] for c in CC], fontsize=10, color=SUB)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="y", labelsize=8, colors=GRAY, length=0)
        ax.tick_params(axis="x", length=0)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("해당 장면 비율(%)", fontsize=10, color=SUB)
    fig.text(0.5, -0.03, "막대 = 나라 평균, 점 = 영상 하나", ha="center", fontsize=10, color=GRAY)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "그림_지표막대.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


BOXCOL = {"person": (254, 152, 0), "seat": (49, 130, 246), "food": (3, 178, 108), "ride": (162, 52, 199),
          "study": (200, 150, 20)}
KO = {"person": "사람", "chair": "의자", "bench": "벤치", "couch": "소파", "dining table": "테이블",
      "motorcycle": "오토바이", "bicycle": "자전거", "laptop": "노트북", "book": "책"}


def kind(c):
    if c == "person":
        return "person"
    if c in SEAT:
        return "seat"
    if c in FOOD:
        return "food"
    if c in RIDE:
        return "ride"
    if c in STUDY:
        return "study"
    return None


def draw(file, boxes, sit_boxes=()):
    img = Image.open(os.path.join(FR, file)).convert("RGB")
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT_B, max(12, img.width // 40))
    for c, conf, b in boxes:
        k = kind(c)
        if not k or (k == "food" and c == "bottle"):
            continue
        col = BOXCOL[k]
        d.rectangle(b, outline=col, width=max(2, img.width // 250))
        lab = KO.get(c, "")
        if c == "person" and any(np.allclose(b, s) for s in sit_boxes):
            lab = "앉은 사람"
        if lab:
            tw = d.textlength(lab, font=f)
            d.rectangle([b[0], b[1] - f.size - 4, b[0] + tw + 6, b[1]], fill=col)
            d.text((b[0] + 3, b[1] - f.size - 3), lab, fill="white", font=f)
    return img


# 자동 점수 상위 12장을 사람이 보고 고른 예시 장면(자막·그래픽이 덮인 장면, 상품 클로즈업 제외)
MANUAL = {"KR": ["KR/Ab-j6YSMkMM_00061.jpg", "KR/AeqkHad6Ijc_00023.jpg"],
          "JP": ["JP/ZoBYb-ScMxI_00072.jpg", "JP/exQYapFKyJM_00046.jpg"],
          "VN": ["VN/UV8pqZCBi10_00100.jpg", "VN/UV8pqZCBi10_00007.jpg"]}


def fig_examples(frames, meta):
    """나라별로 좌석·사람이 가장 잘 보이는 장면 2장씩 → 3×2 모음."""
    picks = {}
    for cc in CC:
        cand = []
        for f, (c, v, sc) in meta.items():
            if c != cc or sc == "out":      # 예시는 매장 안 장면에서만 고른다
                continue
            bx = frames.get(f, [])
            if any(c == "person" and (b[2] - b[0]) * (b[3] - b[1]) > 0.2 * 640 * 360 for c, _, b in bx):
                continue                    # 얼굴 클로즈업은 예시에서 뺀다
            j = judge(bx)
            if not j["seat"] and not j["persons"]:
                continue                    # 좌석도 사람도 없는 장면(상품 클로즈업 등)은 예시로 쓰지 않는다
            score = 3 * j["sit"] + 2 * j["seat"] + j["group"] + j["food"] + min(j["persons"], 4) * 0.3 + j["ride"]
            cand.append((score, v, f))
        cand.sort(reverse=True)
        chosen, used = [], set()
        for s, v, f in cand:          # 서로 다른 영상에서 고른다
            if v in used:
                continue
            chosen.append(f)
            used.add(v)
            if len(chosen) == 2:
                break
        picks[cc] = [f for f in MANUAL.get(cc, []) if f in meta] or chosen
    W, H = 640, 360
    sheet = Image.new("RGB", (W * 2 + 30, (H + 50) * 3 + 10), "white")
    d = ImageDraw.Draw(sheet)
    ft = ImageFont.truetype(FONT_B, 26)
    for i, cc in enumerate(CC):
        y = i * (H + 50) + 10
        d.text((10, y), NAME[cc], fill=COL[cc], font=ft)
        for k, f in enumerate(picks[cc]):
            j = judge(frames.get(f, []))
            im = draw(f, frames.get(f, []), j["sit_boxes"]).resize((W, H))
            sheet.paste(im, (10 + k * (W + 10), y + 38))
    sheet.save(os.path.join(OUT, "그림_탐지예시.png"))
    # 슬라이드용 낱장
    for cc in CC:
        for k, f in enumerate(picks[cc]):
            j = judge(frames.get(f, []))
            draw(f, frames.get(f, []), j["sit_boxes"]).save(os.path.join(OUT, "예시_{}_{}.jpg".format(cc, k + 1)), quality=92)
    return picks


def review_sheet(frames, meta):
    """사람이 직접 탐지 결과를 확인할 무작위 50장(나라별 균등)."""
    rnd = random.Random(7)
    for old in os.listdir(os.path.join(OUT, "검수")):   # 이전 실행의 검수 이미지는 지운다
        os.remove(os.path.join(OUT, "검수", old))
    files = []
    for cc in CC:
        fs = sorted(f for f, (c, _, _) in meta.items() if c == cc)
        files += rnd.sample(fs, min(17, len(fs)))
    for i, f in enumerate(files[:50]):
        j = judge(frames.get(f, []))
        draw(f, frames.get(f, []), j["sit_boxes"]).save(os.path.join(OUT, "검수", "{:02d}_{}".format(i + 1, f.replace("/", "_"))))
    return files[:50]


def main():
    frames, meta = load()
    vrows = per_video(frames, meta)
    summ = summary(vrows)
    save_csv(os.path.join(OUT, "지표_영상별.csv"), vrows)
    save_csv(os.path.join(OUT, "지표_요약.csv"), summ)
    fig_radar(summ)
    fig_dots(vrows, summ)
    picks = fig_examples(frames, meta)
    review_sheet(frames, meta)
    for r in summ:
        print(NAME[r["country"]], "영상", r["영상 수"], "장면", r["장면 수"],
              " ".join("{} {:.1f}%".format(n, r[n]) for _, n in IND))
    print("예시", picks)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
