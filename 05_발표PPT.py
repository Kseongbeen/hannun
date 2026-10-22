# -*- coding: utf-8 -*-
"""
05. 발표 PPT(16:9)를 만든다 — 캔바에서 불러와 다듬을 것을 전제로 도형·글상자·그림만 쓴다

- 디자인: 토스 디자인 시스템(TDS) 느낌 — Pretendard, 토스 블루(#3182F6)와 그레이 스케일, 넓은 여백, 큰 둥근 카드

- 실험 수치와 그림은 output/지표_요약.csv, output/그림_*.png, output/예시_*.jpg에서 읽어 자동으로 넣는다.
- 모든 본문 슬라이드에 발표 대본(노트)을 단다.

산출: output/한눈_발표.pptx
"""

import csv
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
PPTX = os.path.join(OUT, "한눈_발표.pptx")

FONT = "Pretendard"          # 사용자 글꼴로 설치(없으면 캔바·파워포인트가 대체 글꼴 사용)
W, H, M = Inches(13.333), Inches(7.5), Inches(0.6)


def rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# TDS 그레이 스케일: grey900 · grey700 · grey500 · grey200 · grey100
INK, SUB, MUTE, LINE, BG, WHITE = rgb("191F28"), rgb("4E5968"), rgb("8B95A1"), rgb("E5E8EB"), rgb("F2F4F6"), rgb("FFFFFF")
ACC, ACC_SOFT = rgb("3182F6"), rgb("E8F3FF")          # 토스 블루 / blue50
ON_ACC = rgb("D6E8FF")                                 # 파란 바탕 위 보조 글자
CCOL = {"KR": rgb("3182F6"), "JP": rgb("F04452"), "VN": rgb("03B26C")}
CSOFT = {"KR": rgb("E8F3FF"), "JP": rgb("FFEEEE"), "VN": rgb("E5F8EF")}
NAME = {"KR": "한국", "JP": "일본", "VN": "베트남"}
IND = ["좌석", "착석", "무리", "오토바이·자전거"]
RADIUS = Inches(0.24)


# ─────────────────────────── 도구 ───────────────────────────
def blank(prs, bg=WHITE):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = bg
    return s


def text(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=0.3):
    """lines: [(글, 크기, 굵게, 색)] — 글 안에 [[ ]]로 감싼 부분은 강조색."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, (t, size, bold, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(size * spacing)
        parts = t.replace("]]", "[[").split("[[")
        for k, part in enumerate(parts):
            if not part:
                continue
            r = p.add_run()
            r.text = part
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = bold or k % 2 == 1
            r.font.color.rgb = ACC if k % 2 == 1 else color
    return tb


def box(slide, x, y, w, h, fill=BG, line=None, lines=(), anchor=MSO_ANCHOR.TOP, align=PP_ALIGN.LEFT, r=RADIUS, pad=0.28):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    sh.adjustments[0] = min(0.5, r / min(w, h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1.25)
    sh.shadow.inherit = False
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(pad)
    tf.margin_top = tf.margin_bottom = Inches(0.18)
    for i, (t, size, bold, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(size * 0.35)
        parts = t.replace("]]", "[[").split("[[")
        for k, part in enumerate(parts):   # [[ ]] 안은 강조(밝은 보라)
            if not part:
                continue
            rr = p.add_run()
            rr.text = part
            rr.font.name = FONT
            rr.font.size = Pt(size)
            rr.font.bold = bold or k % 2 == 1
            rr.font.color.rgb = (ON_ACC if fill == ACC else ACC) if k % 2 == 1 else color   # 파란 바탕이면 연한 글자
    return sh


def pill(slide, x, y, w, h, label, fill, color, size=12):
    return box(slide, x, y, w, h, fill=fill, lines=[(label, size, True, color)],
               anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, r=h / 2, pad=0.05)


def arrow(slide, x, y, w=Inches(0.3), h=Inches(0.36), color=rgb("D1D6DB")):
    sh = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sh.shadow.inherit = False


def header(slide, section, title, sub=None):
    """TDS식 제목: 작은 파란 섹션 이름 → 큰 굵은 제목 → 회색 설명."""
    text(slide, M, Inches(0.42), W - 2 * M, Inches(0.35), [(section, 14, True, ACC)])
    text(slide, M, Inches(0.78), W - 2 * M, Inches(0.8), [(title, 30, True, INK)])
    if sub:
        text(slide, M, Inches(1.45), W - 2 * M, Inches(0.5), [(sub, 16, False, SUB)])


def foot(slide, n, src=None):
    text(slide, W - M - Inches(0.6), H - Inches(0.45), Inches(0.6), Inches(0.3), [(str(n), 11, True, MUTE)], align=PP_ALIGN.RIGHT)
    if src:
        text(slide, M, H - Inches(0.45), W - 2 * M - Inches(1), Inches(0.3), [("출처: " + src, 9, False, MUTE)])


def note(slide, t):
    slide.notes_slide.notes_text_frame.text = t


def pic(slide, path, x, y, w=None, h=None):
    if os.path.exists(path):
        return slide.shapes.add_picture(path, x, y, w, h)
    box(slide, x, y, w or Inches(4), h or Inches(3), fill=BG,
        lines=[("그림 준비 중: " + os.path.basename(path), 12, False, MUTE)], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)


# ─────────────────────────── 데이터 ───────────────────────────
def load_summary():
    p = os.path.join(OUT, "지표_요약.csv")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8-sig") as f:
        return {r["country"]: r for r in csv.DictReader(f)}


def val(S, cc, k):
    try:
        return float(S[cc][k])
    except (KeyError, ValueError):
        return 0.0


# ─────────────────────────── 슬라이드 ───────────────────────────
def s_cover(prs):
    s = blank(prs)
    text(s, M, Inches(0.7), Inches(9), Inches(0.4), [("2026 HUSS · AI를 활용한 어울림 공모전", 15, True, MUTE)])
    text(s, M, Inches(1.9), Inches(11), Inches(1.6), [("한눈", 96, True, ACC)])
    text(s, M, Inches(3.65), Inches(11.5), Inches(1.4),
         [("번역 없이 문화를 비교하는 AI 비전 팀플 도구", 34, True, INK),
          ("외국인 팀원의 조사가 '부록'이 아닌 '본론'이 되도록", 20, False, SUB)])
    for i, cc in enumerate(["KR", "JP", "VN"]):
        pill(s, M + Inches(1.3) * i, Inches(5.45), Inches(1.15), Inches(0.46), NAME[cc], CSOFT[cc], CCOL[cc], size=14)
    text(s, M, Inches(6.6), Inches(9), Inches(0.4), [("주제 ① 다양한 문화의 어울림  ×  ③ 중심과 주변의 어울림", 14, False, MUTE)])
    note(s, "안녕하십니까. 번역 없이 문화를 비교하는 AI 비전 팀플 도구, '한눈'을 발표하겠습니다.")


def s_team(prs, n):
    s = blank(prs)
    header(s, "목차 · 발표자", "오늘 이야기할 순서")
    # 왼쪽: 발표자 카드
    box(s, M, Inches(2.0), Inches(4.2), Inches(4.4), fill=ACC_SOFT)
    # 사진 자리(캔바에서 이 원에 사진을 끌어다 놓으면 됨)
    ph = s.shapes.add_shape(MSO_SHAPE.OVAL, M + Inches(0.35), Inches(2.35), Inches(1.75), Inches(1.75))
    ph.fill.solid()
    ph.fill.fore_color.rgb = WHITE
    ph.line.color.rgb = rgb("B0B8C1")
    ph.line.width = Pt(1.25)
    ph.line.dash_style = 4          # 점선
    ph.shadow.inherit = False
    ph.name = "사진 자리"
    tf = ph.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    r = tf.paragraphs[0].add_run()
    r.text = "사진"
    r.font.name, r.font.size, r.font.bold = FONT, Pt(13), True
    r.font.color.rgb = MUTE
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    text(s, M + Inches(2.3), Inches(2.7), Inches(1.8), Inches(1.1),
         [("발표자 · 개인 참가", 12, True, ACC), ("김성빈", 34, True, INK)], spacing=0.05)
    text(s, M + Inches(0.35), Inches(4.45), Inches(3.6), Inches(1.9),
         [("상명대학교 융합공과대학", 14, False, SUB), ("지능·데이터융합학부 휴먼AI공학전공", 14, False, SUB),
          ("GDGoC SMU 활동", 13, True, ACC), ("기획 · 데이터 · AI 분석 · 프로토타입 · 발표", 13, False, SUB)], spacing=0.35)
    # 오른쪽: 목차
    toc = [("01", "문제 인식", "외국인 팀원의 조사는 왜 '부록'이 되는가"),
           ("02", "해결 방안", "번역하지 말고, 보게 하자 — 한눈의 작동 방식"),
           ("03", "파일럿 실험", "한국·일본·베트남 편의점을 같은 AI로 재 보기"),
           ("04", "프로토타입", "해석 카드와 5단계 웹 프로토타입"),
           ("05", "기대효과와 한계", "어울림을 만드는 구조, 그리고 남은 과제")]
    x = M + Inches(4.6)
    for k, (no, t, d) in enumerate(toc):
        y = Inches(2.0) + Inches(0.9) * k
        text(s, x, y, Inches(0.9), Inches(0.8), [(no, 28, True, ACC)], anchor=MSO_ANCHOR.MIDDLE)
        text(s, x + Inches(1.0), y + Inches(0.08), W - M - x - Inches(1.0), Inches(0.8),
             [(t, 18, True, INK), (d, 13, False, SUB)], spacing=0.1)
    foot(s, n)
    note(s, "저는 상명대학교 휴먼AI공학전공 김성빈입니다. 개인으로 참가해 기획부터 데이터, AI 분석, 프로토타입까지 맡았습니다. "
            "오늘은 문제 인식, 해결 방안, 파일럿 실험, 프로토타입, 기대효과와 한계 순서로 말씀드리겠습니다.")


def s_hook(prs, n):
    s = blank(prs)
    header(s, "문제 인식", "팀원 4명 중 1명의 조사가, 슬라이드 1장이 됩니다")
    # 왼쪽: 흔한 팀플 발표 목차
    items = ["1. 서론", "2. 한국 편의점 현황", "3. 문제점 분석", "4. 해외 사례 (베트남)", "5. 개선 전략", "6. 결론"]
    y0 = Inches(2.1)
    for i, t in enumerate(items):
        hot = "해외" in t
        box(s, M, y0 + Inches(0.62) * i, Inches(5.2), Inches(0.52), fill=ACC_SOFT if hot else BG,
            line=ACC if hot else None, lines=[(t, 16, hot, ACC if hot else INK)], anchor=MSO_ANCHOR.MIDDLE)
    text(s, M, y0 + Inches(0.62) * 6 + Inches(0.1), Inches(5.2), Inches(0.4),
         [("외국인 팀원의 조사는 대개 이 한 장에 들어갑니다", 12, False, MUTE)])
    # 오른쪽: 겪은 일
    x = Inches(6.6)
    box(s, x, Inches(2.1), Inches(6.1), Inches(1.55), fill=BG, lines=[
        ("겪은 일 ①  뭘 맡겨야 할지 애매하다", 17, True, INK),
        ("한국어 소통이 어려운 팀원에게 줄 역할이 보이지 않음", 14, False, SUB)])
    box(s, x, Inches(3.85), Inches(6.1), Inches(1.55), fill=BG, lines=[
        ("겪은 일 ②  찾아온 자료가 이어지지 않는다", 17, True, INK),
        ("모국어 자료는 번역을 거쳐도 한국 자료와 비교 기준이 달라 본론에 섞이지 않음", 14, False, SUB)])
    box(s, x, Inches(5.6), Inches(6.1), Inches(0.9), fill=ACC, lines=[
        ("결과: 외국인 팀원의 조사 = '해외 사례' 부록", 17, True, WHITE)], anchor=MSO_ANCHOR.MIDDLE)
    foot(s, n)
    note(s, "외국인 유학생과 팀플을 해 보신 분이라면 익숙한 장면일 겁니다. 유학생 팀원에게 무엇을 맡길지 애매하고, "
            "그 팀원이 모국어로 열심히 찾아온 자료는 한국 자료와 이어지지 않습니다. 결국 발표 목차에서 유학생의 조사는 "
            "'해외 사례' 한 장으로 따로 떨어져 나갑니다. 팀원 네 명 중 한 명의 조사가 슬라이드 한 장이 되는 셈입니다.")


def s_status(prs, n):
    s = blank(prs)
    header(s, "현황", "같은 강의실, 두 개의 섬", "숫자로 본 외국인 유학생과 팀플")
    cards = [("30.7만 명", "국내 대학 외국인 유학생", "2023년 18.2만 → 2026년 30.7만, 3년 새 1.7배",
              "교육부 집계(2026년 4월 기준)"),
             ("49.9%", "교육부 권고 어학 기준을 충족한 유학생", "4년제 학위과정 94,025명 중 46,913명 — 절반은 수업 언어부터 벽",
              "한국경제(2026.1.27.), 국회 교육위원회 자료"),
             ("36.6%", "\"팀 프로젝트 참여가 어렵다\"", "한국어 수업의 어려움으로 꼽은 비율 · 토의 참여는 50.9%",
              "서울대 다양성위원회(2018), 유학생 432명")]
    cw = (W - 2 * M - Inches(0.6)) / 3
    for i, (big, label, body, src) in enumerate(cards):
        x = M + (cw + Inches(0.3)) * i
        box(s, x, Inches(2.15), cw, Inches(3.45), fill=BG, lines=[(big, 44, True, ACC), (label, 17, True, INK),
                                                                  (body, 14, False, SUB), (src, 11, False, MUTE)])
    box(s, M, Inches(5.9), W - 2 * M, Inches(0.8), fill=ACC_SOFT, lines=[
        ("유학생은 빠르게 늘지만, 팀플 안에서는 섞이지 못함 — 지금의 해결책(한국어 교육·번역기·버디)은 모두 유학생을 '채워야 할 부족함'으로 봄",
         15, True, ACC)], anchor=MSO_ANCHOR.MIDDLE)
    foot(s, n, "헤럴드경제(2026.9.8.) 교육부 집계 / 한국경제(2026.1.27.) 국회 교육위원회 자료 / 서울대 다양성위원회(2018), 경향신문(2018.12.3.) 보도")
    note(s, "국내 대학의 외국인 유학생은 올해 4월 30만 7천 명으로, 3년 사이 1.7배가 됐습니다. 그런데 학위과정 유학생 가운데 "
            "교육부 권고 어학 기준을 충족한 학생은 49.9%, 절반뿐입니다. 서울대 조사에서 유학생의 36.6%는 한국어 수업에서 "
            "팀 프로젝트 참여가 어렵다고 답했고, 토의 참여가 어렵다는 답은 절반이 넘었습니다. 유학생은 빠르게 늘지만, "
            "팀플 안에서는 섞이지 못하는 두 개의 섬입니다.")


def s_problem(prs, n):
    s = blank(prs)
    header(s, "문제 정의", "외국인 팀원의 조사는 '부록' 취급을 받는다",
           "한국 자료는 중심, 외국 자료는 주변 — 이 위계가 팀플 결과물 안에서 그대로 반복됨")
    causes = [("번역의 거리감", "글 자료는 반드시 번역을 거치고, 번역된 자료는 '남의 나라 이야기'로 읽힘"),
              ("비교 기준 불일치", "한국 팀원은 매출·점포 수, 유학생은 현지 후기·기사 — 나란히 놓을 기준이 없음"),
              ("발표 직전 병합", "각자 조사한 뒤 마지막에 이어 붙이므로 둘을 잇는 논리가 생기지 않음")]
    cw = (W - 2 * M - Inches(0.6)) / 3
    for i, (t, b) in enumerate(causes):
        x = M + (cw + Inches(0.3)) * i
        pill(s, x, Inches(2.35), Inches(1.2), Inches(0.36), "원인 {}".format(i + 1), ACC, WHITE, size=11)
        box(s, x, Inches(2.85), cw, Inches(2.3), fill=BG, lines=[(t, 20, True, INK), (b, 15, False, SUB)])
    box(s, M, Inches(5.5), W - 2 * M, Inches(1.1), fill=ACC, lines=[
        ("핵심은 언어 실력이 아니라, [[서로 다른 언어의 자료가 같은 기준 위에 놓이지 못하는 구조]]", 18, True, WHITE)],
        anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    foot(s, n)
    note(s, "그래서 문제를 이렇게 정의했습니다. 외국인 팀원의 조사는 부록 취급을 받는다. 원인은 세 가지입니다. "
            "번역을 거친 자료는 남의 나라 이야기가 되고, 한국 자료와 비교 기준이 다르며, 발표 직전에 이어 붙이니 논리가 "
            "생기지 않습니다. 핵심은 언어 실력이 아니라, 서로 다른 언어의 자료가 같은 기준 위에 놓이지 못하는 구조입니다.")


def s_idea(prs, n):
    s = blank(prs, bg=ACC)
    text(s, M, Inches(1.6), W - 2 * M, Inches(1.2), [("번역하지 말고, 보게 하자", 48, True, WHITE)], align=PP_ALIGN.CENTER)
    text(s, M, Inches(2.9), W - 2 * M, Inches(1.2),
         [("사진과 영상은 번역이 필요 없습니다.", 22, False, ON_ACC),
          ("여러 나라의 현장을 같은 AI의 눈으로, 같은 기준으로 재면 외국 자료도 본론이 됩니다.", 22, False, ON_ACC)],
         align=PP_ALIGN.CENTER)
    for i, (a, b) in enumerate([("측정", "AI가 한다"), ("해석", "두 문화의 사람이 한다")]):
        x = Inches(3.3) + Inches(3.6) * i
        box(s, x, Inches(4.7), Inches(3.2), Inches(1.4), fill=WHITE, lines=[(a, 28, True, ACC), (b, 17, False, INK)],
            anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    note(s, "그래서 발상을 바꿨습니다. 번역하지 말고, 보게 하자. 사진과 영상은 번역이 필요 없습니다. 여러 나라의 현장을 "
            "같은 AI의 눈으로, 같은 기준으로 재면 외국 자료도 한국 자료와 같은 차트 위의 본론이 됩니다. 측정은 AI가, "
            "그 차이의 이유를 해석하는 일은 두 문화의 사람이 맡습니다.")


def s_flow(prs, n):
    s = blank(prs)
    header(s, "해결 방안", "「한눈」은 이렇게 작동합니다")
    steps = [("① 조사", "나라별 팀원이 자국 현장 사진·영상 수집", "유학생은 모국어 검색어·현지 인맥 활용"),
             ("② AI 측정", "YOLO가 사람·의자·테이블·컵·오토바이를 찾아 셈", "탐지 결과를 생활 지표 6개로 환산"),
             ("③ 비교", "나라별 지표를 같은 차트에 나란히", "레이더 차트 · 탐지 박스 비교"),
             ("④ 해석", "차이가 큰 지표를 현지 출신 팀원이 설명", "해석이 곧 발표의 본론 주장")]
    cw = Inches(2.75)
    for i, (t, a, b) in enumerate(steps):
        x = M + (cw + Inches(0.42)) * i
        box(s, x, Inches(2.3), cw, Inches(3.0), fill=ACC_SOFT if i == 3 else BG,
            lines=[(t, 22, True, ACC), (a, 15, True, INK), (b, 13, False, SUB)])
        if i < 3:
            arrow(s, x + cw + Inches(0.05), Inches(3.6))
    box(s, M, Inches(5.7), W - 2 * M, Inches(0.9), fill=BG, lines=[
        ("팀 역할이 바뀝니다 — 한국 팀원: 한국 현장 · 외국인 팀원: 자국 현장 + 차이의 해석 · AI: 중립적 측정과 시각화", 15, True, INK)],
        anchor=MSO_ANCHOR.MIDDLE)
    foot(s, n)
    note(s, "작동은 네 단계입니다. 나라별 팀원이 자국 현장 자료를 모으면, AI가 사람과 사물을 찾아 세고 생활 지표로 바꿉니다. "
            "나라별 지표를 같은 차트에 나란히 놓고, 차이가 큰 지표는 그 나라 출신 팀원이 이유를 설명합니다. 이제 외국인 "
            "팀원은 무엇을 시킬지 애매한 사람이 아니라, 그 해석을 할 수 있는 유일한 사람이 됩니다.")


def s_ai(prs, n):
    s = blank(prs)
    header(s, "AI 설계", "AI가 사진을 보고, 찾고, 셉니다", "사람이 이해할 수 있는 지표로 바꾸는 규칙은 직접 설계")
    pic(s, os.path.join(OUT, "예시_VN_1.jpg"), M, Inches(2.1), w=Inches(6.2))
    rows = [("좌석", "의자·벤치·테이블이 보임"), ("착석", "사람 박스 아래쪽이 의자·테이블과 겹침"),
            ("무리", "사람 2명 이상이 가까이 있음"),
            ("오토바이·자전거", "입구·유리창 밖 이동 수단")]
    x = Inches(7.2)
    for i, (k, v) in enumerate(rows):
        y = Inches(2.1) + Inches(0.62) * i
        pill(s, x, y + Inches(0.06), Inches(1.9), Inches(0.42), k, ACC_SOFT, ACC, size=12)
        text(s, x + Inches(2.05), y + Inches(0.12), Inches(3.6), Inches(0.4), [(v, 14, False, INK)])
    text(s, x, Inches(5.95), Inches(5.6), Inches(0.8),
         [("모델: YOLO11s(COCO 80종 사전학습), 우리 컴퓨터에서 직접 구동", 12, False, SUB),
          ("장면 선별: CLIP으로 매장 장면만 남김(얼굴·음식 클로즈업·자막 화면 제외)", 12, False, SUB)])
    foot(s, n)
    note(s, "AI가 하는 일은 단순합니다. 사진을 보고 사람과 의자, 테이블, 컵, 오토바이를 찾아 셉니다. 다만 찾은 결과를 "
            "사람이 이해할 수 있는 지표로 바꾸는 규칙은 저희가 직접 설계했습니다. 예를 들어 사람 박스의 아래쪽이 의자와 "
            "겹치면 앉아 있다고 봅니다. 외부 서비스를 호출하는 것이 아니라, 모델을 직접 돌리고 기준을 직접 만들었습니다.")


def s_pilot(prs, n, S, stats):
    s = blank(prs)
    header(s, "파일럿 실험", "한국 · 일본 · 베트남 편의점, 같은 눈으로 재 보기")
    rows = [("대상", "세 나라 편의점 매장 둘러보기 유튜브 영상"),
            ("수집", "나라별 브랜드·도시 검색어로 검색 → 제목으로 촬영 국가 확인 → 사람이 한 번 더 확인"),
            ("규모", stats),
            ("장면 선별", "2초마다 1장 → 흔들림·중복 제거 → 매장 장면만(CLIP) → 영상당 최대 40장"),
            ("공정성", "영상별 비율을 먼저 구하고 평균 — 영상 하나가 결과를 끌고 가지 않게"),
            ("가설", "한국은 '사고 나가는 곳', 베트남은 '머무는 곳', 일본은 그 사이")]
    for i, (k, v) in enumerate(rows):
        y = Inches(2.05) + Inches(0.7) * i
        box(s, M, y, Inches(2.1), Inches(0.56), fill=ACC_SOFT if k == "가설" else BG,
            lines=[(k, 15, True, ACC)], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
        text(s, M + Inches(2.35), y + Inches(0.13), W - 2 * M - Inches(2.4), Inches(0.5), [(v, 15, k == "가설", INK)])
    foot(s, n, "유튜브 공개 영상(분석 목적으로만 사용, 영상 목록은 부록)")
    note(s, "실제로 해 봤습니다. 한국, 일본, 베트남 편의점을 둘러보는 유튜브 영상을 나라별로 모으고, 제목과 사람의 눈으로 "
            "촬영 국가를 확인했습니다. 2초마다 한 장씩 뽑아 흔들린 장면과 중복을 지우고, 매장 장면만 남긴 뒤 영상당 최대 40장만 "
            "썼습니다. 가설은 한국 편의점은 사고 나가는 곳, 베트남은 머무는 곳, 일본은 그 사이라는 것입니다.")


def s_verify(prs, n, excl, S):
    s = blank(prs)
    header(s, "검증", "AI가 모은 자료도, 사람이 확인합니다",
           "자동 수집 결과를 직접 열어 보고 부적합한 자료를 걸러냄 — 측정은 AI, 판단은 사람")
    box(s, M, Inches(2.2), Inches(5.6), Inches(1.9), fill=ACC_SOFT, lines=[
        ("1차 수집 전량 폐기", 19, True, ACC),
        ("일본어 'vlog' 검색 결과에 일본인이 찍은 한국 편의점 영상과 집 먹방이 섞임", 14, False, INK),
        ("→ 영상 종류를 '매장 둘러보기'로 통일, 촬영 국가 확인 규칙 추가", 14, False, SUB)])
    box(s, M, Inches(4.35), Inches(5.6), Inches(2.1), fill=ACC, lines=[
        ("가장 큰 발견", 15, True, ON_ACC),
        ("베트남 결과를 가장 크게 끌어올리던 영상은 AI가 만든 가짜 영상이었음", 17, True, WHITE),
        ("AI 생성·홍보 영상을 빼고 새 영상으로 보충: 베트남 '무리' 24.5% → {:.1f}%, '좌석' 10.7% → {:.1f}%".format(
            val(S, "VN", "무리"), val(S, "VN", "좌석")), 13, False, ON_ACC)])
    x = Inches(6.7)
    text(s, x, Inches(2.2), Inches(6), Inches(0.4), [("2차 수집에서 제외한 영상 {}편".format(len(excl)), 16, True, INK)])
    for i, r in enumerate(excl):
        y = Inches(2.75) + Inches(0.72) * i
        box(s, x, y, Inches(6.0), Inches(0.6), fill=BG, lines=[(r["제외 사유"], 14, True, INK)], anchor=MSO_ANCHOR.MIDDLE)
    foot(s, n)
    note(s, "여기서 중요한 과정이 하나 있었습니다. 처음 모은 일본 영상에는 일본인이 찍은 한국 편의점 영상이 섞여 있어 전부 "
            "버렸습니다. 두 번째 수집에서도 다른 나라 매장, 저화질 세로 영상, 그리고 AI로 만든 가짜 영상과 기업 홍보 영상을 "
            "사람이 직접 보고 걸러냈습니다. 특히 베트남 결과를 가장 크게 끌어올리던 영상이 AI가 만든 가짜였습니다. "
            "AI가 모은 자료도 사람이 확인해야 한다는 것, 이것 역시 한눈이 말하는 어울림입니다.")


def s_result_radar(prs, n, S):
    s = blank(prs)
    header(s, "결과 ①", "'머무는 장면'은 베트남에서 가장 자주 보였습니다",
           "좌석 베트남 {:.1f}% · 한국 {:.1f}% · 일본 {:.1f}%  /  앉은 사람 {:.1f}% · {:.1f}% · {:.1f}%".format(
               val(S, "VN", "좌석"), val(S, "KR", "좌석"), val(S, "JP", "좌석"),
               val(S, "VN", "착석"), val(S, "KR", "착석"), val(S, "JP", "착석")))
    pic(s, os.path.join(OUT, "그림_레이더.png"), M, Inches(2.0), h=Inches(5.0))
    x = Inches(6.9)
    for i, cc in enumerate(["KR", "JP", "VN"]):
        y = Inches(2.1) + Inches(1.35) * i
        lines = [(NAME[cc], 17, True, CCOL[cc]),
                 ("좌석 {:.1f}% · 착석 {:.1f}% · 무리 {:.1f}% · 오토바이·자전거 {:.1f}%".format(
                     val(S, cc, "좌석"), val(S, cc, "착석"), val(S, cc, "무리"), val(S, cc, "오토바이·자전거")), 14, False, INK)]
        box(s, x, y, Inches(5.8), Inches(1.15), fill=CSOFT[cc], lines=lines)
    box(s, x, Inches(6.2), Inches(5.8), Inches(0.62), fill=BG, lines=[
        ("일본은 가설과 달리 한국보다도 낮음 — 가설은 절반만 맞음", 13, True, SUB)], anchor=MSO_ANCHOR.MIDDLE)
    foot(s, n, "자체 분석(YOLO11s 탐지, 수치는 해당 요소가 보인 장면의 비율, 영상별 평균)")
    note(s, "결과입니다. 좌석, 앉은 사람, 무리, 오토바이 모두 베트남에서 가장 자주 보였습니다. 다만 일본은 가설과 달리 "
            "한국보다도 낮게 나왔습니다. 가설은 절반만 맞은 셈입니다.")


def s_result_bars(prs, n, S):
    s = blank(prs)
    header(s, "결과 ②", "다만, 그 차이는 베트남 영상 7편 중 2편에서 나왔습니다",
           "막대 = 나라 평균, 점 = 영상 하나 — 이 규모로는 '경향'까지만 말할 수 있음")
    pic(s, os.path.join(OUT, "그림_지표막대.png"), M, Inches(2.05), w=W - 2 * M)
    box(s, M, Inches(6.05), W - 2 * M, Inches(0.7), fill=ACC_SOFT, lines=[
        ("그래서 한눈은 결론이 아니라 [[질문]]을 줍니다 — \"베트남의 이 두 매장은 왜 달랐을까?\" 답은 현지 팀원의 몫", 15, True, INK)],
        anchor=MSO_ANCHOR.MIDDLE)
    foot(s, n, "자체 분석")
    note(s, "그런데 영상 하나하나를 점으로 찍어 보니, 베트남의 높은 값은 일곱 편 중 두 편에서 나왔습니다. 나머지 다섯 편은 "
            "한국, 일본과 비슷했습니다. 이 규모로는 나라의 차이라고 단정할 수 없고, 경향까지만 말할 수 있습니다. 대신 한눈은 "
            "질문을 줍니다. 이 두 매장은 왜 달랐을까. 그 답은 AI가 아니라 현지 출신 팀원이 할 수 있습니다.")


def s_qa(prs, n):
    s = blank(prs)
    header(s, "검수", "AI가 맞게 봤는지, 한 장씩 열어 채점했습니다",
           "무작위 50장의 박스 전부 + 좌석·착석·오토바이 장면은 전수 확인")
    rows = [("사람", "10 / 12", "83%", "포스터 속 인물·중복 박스가 오답"),
            ("좌석", "21 / 27", "78%", "베트남 13/13 · 한국 6/8 · 일본 2/6 → 오답 6장은 고쳐 반영"),
            ("앉은 사람", "6 / 6", "100%", "의자·스툴에 실제로 앉은 사람"),
            ("오토바이·자전거", "4 / 4", "100%", "매장 밖 실제 이동 수단"),
            ("음식·음료", "0 / 12", "0%", "진열 상품·포장 그림 오인 → 지표에서 제외")]
    for i, (k, a, p, memo) in enumerate(rows):
        y = Inches(2.05) + Inches(0.78) * i
        bad = p == "0%"
        box(s, M, y, Inches(2.3), Inches(0.64), fill=CSOFT["JP"] if bad else BG, lines=[(k, 15, True, INK)], pad=0.1,
            anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
        text(s, M + Inches(2.5), y + Inches(0.12), Inches(1.6), Inches(0.5), [(a, 18, True, INK)])
        text(s, M + Inches(4.1), y + Inches(0.08), Inches(1.4), Inches(0.5), [(p, 24, True, CCOL["JP"] if bad else ACC)])
        text(s, M + Inches(5.6), y + Inches(0.17), Inches(6.5), Inches(0.5), [(memo, 14, False, SUB)])
    box(s, M, Inches(6.05), W - 2 * M, Inches(0.7), fill=ACC_SOFT, lines=[
        ("보정 뒤 좌석: 베트남 {:.1f}% · 한국 {:.1f}% · 일본 {:.1f}% — 순위는 그대로, 차이는 오히려 조금 커짐".format(
            val(S_GLOBAL, "VN", "좌석"), val(S_GLOBAL, "KR", "좌석"), val(S_GLOBAL, "JP", "좌석")), 15, True, INK)],
        anchor=MSO_ANCHOR.MIDDLE)
    foot(s, n, "판정 63건 — 무작위 표본 박스 26개, 좌석 장면 27장, 착석 장면 6장, 오토바이·자전거 장면 4장")
    note(s, "AI가 제대로 봤는지 탐지 결과를 한 장씩 열어 채점했습니다. 사람은 열두 개 중 열 개, 좌석은 스물일곱 장 중 스물한 장을 맞혔습니다. "
            "베트남 좌석은 전부 맞았고, 일본은 장바구니나 진열대를 의자로 본 경우가 많았습니다. 틀린 여섯 장은 고쳐서 반영했고, "
            "그래도 순위는 같았습니다. 반대로 음식은 열두 개 모두 진열 상품을 잘못 본 것이라 지표에서 뺐습니다.")


def s_examples(prs, n):
    s = blank(prs)
    header(s, "결과 ③", "AI가 본 세 나라의 편의점")
    cw = (W - 2 * M - Inches(0.4)) / 3
    for i, cc in enumerate(["KR", "JP", "VN"]):
        x = M + (cw + Inches(0.2)) * i
        pill(s, x, Inches(1.75), Inches(1.1), Inches(0.38), NAME[cc], CCOL[cc], WHITE, size=13)
        pic(s, os.path.join(OUT, "예시_{}_1.jpg".format(cc)), x, Inches(2.3), w=cw)
        pic(s, os.path.join(OUT, "예시_{}_2.jpg".format(cc)), x, Inches(4.55), w=cw)
    foot(s, n, "유튜브 공개 영상 장면에 자체 탐지 결과 표시 · 예시 장면은 자동 점수 상위 12장 중 사람이 선택")
    note(s, "실제로 AI가 본 장면입니다. 파란 박스가 좌석, 주황 박스가 사람입니다. 한국과 일본에도 좌석이 있는 매장은 있습니다. "
            "차이는 좌석이 있느냐가 아니라, 좌석과 앉은 사람이 얼마나 자주 보이느냐입니다.")


def s_card(prs, n, S):
    s = blank(prs)
    header(s, "해석", "「AI 측정 × 현지인 해석」 카드 — 부록이 본론이 되는 장면")
    cols = [("📊 AI 측정", "앉은 사람이 보인 장면\n베트남 {:.1f}% · 한국 {:.1f}% · 일본 {:.1f}%\n(베트남 7편 중 2편에 집중)".format(
                val(S, "VN", "착석"), val(S, "KR", "착석"), val(S, "JP", "착석")), BG, INK),
            ("🗣 현지인 해석", "현지 출신 팀원이 채우는 칸\n예) \"좌석 있는 매장은 학생들이 공부하고 친구를 만나는 곳\"", CSOFT["VN"], INK),
            ("💡 우리 과제의 주장", "대학가 편의점을 '머무는 공간'으로 바꾸는 전략 — 근거: 현지 매장 사례 + 현지인 해석", ACC_SOFT, ACC)]
    cw = (W - 2 * M - Inches(0.9)) / 3
    for i, (t, b, fill, col) in enumerate(cols):
        x = M + (cw + Inches(0.45)) * i
        box(s, x, Inches(2.1), cw, Inches(3.0), fill=fill, lines=[(t, 20, True, col)] + [(ln, 15, False, INK) for ln in b.split("\n")])
        if i < 2:
            arrow(s, x + cw + Inches(0.06), Inches(3.4))
    box(s, M, Inches(5.5), W - 2 * M, Inches(1.0), fill=ACC, lines=[
        ("외국 자료가 '해외 사례' 한 장이 아니라, 결론을 이끄는 [[근거]]가 됩니다", 18, True, WHITE)],
        anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    foot(s, n, "현지인 해석 칸의 문장은 설명용 예시")
    note(s, "여기서 한눈의 핵심이 나옵니다. AI는 앉은 사람이 어디서 얼마나 보였는지만 말해 줍니다. 왜 그런지는 그 나라 출신 "
            "팀원이 해석합니다. 그리고 그 해석이 우리 과제의 주장이 됩니다. 외국 자료가 해외 사례 한 장이 아니라, 결론을 "
            "이끄는 근거가 되는 순간입니다.")


def s_proto(prs, n):
    s = blank(prs)
    header(s, "프로토타입", "직접 만들었습니다 — 5단계 웹 프로토타입", "사진·탐지 박스·지표는 파일럿 실제 결과, 팀원 이름과 해석 문장은 시연용 예시")
    ch = Inches(2.45)
    cw = ch * 16 / 9
    x0 = (W - 2 * cw - Inches(0.25)) / 2
    labels = ["② AI 측정", "③ 비교", "④ 해석 카드", "⑤ 발표로 보내기"]
    for k, i in enumerate((2, 3, 4, 5)):
        x = x0 + (cw + Inches(0.25)) * (k % 2)
        y = Inches(1.95) + (ch + Inches(0.15)) * (k // 2)
        pic(s, os.path.join(OUT, "프로토_{}.png".format(i)), x, y, w=cw)
        pill(s, x + Inches(0.12), y + Inches(0.12), Inches(1.6), Inches(0.34), labels[k], ACC, WHITE, size=11)
    foot(s, n, "시연 영상(약 50초) 별도 제출")
    note(s, "아이디어에서 끝나지 않고 프로토타입을 직접 만들었습니다. 같은 AI가 세 나라 사진을 측정하고, 같은 차트 위에서 비교하고, "
            "소수 영상에 값이 몰리면 현지 팀원에게 물어보라는 경고를 띄웁니다. 현지 팀원이 해석 카드를 쓰면, 그 카드가 발표의 "
            "본론 슬라이드로 들어갑니다. 자세한 흐름은 시연 영상으로 보여 드리겠습니다.")



def s_effect(prs, n):
    s = blank(prs)
    header(s, "기대효과", "측정은 AI가, 어울림은 사람이")
    cards = [("① 다양한 문화의 어울림", ["문화 차이가 번역하며 사라지는 잡음이 아니라", "측정하고 해석하는 인사이트가 됨"]),
             ("③ 중심과 주변의 어울림", ["부록이던 외국 자료가 본론의 근거가 되어", "한국 자료와 같은 위치에 놓임"]),
             ("팀플 구조의 변화", ["'뭘 시키지?' → '이 해석은 이 사람만 할 수 있다'", "언어 수준과 무관하게 같은 차트로 토론"])]
    cw = (W - 2 * M - Inches(0.6)) / 3
    for i, (t, bs) in enumerate(cards):
        x = M + (cw + Inches(0.3)) * i
        box(s, x, Inches(2.1), cw, Inches(2.6), fill=ACC_SOFT if i < 2 else BG,
            lines=[(t, 19, True, ACC)] + [(b, 15, False, INK) for b in bs])
    box(s, M, Inches(5.0), W - 2 * M, Inches(1.5), fill=BG, lines=[
        ("확장성", 15, True, ACC),
        ("편의점은 예시 — 카페 · 전통시장 · 캠퍼스 · 거리 간판 · 급식 등 문화를 비교하는 모든 과제에 같은 방식 적용", 15, False, INK)])
    foot(s, n)
    note(s, "기대효과입니다. 문화 차이는 번역하며 사라지는 잡음이 아니라 측정하고 해석하는 인사이트가 되고, 부록이던 외국 "
            "자료가 본론의 근거가 됩니다. 편의점은 예시일 뿐, 문화를 비교하는 모든 과제에 같은 방식을 쓸 수 있습니다.")


def s_limit(prs, n):
    s = blank(prs)
    header(s, "한계와 계획", "하루 만에 한 파일럿, 그래서 먼저 밝힙니다")
    lim = [("표본 편향", "유튜버가 고른 매장 · 한국은 현지인, 일본·베트남은 여행자 영상 위주"),
           ("탐지 오차", "좌석 정밀도 78%(일본 2/6) · 음식은 0%라 제외 · 흐린 장면 일부 포함"),
           ("규모", "나라당 영상 6~8편 — 베트남 결과는 2편에 좌우, '경향'까지만")]
    plan = [("1단계", "유학생 네트워크로 직접 촬영한 사진 확보 → 표본 편향 완화"),
            ("2단계", "자세 추정 모델로 앉음·서 있음 판별 정확도 개선"),
            ("3단계", "교내 다문화 팀플 수업(한일문화콘텐츠 전공 등)에서 시범 운영")]
    for i, (k, v) in enumerate(lim):
        box(s, M, Inches(2.1) + Inches(1.2) * i, Inches(5.7), Inches(1.0), fill=BG, lines=[(k, 16, True, INK), (v, 13, False, SUB)])
    for i, (k, v) in enumerate(plan):
        x = Inches(6.9)
        pill(s, x, Inches(2.25) + Inches(1.2) * i, Inches(1.1), Inches(0.42), k, ACC, WHITE, size=12)
        text(s, x + Inches(1.3), Inches(2.3) + Inches(1.2) * i, Inches(4.6), Inches(0.9), [(v, 15, False, INK)])
    foot(s, n)
    note(s, "한계도 먼저 말씀드리겠습니다. 유튜버가 고른 매장이라 표본이 치우쳐 있고, 앉아 있는지는 박스 겹침으로 추정했으며, "
            "나라당 영상이 많지 않은 파일럿입니다. 다음 단계로 유학생 네트워크를 통한 직접 촬영, 자세 추정 모델 도입, 교내 "
            "다문화 팀플 수업 시범 운영을 계획하고 있습니다.")


def s_end(prs, n):
    s = blank(prs)
    text(s, M, Inches(2.2), W - 2 * M, Inches(2.2),
         [("팀플의 '해외 사례' 한 장이 본론이 되는 순간,", 34, True, INK),
          ("같은 강의실의 두 섬은 [[하나의 팀]]이 됩니다.", 34, True, INK)], align=PP_ALIGN.CENTER)
    text(s, M, Inches(4.75), W - 2 * M, Inches(0.6), [("한눈 — 서로 다른 말을 쓰는 사람들이 같은 장면을 함께 보게 하는 AI", 18, False, SUB)],
         align=PP_ALIGN.CENTER)
    pill(s, (W - Inches(2.4)) / 2, Inches(5.9), Inches(2.4), Inches(0.62), "감사합니다", ACC, WHITE, size=18)
    note(s, "팀플의 해외 사례 한 장이 본론이 되는 순간, 같은 강의실의 두 섬은 하나의 팀이 됩니다. 감사합니다.")


def s_appendix(prs, n):
    s = blank(prs)
    header(s, "부록", "분석에 쓴 영상 목록 (매장 장면이 남은 영상)")
    p = os.path.join(HERE, "data", "영상목록.csv")
    rows = []
    if os.path.exists(p):
        with open(p, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    used = set()
    q = os.path.join(OUT, "지표_영상별.csv")
    if os.path.exists(q):
        with open(q, encoding="utf-8-sig") as f:
            used = {r["video"] for r in csv.DictReader(f)}
    rows = sorted((r for r in rows if r["id"] in used), key=lambda r: ["KR", "JP", "VN"].index(r["country"]))
    lines = [("[{}] {} — {}".format(NAME.get(r["country"], r["country"]), r["title"][:60], r["url"]), 10, False, INK) for r in rows]
    text(s, M, Inches(1.6), W - 2 * M, Inches(5.5), lines or [("영상 목록 준비 중", 12, False, MUTE)], spacing=0.15)
    foot(s, n)


S_GLOBAL = {}


def main():
    S = load_summary()
    S_GLOBAL.update(S)
    stats = "준비 중"
    if S:
        stats = " · ".join("{} {}편·{}장".format(NAME[c], S[c]["영상 수"], S[c]["장면 수"]) for c in ["KR", "JP", "VN"] if c in S) +             "  (영상 {}편, 분석 장면 {}장)".format(sum(int(S[c]["영상 수"]) for c in S), sum(int(S[c]["장면 수"]) for c in S))
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    s_cover(prs)
    excl = []
    p = os.path.join(HERE, "data", "제외영상.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8-sig") as f:
            excl = list(csv.DictReader(f))
    fns = [s_team, s_hook, s_status, s_problem, s_idea, s_flow, s_ai,
           lambda p, n: s_pilot(p, n, S, stats), lambda p, n: s_verify(p, n, excl, S), lambda p, n: s_result_radar(p, n, S),
           lambda p, n: s_result_bars(p, n, S), s_qa, s_examples, lambda p, n: s_card(p, n, S), s_proto,
           s_effect, s_limit, s_end, s_appendix]
    for i, fn in enumerate(fns):
        fn(prs, i + 2)
    prs.save(PPTX)
    print("[저장]", PPTX, len(prs.slides), "장")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
