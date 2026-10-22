# -*- coding: utf-8 -*-
"""
14. '편의점은 하나의 예시, YOLO는 다른 현장 비교에도 그대로 쓸 수 있다'를 기획서·발표·대본에 넣는다

- 기획서: 2-1 차별성에 '범용성' 항목 추가(바로 앞 '해석의 몫' 항목과 같은 서식), 2-2 사례 자료 항목과
  3-2 대상 확장 항목에 구체 예시(거리·공원·캠퍼스에서 무엇을 세고 어떤 지표가 되는지) 추가
- 발표: 8쪽 모델 설명, 17쪽 확장성 상자 / 대본: 9·17쪽
- 사용자가 고친 현재 파일 위에 해당 문구만 바꾸고, 바꾸기 전 파일은 output/_자동백업/에 남긴다.
"""

import datetime
import os
import re
import shutil
import sys
import zipfile
import xml.dom.minidom

from docx import Document
from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
HWP, PPT, DOCX = (os.path.join(OUT, f) for f in ("한눈_기획서.hwpx", "한눈_발표.pptx", "한눈_발표대본.docx"))
S12 = os.path.join(HERE, "12_개념반영_대본.py")

EXAMPLES = "거리(자동차·버스·오토바이·자전거 → 이동 수단 구성), 공원·광장(사람·벤치·개 → 머무름·반려동물 동반), 캠퍼스(사람·의자·테이블 → 혼자·무리 비율)"

HWP_EDITS = [
    ("원본은 재배포하지 않으며, 영상 목록은 발표 자료 부록에 수록</hp:t>",
     "원본은 재배포하지 않으며, 영상 목록은 발표 자료 부록에 수록. 편의점은 여러 비교 주제 중 하나로 고른 예시</hp:t>"),
    ("편의점은 예시. 카페·전통시장·캠퍼스·거리 간판·급식 등 현장 이미지로 비교할 수 있는 모든 과제에 같은 방식 적용",
     "편의점은 예시. 같은 탐지 모델로 " + EXAMPLES + " 등 현장 이미지로 비교할 수 있는 과제 전반에 적용"),
]
NEW_BULLET = ("범용성:", " 편의점은 하나의 예시. YOLO(COCO 80종)는 사람·자동차·버스·오토바이·자전거·벤치·개 등 일상 사물을 "
              "찾으므로, 지표 규칙만 바꾸면 다른 현장 비교 과제에도 그대로 쓸 수 있음(3-2 확장 방향 참고)")

PPT_EDITS = {
    8: [("모델: YOLO11s(COCO 80종 사전학습)", "모델: YOLO11s(COCO 80종 사전학습) — 편의점 외 다른 현장 사진에도 그대로 사용")],
    17: [("편의점은 예시 — 카페 · 전통시장 · 캠퍼스 · 거리 간판 · 급식 등 문화를 비교하는 모든 과제에 같은 방식 적용",
          "편의점은 예시 — YOLO는 사람·자동차·자전거·벤치·개 등 일상 사물 80종을 찾으므로, 지표 규칙만 바꾸면 "
          "거리(이동 수단)·공원(머무름·반려동물)·캠퍼스(혼자·무리) 등 어떤 현장 비교 과제에도 적용")],
}
SCRIPT_EDITS = [
    ("이번 파일럿에서는 제가 그 역할을 대신해 한국, 일본,",
     "이번 파일럿에서는 제가 그 역할을 대신해, 여러 비교 주제 중 하나의 예시로 한국, 일본,"),
    ("편의점은 예시일 뿐, 문화를 비교하는 모든 과제에 같은 방식을 쓸 수 있습니다.",
     "편의점은 예시일 뿐입니다. YOLO는 사람, 자동차, 자전거, 벤치, 개처럼 일상 사물 80종을 찾기 때문에, 지표 규칙만 바꾸면 "
     "거리의 이동 수단, 공원의 머무름, 캠퍼스의 혼자·무리 비율처럼 어떤 현장 비교에도 같은 방식을 쓸 수 있습니다."),
]


def backup(path):
    d = os.path.join(OUT, "_자동백업")
    os.makedirs(d, exist_ok=True)
    stem, ext = os.path.splitext(os.path.basename(path))
    shutil.copy2(path, os.path.join(d, "{}_{}{}".format(stem, datetime.datetime.now().strftime("%m%d_%H%M%S"), ext)))


def para_span(x, needle):
    k = x.find(needle)
    assert k > 0, needle
    ps = x.rfind("<hp:p ", 0, k)
    depth, i = 0, ps
    while True:
        a, b = x.find("<hp:p ", i), x.find("</hp:p>", i)
        if a != -1 and a < b:
            depth, i = depth + 1, a + 5
        else:
            depth, i = depth - 1, b + len("</hp:p>")
            if depth == 0:
                return ps, i


def build_hwp():
    z = zipfile.ZipFile(HWP)
    x = z.read("Contents/section0.xml").decode("utf-8")
    for a, b in HWP_EDITS:
        assert x.count(a) == 1, (a, x.count(a))
        x = x.replace(a, b)
    # '해석의 몫' 문단을 본떠 '범용성' 문단을 바로 뒤에 넣는다(글자·문단 모양 그대로)
    ps, pe = para_span(x, "<hp:t>해석의 몫:</hp:t>")
    tpl = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", x[ps:pe], flags=re.S)
    label = re.search(r"<hp:t>해석의 몫:</hp:t>", tpl)
    body = re.search(r"<hp:t> AI는 차이의 크기만.*?</hp:t>", tpl, re.S)
    assert label and body
    new = tpl[:body.start()] + "<hp:t>{}</hp:t>".format(NEW_BULLET[1]) + tpl[body.end():]
    new = new.replace("<hp:t>해석의 몫:</hp:t>", "<hp:t>{}</hp:t>".format(NEW_BULLET[0]), 1)
    x = x[:pe] + new + x[pe:]
    x = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", x, flags=re.S)
    xml.dom.minidom.parseString(x.encode("utf-8"))
    tmp = HWP + ".tmp"
    with zipfile.ZipFile(tmp, "w") as out:
        for info in z.infolist():
            data = x.encode("utf-8") if info.filename == "Contents/section0.xml" else z.read(info.filename)
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            out.writestr(zi, data)
    z.close()
    os.replace(tmp, HWP)


def set_par(slide, old, new):
    for sh in slide.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                full = "".join(r.text for r in p.runs)
                if old in full and p.runs:
                    p.runs[0].text = full.replace(old, new)
                    for r in p.runs[1:]:
                        r.text = ""
                    return
    raise AssertionError(old)


def build_ppt():
    prs = Presentation(PPT)
    slides = list(prs.slides)
    for no, edits in PPT_EDITS.items():
        for a, b in edits:
            set_par(slides[no - 1], a, b)
    for sl in slides:
        tf = sl.notes_slide.notes_text_frame
        if tf is None:
            continue
        for a, b in SCRIPT_EDITS:
            if a in tf.text:
                tf.text = tf.text.replace(a, b)
    prs.save(PPT)


def build_script():
    d = Document(DOCX)
    hit = 0
    for p in d.paragraphs:
        for a, b in SCRIPT_EDITS:
            if a in p.text:
                full = p.text.replace(a, b)
                p.runs[0].text = full
                for r in p.runs[1:]:
                    r.text = ""
                hit += 1
    assert hit == len(SCRIPT_EDITS), hit
    d.save(DOCX)
    # 대본 원본(12 스크립트의 SCRIPT)도 같게 — 줄바꿈으로 나뉜 문자열이라 공백을 무시하고 맞춘다
    s = open(S12, encoding="utf-8").read()
    for a, b in SCRIPT_EDITS:
        pat = r'\s*"?\s*'.join(re.escape(w) for w in a.split(" "))
        m = re.search(pat.replace(r"\ ", r"\s*"), s)
        if m:
            s = s[:m.start()] + b + s[m.end():]
    open(S12, "w", encoding="utf-8").write(s)


def main():
    for f in (HWP, PPT, DOCX):
        backup(f)
    build_hwp()
    build_ppt()
    build_script()
    print("[저장]", HWP, PPT, DOCX, sep="\n  ")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
