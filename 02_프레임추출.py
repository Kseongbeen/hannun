# -*- coding: utf-8 -*-
"""
02. 영상에서 프레임을 뽑고 흔들린 장면·겹치는 장면을 걸러낸다

- 2초에 1장씩 뽑는다(인트로·아웃트로 앞뒤 5%는 버림).
- 흔들림: 라플라시안 분산(선명도 점수)이 BLUR_MIN보다 낮으면 버린다.
- 중복: 바로 앞에 남긴 장면과 32×32 흑백 축소본의 평균 차이가 DUP_MAX보다 작으면 버린다.
- 이미 뽑은 영상은 건너뛴다(영상이 계속 받아지는 중에도 다시 돌리면 된다).

산출: data/frames/{KR,JP,VN}/{영상id}_{초}.jpg, data/프레임목록.csv
"""

import csv
import glob
import os
import subprocess
import sys

import cv2
import imageio_ffmpeg
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(HERE, "data", "video")
FR = os.path.join(HERE, "data", "frames")
LIST = os.path.join(HERE, "data", "프레임목록.csv")

STEP_S = 2.0
BLUR_MIN = 60.0
DUP_MAX = 6.0
FIELDS = ["country", "video", "sec", "file", "sharp"]


def small(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.resize(g, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)


def imread(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)


def extract(path, cc, vid):
    """ffmpeg로 STEP_S초마다 한 장씩 뽑은 뒤(가장 빠름), 흔들림·중복을 지운다."""
    out = os.path.join(FR, cc)
    os.makedirs(out, exist_ok=True)
    pat = os.path.join(out, vid + "_%05d.jpg")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-y", "-i", path,
                    "-vf", "fps=1/{},scale=640:-2".format(STEP_S), "-q:v", "3", pat], check=True)
    files = sorted(glob.glob(os.path.join(out, vid + "_*.jpg")))
    lo, hi = int(len(files) * 0.05), int(len(files) * 0.95)   # 인트로·아웃트로 제외
    rows, prev = [], None
    for k, fp in enumerate(files):
        img = imread(fp)
        keep = lo <= k < hi and img is not None
        if keep:
            sharp = cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
            keep = sharp >= BLUR_MIN
        if keep:
            s = small(img)
            keep = prev is None or np.abs(s - prev).mean() >= DUP_MAX
            if keep:
                prev = s
        if not keep:
            os.remove(fp)
            continue
        sec = int(k * STEP_S)
        rows.append({"country": cc, "video": vid, "sec": sec,
                     "file": "{}/{}".format(cc, os.path.basename(fp)), "sharp": round(sharp, 1)})
    return rows


def main():
    rows = []
    if os.path.exists(LIST):
        with open(LIST, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    done = {r["video"] for r in rows}
    for path in sorted(glob.glob(os.path.join(VID, "*", "*.mp4"))):
        cc = os.path.basename(os.path.dirname(path))
        vid = os.path.splitext(os.path.basename(path))[0]
        if vid in done or path.endswith(".part"):
            continue
        new = extract(path, cc, vid)
        rows.extend(new)
        print("[{}] {} → {}장".format(cc, vid, len(new)), flush=True)
        with open(LIST, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
    by = {}
    for r in rows:
        by[r["country"]] = by.get(r["country"], 0) + 1
    print("합계", by)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
