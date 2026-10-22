# -*- coding: utf-8 -*-
"""
06. 기획서(hwpx)를 만든다 — 해썹 공모전 기획서(42_기획서_HWPX.py)와 같은 서식·구성

- 서식: 해썹 공모전 양식 hwpx의 글자·문단 모양과 머리 표(아이디어명·팀명·활용 데이터·핵심 요약)를 빌려 쓴다.
  첫 번째(분석 부문) 부분만 쓰고, 제목과 일부 머리말을 이 공모전에 맞게 바꾼다.
- 실험 수치는 output/지표_요약.csv, 그림은 output/그림_*.png에서 읽는다.

산출: output/한눈_기획서.hwpx
"""

import datetime
import html
import os
import random
import re
import struct
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
# 서식은 해썹 공모전 기획서와 같게 하려고 그때 쓴 양식 hwpx의 글자·문단 모양을 그대로 빌려 쓴다(원본은 건드리지 않음)
FORM = os.path.join(HERE, "..", "2026년 한국식품안전관리인증원 공공데이터 분석·활용 경진대회", "아이디어 기획서 양식.hwpx")
FIG = os.path.join(HERE, "output")
# 사용자가 한글에서 고친 output/한눈_기획서.hwpx를 덮어쓰지 않도록 다른 이름으로 만든다(수정본 보정은 10_기획서_수정반영.py)
OUT = os.path.join(HERE, "output", "한눈_기획서_자동생성.hwpx")

# 양식에 있는 모양 번호
C_BODY, C_GRAY, C_BOLD, C_SUB, C_SMALL = "16", "17", "18", "19", "2"
P_BODY, P_FIRST, P_LEFT, P_CENTER = "19", "26", "30", "29"
P_BULLET, P_HEAD = "10", "12"   # 내어쓰기 글머리표 / 위 여백 있는 작은 제목
TEXT_W = 47366          # 양식 표 너비(HWPUNIT). 본문 폭 안쪽
random.seed(7)

# ─────────────────────────────────────────────────────────────
# XML 조각 만들기
# ─────────────────────────────────────────────────────────────
def esc(t):
    return html.escape(t, quote=False)


_fn = [0]
C_NOTE, S_NOTE = "3", "14"      # 양식의 9pt 글자 모양 / '각주' 스타일


def FOOT(t):
    """한글 각주 컨트롤(해썹 기획서 v11과 같은 구조). 번호는 한글이 다시 매긴다."""
    _fn[0] += 1
    n = _fn[0]
    fmt = '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
    return ('<hp:ctrl><hp:footNote number="{n}" suffixChar="41" instId="{iid}">'
            '<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="TOP" linkListIDRef="0" '
            'linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
            '<hp:p id="0" paraPrIDRef="{pp}" styleIDRef="{st}" pageBreak="0" columnBreak="0" merged="0">'
            '<hp:run charPrIDRef="{c}"><hp:ctrl><hp:autoNum num="{n}" numType="FOOTNOTE">{fmt}</hp:autoNum></hp:ctrl>'
            '<hp:t> {t}</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl>'
            ).format(n=n, iid=1300000000 + n, pp=P_BULLET, st=S_NOTE, c=C_NOTE, fmt=fmt, t=esc(t))


def _with_notes(t):
    """글 안의 ^[각주 내용]을 각주 컨트롤로 바꾼다."""
    out, i = [], 0
    while True:
        k = t.find("^[", i)
        if k < 0:
            break
        if k > i:
            out.append("<hp:t>{}</hp:t>".format(esc(t[i:k])))
        depth, j = 1, k + 2          # 각주 안의 [단독] 같은 괄호를 건너뛰도록 짝을 센다
        while depth:
            depth += {"[": 1, "]": -1}.get(t[j], 0)
            j += 1
        out.append(FOOT(t[k + 2:j - 1]))
        i = j
    if i < len(t):
        out.append("<hp:t>{}</hp:t>".format(esc(t[i:])))
    return "".join(out) or "<hp:t/>"


def P(runs, pp=P_BODY):
    """runs: 글자 하나면 본문, [(글, 글자모양), ...]이면 여러 모양."""
    if isinstance(runs, str):
        runs = [(runs, C_BODY)]
    body = "".join('<hp:run charPrIDRef="{}">{}</hp:run>'.format(c, _with_notes(t)) for t, c in runs)
    return '<hp:p id="0" paraPrIDRef="{}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">{}</hp:p>'.format(pp, body)


def H(t):
    """본문 안 작은 제목(굵게)."""
    return P([("■ " + t, C_BOLD)], pp=P_HEAD)


def B(t, bold=None):
    """글머리표 문단. bold가 있으면 앞부분을 굵게."""
    if bold:
        return P([("• ", C_BODY), (bold, C_BOLD), (" " + t, C_BODY)], pp=P_BULLET)
    return P([("• " + t, C_BODY)], pp=P_BULLET)


def N(t):
    """① ② 형태의 하위 항목 제목."""
    return P([("   " + t, C_BOLD)], pp=P_BULLET)


def D(t, bold=None):
    """하위 항목의 세부 줄."""
    if bold:
        return P([("   - ", C_BODY), (bold, C_BOLD), (" " + t, C_BODY)], pp=P_BULLET)
    return P([("   - " + t, C_BODY)], pp=P_BULLET)


def CAP(t):
    return P([(t, C_GRAY)], pp=P_CENTER)


def BLANK():
    return P([("", C_BODY)])


def _cell(text, col, row, width, head, span=1):
    bf = "6" if head else "5"
    pp = P_CENTER if head else P_LEFT
    ch = C_BOLD if head else C_BODY
    paras = "".join(
        '<hp:p id="2147483648" paraPrIDRef="{}" styleIDRef="28" pageBreak="0" columnBreak="0" merged="0">'
        '<hp:run charPrIDRef="{}"><hp:t>{}</hp:t></hp:run></hp:p>'.format(pp, ch, esc(line))
        for line in str(text).split("\n"))
    return ('<hp:tc name="" header="{h}" hasMargin="1" protect="0" editable="0" dirty="0" borderFillIDRef="{bf}">'
            '<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" '
            'linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{p}</hp:subList>'
            '<hp:cellAddr colAddr="{c}" rowAddr="{r}"/><hp:cellSpan colSpan="{s}" rowSpan="1"/>'
            '<hp:cellSz width="{w}" height="282"/><hp:cellMargin left="340" right="340" top="200" bottom="200"/></hp:tc>'
            ).format(h=1 if head else 0, bf=bf, p=paras, c=col, r=row, s=span, w=width)


_z = [30]


def T(rows, ratio):
    """rows[0]은 머리글. ratio는 열 너비 비율."""
    tot = sum(ratio)
    widths = [int(TEXT_W * r / tot) for r in ratio]
    widths[-1] = TEXT_W - sum(widths[:-1])
    trs = []
    for ri, row in enumerate(rows):
        tds = "".join(_cell(v, ci, ri, widths[ci], ri == 0) for ci, v in enumerate(row))
        trs.append("<hp:tr>" + tds + "</hp:tr>")
    _z[0] += 1
    tbl = ('<hp:tbl id="{id}" zOrder="{z}" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" '
           'dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="{rc}" colCnt="{cc}" cellSpacing="0" borderFillIDRef="5" noAdjust="0">'
           '<hp:sz width="{w}" widthRelTo="ABSOLUTE" height="{hgt}" heightRelTo="ABSOLUTE" protect="0"/>'
           '<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" '
           'horzRelTo="COLUMN" vertAlign="TOP" horzAlign="CENTER" vertOffset="0" horzOffset="0"/>'
           '<hp:outMargin left="141" right="141" top="141" bottom="141"/><hp:inMargin left="340" right="340" top="200" bottom="200"/>'
           '{trs}</hp:tbl>').format(id=random.randint(10 ** 9, 2 * 10 ** 9), z=_z[0], rc=len(rows), cc=len(rows[0]),
                                   w=TEXT_W, hgt=1800 * len(rows), trs="".join(trs))
    return ('<hp:p id="0" paraPrIDRef="{}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            '<hp:run charPrIDRef="{}">{}<hp:t/></hp:run></hp:p>').format(P_LEFT, C_BODY, tbl)


_images = []


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def IMG(fname, width_mm=165):
    path = os.path.join(FIG, fname)
    wpx, hpx = png_size(path)
    idx = len(_images) + 1
    _images.append(("image{}".format(idx), path))
    org_w, org_h = wpx * 75, hpx * 75
    cur_w = int(width_mm * 283.465)
    cur_w = min(cur_w, TEXT_W)
    cur_h = int(cur_w * hpx / wpx)
    sx, sy = cur_w / org_w, cur_h / org_h
    _z[0] += 1
    pic = ('<hp:pic id="{id}" zOrder="{z}" numberingType="PICTURE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" '
           'dropcapstyle="None" href="" groupLevel="0" instid="{iid}" reverse="0">'
           '<hp:offset x="0" y="0"/><hp:orgSz width="{ow}" height="{oh}"/><hp:curSz width="{cw}" height="{chh}"/>'
           '<hp:flip horizontal="0" vertical="0"/><hp:rotationInfo angle="0" centerX="{cx}" centerY="{cy}" rotateimage="1"/>'
           '<hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
           '<hc:scaMatrix e1="{sx:.6f}" e2="0" e3="0" e4="0" e5="{sy:.6f}" e6="0"/>'
           '<hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo>'
           '<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="{ow}" y="0"/><hc:pt2 x="{ow}" y="{oh}"/><hc:pt3 x="0" y="{oh}"/></hp:imgRect>'
           '<hp:imgClip left="0" right="{ow}" top="0" bottom="{oh}"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>'
           '<hp:imgDim dimwidth="{ow}" dimheight="{oh}"/>'
           '<hc:img binaryItemIDRef="{bid}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/><hp:effects/>'
           '<hp:sz width="{cw}" widthRelTo="ABSOLUTE" height="{chh}" heightRelTo="ABSOLUTE" protect="0"/>'
           '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" '
           'horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           '<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:shapeComment>{name}</hp:shapeComment></hp:pic>'
           ).format(id=random.randint(10 ** 9, 2 * 10 ** 9), z=_z[0], iid=random.randint(10 ** 8, 10 ** 9),
                    ow=org_w, oh=org_h, cw=cur_w, chh=cur_h, cx=cur_w // 2, cy=cur_h // 2, sx=sx, sy=sy,
                    bid="image{}".format(idx), name=esc(fname))
    return ('<hp:p id="0" paraPrIDRef="{}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            '<hp:run charPrIDRef="{}">{}<hp:t/></hp:run></hp:p>').format(P_CENTER, C_BODY, pic)


# ─────────────────────────────────────────────────────────────
# 실험 수치 읽기 (04_지표_시각화.py 산출물)
# ─────────────────────────────────────────────────────────────
import csv

NAME = {"KR": "한국", "JP": "일본", "VN": "베트남"}
IND = ["좌석", "착석", "무리", "오토바이·자전거"]


def _csv(p):
    p = os.path.join(HERE, p)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


SUMM = {r["country"]: r for r in _csv("output/지표_요약.csv")}
VIDS = _csv("data/영상목록.csv")
EXCL = _csv("data/제외영상.csv")


def v(cc, k):
    try:
        return float(SUMM[cc][k])
    except (KeyError, ValueError):
        return 0.0


def rank(k):
    order = sorted(["KR", "JP", "VN"], key=lambda c: -v(c, k))
    return " > ".join("{} {:.1f}%".format(NAME[c], v(c, k)) for c in order)


N_VID = {c: int(SUMM[c]["영상 수"]) if c in SUMM else 0 for c in NAME}
N_SCN = {c: int(SUMM[c]["장면 수"]) if c in SUMM else 0 for c in NAME}
N_VID_ALL, N_SCN_ALL = sum(N_VID.values()), sum(N_SCN.values())

IDEA = "「한눈」: 번역 없이 문화를 비교하는 AI 비전 팀플 도구 — 외국인 팀원의 조사가 '부록'이 아닌 '본론'이 되도록"
SUMMARY = ("외국인 유학생이 포함된 팀플에서 유학생의 모국어 조사가 번역을 거치며 '해외 사례' 부록으로 밀려나는 문제를, "
           "번역이 필요 없는 현장 이미지로 해결하는 도구. 나라별 팀원이 모은 사진·영상을 객체 탐지 AI(YOLO)가 같은 기준으로 "
           "측정해 생활 지표로 바꾸고, 차이의 원인은 현지 출신 팀원이 해석해 발표의 본론 근거로 삼음. "
           "한국·일본·베트남 편의점 영상 {}편, 장면 {}장으로 파일럿 검증하고, 조사→측정→비교→해석→발표 흐름의 "
           "웹 프로토타입과 시연 영상 제작".format(N_VID_ALL, N_SCN_ALL))
TEAM = ["(팀명)", "김성빈"]   # 팀명, 주기획자
DATA_LINES = [
    "• 자체수집: 한국·일본·베트남 편의점 매장 둘러보기 유튜브 공개 영상 {}편 → 분석 장면 {}장".format(N_VID_ALL, N_SCN_ALL),
    "• 사전학습 모델: YOLO11s(COCO 80종 객체 탐지), CLIP ViT-B/32(장면 분류)",
    "• 기타: 외국인 유학생 어학 기준·팀플 관련 언론 보도(2026 국회 교육위원회 자료 인용 기사 등)",
]


# ─────────────────────────────────────────────────────────────
# 본문 내용 (양식 머리말 순서대로)
# ─────────────────────────────────────────────────────────────
def sec_1_1():
    x = []
    x.append(H("같은 강의실, 두 개의 섬"))
    x.append(B("전국 4년제 대학 207곳 학위과정 외국인 유학생 94,025명 중 교육부 권고 어학 기준(TOPIK 3급 또는 TOEFL iBT 59점 "
               "이상)을 충족한 학생은 46,913명(49.9%)^[한국경제(2026.1.27.), \"[단독] 조별과제 걸리면 지옥…한국말 못 하는 유학생이 '절반'\". 2026년 국회 교육위원회 자료 인용]", "어학 기준:"))
    x.append(B("대학이 기준 미달자를 선발해도 별도 불이익 없음^[같은 기사]", "선발 구조:"))
    x.append(B("\"팀 프로젝트에서 중국인 유학생과 같은 조가 됐는데 소통이 잘 되지 않아 어려움이 컸다\", \"다음 학기에는 유학생이 "
               "없는 수업을 골라 수강할 예정\"(한국 학생 인터뷰)^[한국경제(2026.1.27.), \"외국인 유학생 절반, 어학능력 미달…소통 안돼 "
               "팀플 망쳐\"]", "팀플 기피:"))
    x.append(B("'한국 유학 왔는데 한국인 친구 없어요'라는 제목의 보도에서, 유학생과의 과제를 꺼리는 한국 학생 인터뷰를 보고 "
               "한국 학생에게 다가가기 어려워졌다는 유학생 사례 소개^[오마이뉴스(2020.12.1.), \"'한국 유학 왔는데 한국인 친구 없어요'... "
               "겉도는 외국인 유학생\". 2020년 보도로, 같은 문제가 수년째 이어지고 있음을 보여 줌]", "고립:"))
    x.append(H("팀플에서 반복되는 장면: 외국인 팀원의 조사는 '부록'이 됨"))
    x.append(B("한국어 소통이 어려운 팀원에게 맡길 역할이 불분명. 자료 조사·PPT 꾸미기 등 주변 업무로 배정되기 쉬움", "역할 분배:"))
    x.append(B("유학생이 모국어로 찾은 자료는 번역을 거쳐도 한국 자료와 비교 기준이 달라 본론에 섞이지 않음", "자료 활용:"))
    x.append(B("최종 발표에서 유학생의 조사는 '해외 사례' 한 장으로 분리. 팀원 4명 중 1명의 조사가 슬라이드 1장이 되는 구조"
               "^[4인 팀을 가정한 예시. 통계가 아니라 제안자가 겪은 팀플 구조를 표현한 것]",
               "결과:"))
    x.append(B("한국 자료는 중심, 외국 자료는 주변이라는 위계가 팀플 결과물 안에서 그대로 반복됨", "문제 정의:"))
    x.append(CAP("[표 1] 외국 자료가 부록이 되는 원인"))
    x.append(T([["원인", "내용", "결과"],
                ["번역의 거리감", "글 자료는 반드시 번역을 거쳐야 하며, 번역된 자료는 '남의 나라 이야기'로 읽힘", "본론과 분리"],
                ["비교 기준 불일치", "한국 팀원은 매출·점포 수, 유학생은 현지 후기·기사 등 서로 다른 기준으로 조사", "나란히 비교 불가"],
                ["사후 병합", "각자 조사한 뒤 발표 직전에 이어 붙임", "두 자료를 잇는 논리 부재"]],
               [1.3, 4.2, 1.5]))
    x.append(H("기존 해결책의 한계"))
    x.append(CAP("[표 2] 기존 방식과 한계"))
    x.append(T([["기존 방식", "접근", "한계"],
                ["한국어 교육", "유학생의 한국어 실력 향상", "문제를 유학생 개인의 결핍으로 봄. 효과까지 시간이 걸림"],
                ["번역기·요약 AI", "외국어 자료를 한국어로 옮김", "말은 옮기지만 비교 기준은 맞추지 못함"],
                ["버디 프로그램", "한국 학생과 유학생을 짝지음", "수업 밖 활동으로, 팀플 결과물의 구조는 그대로"]],
               [1.4, 2.4, 3.6]))
    x.append(B("세 방식 모두 유학생을 '채워야 할 부족함'으로 전제. 본 제안은 언어 차이를 비용이 아닌 팀의 자원으로 전환하는 데 초점",
               "시사점:"))
    return x


def sec_1_2():
    x = []
    x.append(H("번역하지 말고, 보게 하자 — 번역이 필요 없는 자료, 이미지"))
    x.append(B("글은 번역을 거쳐야 비교할 수 있으나, 현장 사진·영상은 어느 나라 것이든 같은 기준으로 바로 잴 수 있음", "글과 이미지:"))
    x.append(B("수백 장의 장면에서 사람·의자·테이블을 같은 기준으로 세는 일은 사람이 하면 기준이 흔들리고 시간이 많이 듦. "
               "객체 탐지 AI는 같은 기준을 끝까지 유지^[객체 탐지: 사진 속 사물의 종류와 위치를 사각형(박스)으로 찾아내는 인공지능 기술]", "AI가 필요한 이유:"))
    x.append(B("AI는 '무엇이 얼마나 보이는가'(측정)를, 사람은 '왜 그런가'(해석)를 맡음. 해석은 그 나라 출신 팀원만 할 수 있는 역할",
               "역할 분리:"))
    x.append(B("외국 자료가 번역문이 아니라 한국 자료와 같은 차트 위의 숫자가 되므로, 부록이 아닌 본론의 근거로 쓰일 수 있음",
               "기대 변화:"))
    x.append(CAP("[표 3] 글 자료 중심 조사와 이미지 측정 방식 비교"))
    x.append(T([["구분", "글 자료 중심(현행)", "이미지 측정(제안)"],
                ["외국 자료의 형태", "번역문", "한국 자료와 같은 지표의 숫자"],
                ["비교 기준", "팀원마다 다름", "AI가 같은 규칙으로 측정"],
                ["외국인 팀원의 역할", "자료 수집·번역", "자국 현장 수집 + 차이의 해석"],
                ["발표 속 위치", "'해외 사례' 한 장", "본론 슬라이드마다 나라별 비교"]],
               [1.5, 2.6, 3.0]))
    return x


def sec_2_1():
    x = []
    x.append(P([("서비스명: 한눈 — 다문화 팀플을 위한 현장 비교 도구", C_BOLD)], pp=P_HEAD))
    x.append(B("나라별 팀원이 모은 현장 이미지를 AI가 같은 기준으로 측정·시각화하고, 차이의 원인은 현지 출신 팀원이 해석해 "
               "발표의 본론 주장으로 연결하는 도구", "핵심 개념:"))
    x.append(B("외국인 유학생이 포함된 문화 비교형 팀플(교양·전공 수업). 초기 대상은 한일문화콘텐츠 전공처럼 국가 비교 과제가 "
               "많은 수업", "주 사용자:"))
    x.append(B("비교 대상 설정 → 나라별 현장 이미지 수집 → AI 측정 → 같은 차트로 비교 → 「AI 측정 × 현지인 해석」 카드 작성 → "
               "발표 본론에 반영", "이용 흐름:"))
    x.append(CAP("[표 4] 팀 역할의 재설계"))
    x.append(T([["주체", "맡는 일", "바뀌는 점"],
                ["한국 팀원", "한국 현장 이미지 수집, 한국 측 해석", "외국 자료를 번역문이 아닌 숫자로 받음"],
                ["외국인 팀원", "모국어 검색어·현지 인맥으로 자국 현장 수집, 차이의 원인 해석",
                 "'뭘 시킬지 애매한 팀원'에서 '그 해석을 할 수 있는 유일한 팀원'으로"],
                ["AI", "사람·사물 탐지, 생활 지표 환산, 비교 시각화", "같은 기준을 끝까지 유지하는 중립적 측정자"]],
               [1.2, 3.0, 3.2]))
    x.append(H("측정 지표 — 탐지 결과를 사람이 이해하는 말로"))
    x.append(CAP("[표 5] 생활 지표와 판정 규칙"))
    x.append(T([["지표", "판정 규칙(장면 단위)", "의미"],
                ["좌석", "의자·벤치·소파·테이블이 하나 이상 보임", "머무를 수 있는 공간인가"],
                ["착석", "사람 박스의 아래쪽 절반이 의자·테이블 박스와 20% 이상 겹침", "실제로 머무는가"],
                ["무리", "사람 2명 이상이 가까이 있음(중심 거리 < 평균 박스 너비 × 1.5)", "혼자 오는가, 함께 오는가"],
                ["오토바이·자전거", "오토바이·자전거(입구·유리창 밖 포함)", "어떤 생활권의 가게인가"]],
               [1.3, 3.9, 2.0]))
    x.append(H("차별성"))
    x.append(B("번역기·요약 AI가 '말'을 옮긴다면, 본 제안은 언어를 거치지 않고 '장면'을 같은 기준으로 측정", "언어 비의존:"))
    x.append(B("외부 서비스 호출이 아니라 탐지 모델을 직접 구동하고, 탐지 결과를 생활 지표로 바꾸는 규칙과 수집·검수 기준을 "
               "직접 설계", "자체 설계:"))
    x.append(B("AI는 차이의 크기만 제시하고 이유는 판단하지 않음. 해석은 사람, 특히 현지 출신 팀원의 몫으로 남겨 AI가 "
               "문화를 단정하지 않도록 함", "해석의 몫:"))
    x.append(H("프로토타입과 대표 화면"))
    x.append(B("조사 → AI 측정 → 비교 → 해석 카드 → 발표로 보내기의 5단계 웹 화면 제작 완료. 사진·탐지 박스·지표는 파일럿 실제 "
               "결과를 사용하고, 팀원 이름과 해석 문장은 시연용 예시^[한 파일짜리 웹앱(output/한눈_프로토타입.html). 주소 뒤에 ?demo=1을 "
               "붙이면 자막과 함께 자동 시연되며, 이를 녹화한 것이 제출 영상(한눈_시연영상.mp4)]", "구현 상태:"))
    x.append(B("③ 비교 화면에서 영상별 값을 점으로 함께 보여 주고, 소수 영상에 값이 몰리면 '현지 팀원에게 물어보세요' 경고를 띄워 "
               "해석 카드로 이어지게 함", "핵심 장면:"))
    x.append(IMG("그림_프로토타입.png", width_mm=165))
    x.append(CAP("[그림 2] 대표 화면: ② AI 측정 → ③ 비교 → ④ 해석 카드 → ⑤ 발표로 보내기 (시연용 예시 포함)"))
    x.append(IMG("그림_탐지예시.png", width_mm=150))
    x.append(CAP("[그림 1] AI가 본 세 나라의 편의점 — 파랑: 좌석, 주황: 사람, 초록: 음식·음료, 보라: 오토바이·자전거"))
    return x


def sec_2_2():
    x = []
    x.append(B("세 나라 편의점 매장 둘러보기 영상을 수집해 파일럿 분석에 사용. 영상은 분석 목적으로만 쓰고 원본은 재배포하지 않으며, "
               "목록과 주소는 참고 자료에 명시", "구분 기준:"))
    x.append(CAP("[표 6] 파일럿 분석 데이터"))
    rows = [["구분", "한국", "일본", "베트남"],
            ["영상 수(편)", str(N_VID["KR"]), str(N_VID["JP"]), str(N_VID["VN"])],
            ["분석 장면 수(장)", str(N_SCN["KR"]), str(N_SCN["JP"]), str(N_SCN["VN"])],
            ["주요 브랜드", "GS25·CU·세븐일레븐 등", "로손 중심", "서클K·GS25·세븐일레븐"],
            ["촬영자", "현지인 위주", "여행자 위주", "여행자 위주"]]
    x.append(T(rows, [1.6, 1.8, 1.8, 1.8]))
    x.append(H("수집 기준과 정제"))
    x.append(B("나라별 대표 브랜드 + 도시 + '둘러보기/tour' 검색어로 유튜브 검색(현지어·영어 병행)^[2026.9.27. 검색·수집. "
               "영상 목록과 주소는 data/영상목록.csv, 제외 사유는 data/제외영상.csv]", "검색:"))
    x.append(B("제목에 그 나라 지명·브랜드가 있고 다른 나라 이름이 없는 영상만 사용. 2~25분 길이", "촬영 국가 확인:"))
    x.append(B("1차 수집(현지어 'vlog' 검색)에서 일본 검색 결과에 일본인이 촬영한 한국 편의점 영상과 집 먹방이 섞여 전량 폐기. "
               "2차 수집에서 영상 종류를 '매장 둘러보기'로 통일하고 촬영 국가 확인 규칙 추가^[1차 수집 자료(한국 10편·일본 8편)는 "
               "_보관_1차수집 폴더에 보관]", "1차 수집 폐기:"))
    if EXCL:
        x.append(B("제목 필터를 통과했으나 사람이 직접 열어 보고 부적합한 영상 {}편 제외({})".format(
            len(EXCL), ", ".join(r["제외 사유"] for r in EXCL)), "사람 확인:"))
        x.append(B("베트남 결과를 가장 크게 끌어올리던 영상이 AI로 만든 가짜 영상이었음. 제외·보충 전후 베트남 '무리' 24.5% → "
                   "{:.1f}%, '좌석' 10.7% → {:.1f}%. 자동 수집 자료도 사람이 확인해야 한다는 점을 한눈의 절차(수집 → 사람 확인 → "
                   "측정)에 반영^[영상 id ebjX33pTvUs. 장면을 직접 열어 보니 같은 인물이 여러 가게에 등장하는 합성 이미지였고 실제 매장 "
                   "촬영이 아니었음]".format(v("VN", "무리"), v("VN", "좌석")), "가장 큰 발견:"))
    x.append(B("매장 장면이 남지 않은 영상(세로형 저화질, 매장 밖 위주)은 분석에서 자연히 빠져 최종 분석 영상은 한국 {}편, "
               "일본 {}편, 베트남 {}편".format(N_VID["KR"], N_VID["JP"], N_VID["VN"]), "최종 분석:"))
    return x


def sec_2_3():
    x = []
    x.append(H("(1) 전처리 — 프레임 추출과 정제"))
    x.append(B("2초마다 1장 추출, 영상 앞뒤 5%(인트로·아웃트로) 제외", "추출:"))
    x.append(B("라플라시안 분산(선명도 점수)^[이미지 경계선이 얼마나 뚜렷한지를 나타내는 값. 흔들린 장면일수록 작음] 60 미만 프레임 제거. "
               "세로형 저화질 영상(시험 영상 중앙값 9.6)은 걸러지고 정상 영상(하위 5% 158)은 남도록 기준 설정", "흔들림 제거:"))
    x.append(B("직전에 남긴 장면과 32×32 흑백 축소본의 평균 차이가 6 미만이면 제거", "중복 제거:"))
    x.append(H("(2) 장면 선별 — CLIP으로 매장 장면만"))
    x.append(B("장면 설명 문장 10개^[CLIP: 사진과 문장의 뜻이 얼마나 가까운지 재는 공개 인공지능 모델(Radford 외, 2021). openai/clip-vit-base-patch32 사용](매장 안·매장 좌석·매장 입구 + 얼굴 클로즈업·음식 클로즈업·자막 화면·집 안·도로·차 안·창고) 중 "
               "가장 가까운 것을 고르고, 매장 관련 3종이면서 확률 0.35 이상인 장면만 사용", "방법:"))
    x.append(B("영상 하나가 결과를 좌우하지 않도록 영상당 최대 40장을 무작위로 사용", "균형:"))
    x.append(H("(3) 객체 탐지와 지표 환산"))
    x.append(B("YOLO11s^[Ultralytics YOLO11s. 사람·의자·컵 등 80종 사물 사진(COCO 데이터셋)으로 미리 학습된 공개 모델]"
               "(COCO 80종 사전학습), 신뢰도 0.35 이상 박스 사용. 외부 서비스 호출 없이 CPU에서 직접 구동", "탐지:"))
    x.append(B("2-1의 '생활 지표와 판정 규칙' 표에 따라 장면마다 다섯 지표의 해당 여부(0/1) 판정. '공부'(노트북·책)는 매대의 잡지·책까지 잡혀 "
               "지표에서 제외^[탐지된 '책' 15건을 직접 확인한 결과 잡지 매대·과자 포장이 대부분이었음]. '테이블 위 음식'도 검수 정밀도 0%로 "
               "제외((6) 참고). 좌석 오답 6장은 사람 검수대로 고쳐 반영", "환산:"))
    x.append(B("영상별로 해당 장면 비율을 먼저 구하고, 그 평균을 나라 값으로 사용^[예: 한 영상의 장면 40장 중 5장에 좌석이 보이면 그 영상의 "
               "좌석 값은 12.5%. 나라 값은 그 나라 영상 값들의 평균]. 영상별 값을 함께 제시", "집계:"))
    x.append(H("(4) 파일럿 결과"))
    x.append(B("다섯 지표의 나라별 값은 아래 표와 같음^[산출 파일 output/지표_요약.csv·지표_영상별.csv, 코드 04_지표_시각화.py]", "결과:"))
    x.append(CAP("[표 7] 나라별 생활 지표 (해당 요소가 보인 장면의 비율, 영상별 평균)"))
    rows = [["지표", "한국", "일본", "베트남"]]
    for k in IND:
        rows.append([k] + ["{:.1f}%".format(v(c, k)) for c in ["KR", "JP", "VN"]])
    x.append(T(rows, [1.8, 1.6, 1.6, 1.6]))
    for k in ["좌석", "착석", "무리", "오토바이·자전거"]:
        x.append(B(rank(k), k + ":"))
    x.append(IMG("그림_레이더.png", width_mm=95))
    x.append(CAP("[그림 2] 나라별 장면 지문(레이더 차트)"))
    x.append(IMG("그림_지표막대.png", width_mm=165))
    x.append(CAP("[그림 3] 지표별 나라 평균(막대)과 영상별 값(점)"))
    x.extend(RESULT_NOTES)
    x.append(H("(5) 「AI 측정 × 현지인 해석」 카드"))
    x.append(CAP("[표 8] 해석 카드 예시 — 현지인 해석 칸은 실제 팀플에서 해당 나라 출신 팀원이 작성"))
    x.append(T([["AI 측정", "현지인 해석(작성 예시)", "우리 과제의 주장"],
                ["앉은 사람이 보인 장면: 베트남 {:.1f}%, 한국 {:.1f}%, 일본 {:.1f}% (베트남 7편 중 2편에 집중)".format(v("VN", "착석"), v("KR", "착석"), v("JP", "착석")),
                 "\"좌석 있는 매장은 학생들이 공부하고 친구를 만나는 곳\"", "대학가 편의점을 '머무는 공간'으로 바꾸는 전략"],
                ["오토바이·자전거가 보인 장면: 베트남 {:.1f}%, 한국 {:.1f}%".format(v("VN", "오토바이·자전거"), v("KR", "오토바이·자전거")),
                 "\"오토바이로 잠깐 들러 쉬었다 가는 곳\"", "이동 중 들르는 거점형 매장 설계"]],
               [2.4, 2.6, 2.2]))
    x.append(B("현지인 해석 칸의 문장은 설명을 위한 가상의 예시이며, 실제 사용 시 해당 나라 출신 팀원이 작성. AI는 이유를 "
               "추정하지 않음^[생성형 AI에 이유를 묻지 않는 것은 설계상 선택. 문화에 대한 AI의 단정을 피하고 해석을 사람의 몫으로 남기기 위함]",
               "유의:"))
    x.append(H("(6) 신뢰도 확보 — 한 장씩 열어 채점한 탐지 정확도"))
    x.append(B("무작위 50장(한국 17·일본 17·베트남 16)의 박스 26개를 한 개씩 확인하고, 지표를 좌우하는 좌석·착석·오토바이 "
               "장면은 전부 확인^[판정 기록은 output/검수결과.csv(63건). 사람·물건의 일부만 보여도 실제 대상이면 정답, 사진·포장 그림 속 "
               "대상과 같은 대상의 중복 박스는 오답으로 채점]", "방법:"))
    x.append(CAP("[표 9] 탐지 검수 결과"))
    x.append(T([["검수 대상", "방법", "정답/전체", "정밀도", "조치"],
                ["사람", "무작위 50장의 박스 전부", "10/12", "83%", "오답: 광고 포스터 속 인물, 같은 사람 발 중복"],
                ["좌석", "좌석이 잡힌 장면 전수", "21/27", "78%", "오답 6장(장바구니·진열대 등)은 좌석 0으로 고쳐 반영"],
                ["  └ 나라별", "", "베트남 13/13 · 한국 6/8 · 일본 2/6", "", "일본 좌석 1.9%→0.6%, 한국 3.3%→2.5%"],
                ["앉은 사람", "착석 판정 장면 전수", "6/6", "100%", "—"],
                ["오토바이·자전거", "해당 장면 전수", "4/4", "100%", "종류 혼동 1건(오토바이를 자전거로), 지표는 둘을 합쳐 영향 없음"],
                ["음식·음료", "무작위 50장의 박스 전부", "0/12", "0%", "진열 상품·포장 그림을 오인 → '테이블 위 음식' 지표 제외"]], [1.3, 1.9, 1.7, 0.8, 3.0]))
    x.append(B("앞 절의 결과표와 그림은 좌석 오답 6장을 고친 뒤의 값. 자동 측정 그대로면 좌석은 한국 3.3%·일본 1.9%·베트남 4.6%로, "
               "보정 뒤에도 순위(베트남 > 한국 > 일본)는 같음", "보정 반영:"))
    x.append(B("무작위 50장 중 박스가 하나도 없는 35장을 다시 보니 좌석을 놓친 장면 1장, 사람 1명을 놓친 장면 1장. 한국 표본 17장 중 "
               "5장은 자막 글자 때문에 흔들림 필터를 통과한 흐린 장면으로, 한국 값을 조금 낮추는 방향의 오차", "놓친 것:"))
    x.append(B("좌석 판정은 베트남에서 전부 맞았고 일본에서 틀린 것이 많아, 보정으로 나라 간 차이가 오히려 조금 커짐. 음식처럼 "
               "정밀도가 낮은 지표는 결과에서 빼는 것이 원칙", "시사점:"))
    x.append(B("영상별 값을 점으로 함께 제시해 소수 영상이 결과를 끌고 가는지 확인(지표 막대 그림)", "영상 편중 점검:"))
    return x


def sec_3_1():
    x = []
    x.append(CAP("[표 9] 성과 지표와 시범 운영 목표(안)"))
    x.append(T([["지표", "현재", "목표(안)", "측정 방법"],
                ["외국 자료의 본론 반영", "'해외 사례' 파트에 분리", "본론 슬라이드의 50% 이상에 나라별 비교 포함", "최종 발표 자료 분석"],
                ["외국인 팀원의 역할", "자료 수집·번역 위주", "해석 카드 작성 100%", "팀별 해석 카드 작성자"],
                ["팀플 만족도", "측정 없음", "시범 전후 비교에서 개선", "한국·외국인 학생 설문"],
                ["탐지 신뢰도", "사람 83%·좌석 78%(파일럿 검수)", "좌석 90% 이상(학습 데이터 보강)", "무작위 표본 + 핵심 지표 전수 검수"]],
               [1.7, 1.7, 2.4, 1.8]))
    x.append(H("정성적 기대효과"))
    x.append(B("문화 차이가 번역 과정에서 사라지는 잡음이 아니라, 측정하고 해석하는 인사이트로 전환", "① 다양한 문화의 어울림:"))
    x.append(B("부록이던 외국 자료가 본론의 근거가 되어, 한국 자료와 외국 자료가 같은 위치에 놓임", "③ 중심과 주변의 어울림:"))
    x.append(B("'뭘 시키지?'가 '이 해석은 이 사람만 할 수 있다'로 바뀌고, 언어 수준과 무관하게 같은 차트를 보며 토론", "팀플 구조:"))
    x.append(B("한국 학생에게는 외국인 팀원이 있기에 가능한 조사라는 동기가 생겨, 유학생 기피 대신 협업 유인이 됨", "참여 유인:"))
    return x


def sec_3_2():
    x = []
    x.append(CAP("[표 10] 활용 대상과 활용처"))
    x.append(T([["대상", "활용"],
                ["문화 비교형 수업(교양·전공)", "국가 비교 팀플 과제의 조사 도구. 한일문화콘텐츠 전공 등에서 시범"],
                ["교수자", "외국인 학생이 포함된 팀의 역할 설계 가이드, 해석 카드 기반 평가"],
                ["국제처·유학생 지원 부서", "유학생-한국 학생 협업 프로그램의 공동 과제 도구"],
                ["교류 프로그램", "해외 자매대학과의 공동 현장 비교 과제"]],
               [2.2, 5.0]))
    x.append(H("확장 방향"))
    x.append(B("편의점은 예시. 카페·전통시장·캠퍼스·거리 간판·급식 등 현장 이미지로 비교할 수 있는 모든 과제에 같은 방식 적용",
               "대상 확장:"))
    x.append(B("대상에 맞는 지표 규칙만 바꾸면 되도록 설계(예: 거리 간판 — 문자 인식으로 언어별 간판 비율)", "지표 확장:"))
    x.append(H("추진 계획과 한계"))
    x.append(CAP("[표 11] 추진 단계(안)"))
    x.append(T([["단계", "내용", "결과물"],
                ["1. 파일럿(완료)", "세 나라 편의점 영상 {}편, 장면 {}장 분석, 5단계 웹 프로토타입·시연 영상 제작".format(N_VID_ALL, N_SCN_ALL),
                 "지표·시각화·프로토타입 자동 생성 코드"],
                ["2. 직접 촬영", "유학생 네트워크로 현지 사진 확보, 자세 추정 모델로 착석 판별 개선", "표본 편향 완화"],
                ["3. 수업 시범", "문화 비교형 수업 1~2개에서 팀플 도구로 운영", "성과 지표 첫 측정"]],
               [1.6, 3.8, 1.8]))
    x.append(B("유튜버가 고른 매장이며, 한국은 현지인 영상, 일본·베트남은 여행자 영상 비중이 높아 촬영 시선이 다름. 일본은 "
               "로손 매장 영상에 치우침", "표본 편향:"))
    x.append(B("착석은 박스 겹침으로 추정한 값으로 자세를 직접 보지 않음. 좌석이 화면 밖에 있으면 놓침", "측정 한계:"))
    x.append(B("나라당 영상 {}~{}편 규모의 파일럿으로, 베트남 결과는 영상 2편에 좌우됨. 수치는 경향 확인용이며 나라 전체를 대표하지 않음".format(
        min(N_VID.values()), max(N_VID.values())), "규모:"))
    return x


RESULT_NOTES = [
    H("결과 해석 — 경향은 가설 방향, 확정은 아직"),
    B("좌석·착석·무리·오토바이·자전거 네 지표 모두 베트남에서 가장 높음. 가설('베트남은 머무는 곳')과 같은 방향", "경향:"),
    B("일본은 가설('한국과 베트남의 중간')과 달리 네 지표 모두 한국과 비슷하거나 낮음. 가설은 절반만 맞음", "가설과 다른 점:"),
    B("베트남의 높은 값은 7편 중 2편(좌석 20.0%·12.5%)에서 나왔고 나머지 5편은 한국·일본과 비슷. 한국도 1편(좌석 12.5%)이 "
      "평균을 끌어올림^[베트남 PMkTMjwLLHs(호찌민 서클K, 좌석 20.0%)·UV8pqZCBi10(하노이 서클K, 12.5%), 한국 AeqkHad6Ijc"
      "(청주 세븐일레븐, 12.5%)] → 이 규모로는 나라 간 차이로 단정할 수 없고 '경향'까지만 말할 수 있음", "영상 편중:"),
    B("한눈의 목적은 결론을 대신 내리는 것이 아니라 '베트남의 이 두 매장은 왜 달랐는가'처럼 현지 팀원이 답할 질문을 "
      "만드는 것. 파일럿은 그 질문이 실제 데이터에서 나온다는 것을 확인", "의미:"),
]

REFS = [
    "한국경제(2026.1.27.), \"[단독] 조별과제 걸리면 지옥…한국말 못 하는 유학생이 '절반'\" (hankyung.com/article/202601274102i)",
    "한국경제(2026.1.27.), \"외국인 유학생 절반, 어학능력 미달…소통 안돼 팀플 망쳐\" (hankyung.com/article/2026012759621)",
    "오마이뉴스(2020.12.1.), \"'한국 유학 왔는데 한국인 친구 없어요'... 겉도는 외국인 유학생\" (ohmynews.com, A0002697678)",
    "Ultralytics YOLO11 (docs.ultralytics.com) / Lin TY 외(2014), Microsoft COCO: Common Objects in Context, ECCV",
    "Radford A 외(2021), Learning Transferable Visual Models From Natural Language Supervision (CLIP), ICML",
    "파일럿 분석 영상: 유튜브 공개 영상 21편(목록·주소는 data/영상목록.csv), 분석 목적으로만 사용",
]


# ─────────────────────────────────────────────────────────────
# 조립
# ─────────────────────────────────────────────────────────────
def fill_header(xml):
    """첫 번째(분석 부문) 머리 표를 채운다."""
    xml = xml.replace("[데이터 분석 부문 아이디어 기획서]", "[AI를 활용한 어울림 공모전 아이디어 기획서]", 1)
    i = xml.find("<hp:tbl")
    j = xml.find("</hp:tbl>", i) + len("</hp:tbl>")
    t = xml[i:j]
    t = t.replace('<hp:run charPrIDRef="17"><hp:t>아이디어명을 입력하세요</hp:t></hp:run>',
                  '<hp:run charPrIDRef="{}"><hp:t>{}</hp:t></hp:run>'.format(C_BOLD, esc(IDEA)), 1)
    # 예시 문단 삭제
    t = re.sub(r'<hp:p id="0" paraPrIDRef="30"[^>]*><hp:run charPrIDRef="17"><hp:t>\(예: HACCP, GMP[^<]*</hp:t></hp:run>'
               r'(?:<hp:run charPrIDRef="16"/>)?(?:<hp:linesegarray>.*?</hp:linesegarray>)?</hp:p>', "", t, count=1, flags=re.S)
    # '인증원 공공데이터 필수' 안내 문단 삭제(이 공모전과 무관)
    k = t.find("한국식품안전관리인증원 공공데이터 필수")
    if k > 0:
        ps = t.rfind("<hp:p ", 0, k)
        pe = t.find("</hp:p>", k) + len("</hp:p>")
        t = t[:ps] + t[pe:]
    # 팀명·주기획자 빈칸
    blank_cell = '<hp:p id="2147483648" paraPrIDRef="30" styleIDRef="28" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="16"/>'
    for name in TEAM:
        t = t.replace(blank_cell, blank_cell.replace('<hp:run charPrIDRef="16"/>',
                                                     '<hp:run charPrIDRef="16"><hp:t>{}</hp:t></hp:run>'.format(esc(name))), 1)
    # 주요 활용 데이터
    data_t = "<hp:lineBreak/>".join(esc(s) for s in DATA_LINES)
    t = t.replace("<hp:t>• 공공데이터: [기관명] [데이터셋명]<hp:lineBreak/>• 기타데이터: [자체수집/민간데이터 등]</hp:t>",
                  "<hp:t>" + data_t + "</hp:t>", 1)
    t = t.replace('<hp:run charPrIDRef="17"><hp:t>• 공', '<hp:run charPrIDRef="16"><hp:t>• 공', 1)
    # 요약
    t = t.replace('<hp:run charPrIDRef="17"><hp:t>아이디어의 목적, 주요 내용 및 기대효과를 1~2문장으로 요약 작성</hp:t></hp:run>',
                  '<hp:run charPrIDRef="16"><hp:t>{}</hp:t></hp:run>'.format(esc(SUMMARY)), 1)
    for must in [IDEA[:10], SUMMARY[:10], DATA_LINES[0][:10]]:
        assert esc(must) in t, must
    return xml[:i] + t + xml[j:]


def heading_para(xml, text, start):
    k = xml.find(text, start)
    assert k > 0, text
    ps = xml.rfind("<hp:p ", 0, k)
    pe = xml.find("</hp:p>", k) + len("</hp:p>")
    return ps, pe


def build_section(xml):
    xml = fill_header(xml)
    for old, new in [("1-2. 데이터 기반 해결 필요성", "1-2. AI 기반 해결 필요성"),
                     ("2-3. 데이터 전처리·가공 방법, 분석 기법", "2-3. 분석 방법 및 파일럿 결과")]:
        xml = xml.replace(old, new, 1)
    vis = xml.find("[데이터 시각화 부문 아이디어 기획서]")
    vis_p = xml.rfind("<hp:p ", 0, vis)
    head = xml[:vis_p]
    # 분석 부문 머리말 문단을 차례로 찾아, 각 머리말 뒤에 본문을 넣는다
    plan = [("제안 배경 및 추진 필요성", []), (" 1-1. 현황 및 문제점", sec_1_1()),
            (" 1-2. AI 기반 해결 필요성", sec_1_2()), ("2. 주요 내용 및 분석 방안", []),
            ("2-1. 아이디어 핵심 개요", sec_2_1()), (" 2-2. 활용 데이터", sec_2_2()),
            (" 2-3. 분석 방법 및 파일럿 결과", sec_2_3()), ("3. 기대효과 및 활용 방안", []),
            (" 3-1. 기대효과(정량적/정성적)", sec_3_1()), (" 3-2. 예상 활용 대상 및 활용처", sec_3_2())]
    out, pos = [], 0
    first_ps, _ = heading_para(head, plan[0][0], 0)
    out.append(head[:first_ps])
    pos = first_ps
    for text, body in plan:
        ps, pe = heading_para(head, text, pos)
        out.append(head[ps:pe])
        out.extend(body)
        pos = pe
    # 참고문헌
    out.append(BLANK())
    out.append(P([("참고 자료", C_BOLD)]))
    for r in REFS:
        out.append(P([("· " + r, C_SMALL)], pp=P_BULLET))
    body = "".join(out)
    # 그림·표 번호를 나오는 순서대로 다시 매긴다
    for kind in ("그림", "표"):
        cnt = [0]
        def _n(m, cnt=cnt, kind=kind):
            cnt[0] += 1
            return "[{} {}]".format(kind, cnt[0])
        body = re.sub(r"\[" + kind + r" \d+\]", _n, body)
    return body + "</hs:sec>"


def main():
    zin = zipfile.ZipFile(FORM)
    sec = zin.read("Contents/section0.xml").decode("utf-8")
    sec = build_section(sec)
    sec = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", sec, flags=re.S)
    # 잘 짜인 XML인지 확인
    import xml.dom.minidom
    xml.dom.minidom.parseString(sec.encode("utf-8"))

    hpf = zin.read("Contents/content.hpf").decode("utf-8")
    items = "".join('<opf:item id="{}" href="BinData/{}.png" media-type="image/png" isEmbeded="1"/>'.format(i, i) for i, _ in _images)
    hpf = hpf.replace('<opf:item id="section0"', items + '<opf:item id="section0"', 1)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    hpf = re.sub(r"<opf:title\s*/>|<opf:title>.*?</opf:title>", "<opf:title>" + esc("AI를 활용한 어울림 공모전 기획서 한눈") + "</opf:title>", hpf, count=1)
    hpf = re.sub(r'(<opf:meta name="ModifiedDate" content="text">)[^<]*', r"\g<1>" + now, hpf)
    xml.dom.minidom.parseString(hpf.encode("utf-8"))

    prv = re.sub(r"<[^>]+>", " ", sec)
    prv = re.sub(r"\s+", " ", html.unescape(prv))[:1000]

    zout = zipfile.ZipFile(OUT, "w")
    for info in zin.infolist():
        n = info.filename
        if n == "Contents/section0.xml":
            data = sec.encode("utf-8")
        elif n == "Contents/content.hpf":
            data = hpf.encode("utf-8")
        elif n == "Preview/PrvText.txt":
            data = prv.encode("utf-8")
        else:
            data = zin.read(n)
        comp = zipfile.ZIP_STORED if n == "mimetype" else zipfile.ZIP_DEFLATED
        zout.writestr(zipfile.ZipInfo(n, date_time=datetime.datetime.now().timetuple()[:6]), data, compress_type=comp)
    for iid, path in _images:
        zout.write(path, "BinData/{}.png".format(iid), compress_type=zipfile.ZIP_STORED)
    zout.close()
    print("[저장]", OUT, "그림", len(_images), "개, 본문 글자 수 약", len(re.sub(r"<[^>]+>", "", sec)))


if __name__ == "__main__":
    main()
