# -*- coding: utf-8 -*-
"""
03. 매장 장면만 골라내고(CLIP), 골라낸 장면에서 사람·사물을 찾는다(YOLO)

- 장면 분류: CLIP(openai/clip-vit-base-patch32)에 장면 설명 문장 10개를 주고 가장 가까운 것을 고른다.
  매장 안 / 매장 좌석 / 매장 입구 세 가지로 분류된 장면만 남기고, 얼굴 클로즈업·음식 클로즈업·자막 화면·
  집 안·도로·차 안·창고는 버린다.
- 영상 하나가 결과를 좌우하지 않도록 영상당 최대 PER_VIDEO장만 무작위로 쓴다.
- 객체 탐지: YOLO11s(COCO 80종 사전학습)로 신뢰도 CONF 이상인 박스를 모두 기록한다.
- 이미 처리한 프레임은 건너뛴다.

산출: data/장면분류.csv, data/탐지결과.csv
"""

import csv
import os
import random
import sys

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
from ultralytics import YOLO

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, "data", "frames")
FRAMES = os.path.join(HERE, "data", "프레임목록.csv")
SCENE = os.path.join(HERE, "data", "장면분류.csv")
DET = os.path.join(HERE, "data", "탐지결과.csv")

PER_VIDEO = 40
CONF = 0.35
KEEP_P = 0.35
random.seed(7)

PROMPTS = [
    ("in", "a photo of the inside of a convenience store with shelves of products"),
    ("seat", "a photo of people sitting at tables inside a convenience store"),
    ("out", "a photo of a convenience store entrance seen from the street"),
    ("x", "a close-up photo of a person's face talking to the camera"),
    ("x", "a close-up photo of food or a product held in a hand"),
    ("x", "a screenshot of text or a title screen"),
    ("x", "a photo of a room inside a house"),
    ("x", "a photo of a street or road with no shop"),
    ("x", "a photo taken inside a car"),
    ("x", "a photo of a storage room or warehouse"),
]


def imread(path):
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save(path, rows, fields):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def classify(frames):
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").eval()
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    texts = [p for _, p in PROMPTS]
    out = []
    for k in range(0, len(frames), 32):
        batch = frames[k:k + 32]
        imgs = [Image.fromarray(cv2.cvtColor(imread(os.path.join(FR, r["file"])), cv2.COLOR_BGR2RGB)) for r in batch]
        with torch.no_grad():
            inp = proc(text=texts, images=imgs, return_tensors="pt", padding=True)
            prob = model(**inp).logits_per_image.softmax(dim=1).numpy()
        for r, p in zip(batch, prob):
            j = int(p.argmax())
            tag = PROMPTS[j][0] if p[j] >= KEEP_P else "x"
            out.append({"country": r["country"], "video": r["video"], "file": r["file"],
                        "scene": tag, "p": round(float(p[j]), 3)})
        print("  장면 분류 {}/{}".format(min(k + 32, len(frames)), len(frames)), flush=True)
    return out


def main():
    frames = load(FRAMES)
    scenes = load(SCENE)
    done = {r["file"] for r in scenes}
    todo = [r for r in frames if r["file"] not in done]
    if todo:
        scenes += classify(todo)
        save(SCENE, scenes, ["country", "video", "file", "scene", "p"])

    # 영상당 최대 PER_VIDEO장
    keep = {}
    for r in scenes:
        if r["scene"] != "x":
            keep.setdefault(r["video"], []).append(r)
    use = []
    for v, rs in keep.items():
        rs.sort(key=lambda r: r["file"])
        use += rs if len(rs) <= PER_VIDEO else random.Random(v).sample(rs, PER_VIDEO)

    dets = load(DET)
    done = {r["file"] for r in dets}
    todo = [r for r in use if r["file"] not in done]
    yolo = YOLO("yolo11s.pt")
    for i, r in enumerate(todo):
        img = imread(os.path.join(FR, r["file"]))
        h, w = img.shape[:2]
        res = yolo.predict(img, conf=CONF, verbose=False)[0]
        rows = []
        for b in res.boxes:
            x1, y1, x2, y2 = [float(v) for v in b.xyxy[0]]
            rows.append({"country": r["country"], "video": r["video"], "file": r["file"], "scene": r["scene"],
                         "cls": res.names[int(b.cls)], "conf": round(float(b.conf), 3),
                         "x1": round(x1), "y1": round(y1), "x2": round(x2), "y2": round(y2), "W": w, "H": h})
        if not rows:  # 아무것도 없는 장면도 분모에 들어가야 하므로 빈 줄을 남긴다
            rows.append({"country": r["country"], "video": r["video"], "file": r["file"], "scene": r["scene"],
                         "cls": "", "conf": "", "x1": "", "y1": "", "x2": "", "y2": "", "W": w, "H": h})
        dets += rows
        if (i + 1) % 50 == 0 or i + 1 == len(todo):
            print("  탐지 {}/{}".format(i + 1, len(todo)), flush=True)
            save(DET, dets, ["country", "video", "file", "scene", "cls", "conf", "x1", "y1", "x2", "y2", "W", "H"])

    cnt = {}
    for r in use:
        cnt.setdefault(r["country"], {}).setdefault(r["scene"], 0)
        cnt[r["country"]][r["scene"]] += 1
    print("분석 장면 수", cnt)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
