# -*- coding: utf-8 -*-
"""
11. 사용자가 두 번째로 손본 기획서의 서식만 정리한다(문장은 그대로)

- 원본: output/한눈_기획서_사용자수정2_백업.hwpx (사용자 수정본 그대로 보관)
- 정리 내용
  1) '2. 주요 내용 및 분석 방안' 머리말만 굵지 않던 것 → 1·3장 머리말과 같은 글자 모양
  2) (표 뒤 빈 줄은 쪽 흐름을 무너뜨려 제외)
  3) 참고 자료가 양쪽 정렬이라 주소 때문에 글자 사이가 벌어지던 것 → 왼쪽 정렬(내어쓰기 유지)
  4) CLIP 각주의 긴 모델 이름 때문에 글자 사이가 벌어지던 것 → 짧게
  7) 발표 3쪽과 같은 통계를 1-1에 각주와 함께 추가(규모 30.7만 명, 서울대 조사 36.6%·50.9%)
  6) 쪽 끝에서 한 글자만 넘어가던 항목 → 문구를 줄여 한 쪽에
  5) [표 8] 첫 열이 좁아 '오토바이·자전 / 거'로 끊기던 것 → 줄바꿈 위치 지정

산출: output/한눈_기획서.hwpx
"""

import os
import re
import sys
import zipfile
import xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "output", "한눈_기획서_사용자수정2_백업.hwpx")
OUT = os.path.join(HERE, "output", "한눈_기획서.hwpx")
GAP = ('<hp:p id="0" paraPrIDRef="12" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
       '<hp:run charPrIDRef="2"><hp:t/></hp:run></hp:p>')


def para_end(x, ps):
    depth, i = 0, ps
    while True:
        a, b = x.find("<hp:p ", i), x.find("</hp:p>", i)
        if a != -1 and a < b:
            depth, i = depth + 1, a + 5
        else:
            depth, i = depth - 1, b + len("</hp:p>")
            if depth == 0:
                return i


def top_paragraphs(x):
    """본문 최상위 문단의 (시작, 끝) 목록."""
    out, i = [], x.find("<hp:p ")
    while i != -1:
        e = para_end(x, i)
        out.append((i, e))
        i = x.find("<hp:p ", e)
    return out

_fn = [1400000000]


def FN(t):
    _fn[0] += 1
    fmt = '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
    return ('<hp:ctrl><hp:footNote number="1" suffixChar="41" instId="{i}"><hp:subList id="" textDirection="HORIZONTAL" '
            'lineWrap="BREAK" vertAlign="TOP" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" '
            'hasNumRef="0"><hp:p id="0" paraPrIDRef="10" styleIDRef="14" pageBreak="0" columnBreak="0" merged="0">'
            '<hp:run charPrIDRef="3"><hp:ctrl><hp:autoNum num="1" numType="FOOTNOTE">{f}</hp:autoNum></hp:ctrl>'
            '<hp:t> {t}</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl>').format(i=_fn[0], f=fmt, t=esc(t))


def BUL(label, text, note):
    """사용자 수정본의 '• 굵은 이름: 본문' 항목과 같은 글자·문단 모양."""
    return ('<hp:p id="0" paraPrIDRef="10" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            '<hp:run charPrIDRef="17"><hp:t>• </hp:t></hp:run><hp:run charPrIDRef="16"><hp:t>{}</hp:t></hp:run>'
            '<hp:run charPrIDRef="17"><hp:t> {}</hp:t>{}<hp:t/></hp:run></hp:p>').format(esc(label), esc(text), FN(note))


def REF(t):
    return ('<hp:p id="0" paraPrIDRef="10" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            '<hp:run charPrIDRef="1"><hp:t>{}</hp:t></hp:run></hp:p>').format(esc(t))


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def add_stats(x):
    """발표 3쪽과 같은 통계를 1-1에 넣는다(교차검증한 원문 기사 기준)."""
    k = x.find("어학 기준:")
    ps = x.rfind("<hp:p ", 0, k)
    x = x[:ps] + BUL("규모:", "국내 고등교육기관 외국인 유학생 30만 7천 명(2026년 4월 기준). 2023년 18만 2천 명에서 3년 새 약 1.7배",
                     "헤럴드경제(2026.9.8.), \"캠퍼스에 가득 외국인 유학생…30만명 시대 부실 유치 막고 '정착형 인재' 키운다\". 교육부 집계 인용") + x[ps:]
    k = x.find("팀플 기피:")
    pe = para_end(x, x.rfind("<hp:p ", 0, k))
    x = x[:pe] + BUL("팀플 참여:", "서울대 외국인 학위과정생 432명 조사에서 한국어 수업의 어려움으로 '토의 참여'(50.9%)와 '팀 프로젝트 "
                     "참여'(36.6%)를 꼽음. 한국어 강의를 이해하기 어렵다는 응답도 47.2%",
                     "서울대 다양성위원회(2018), 「서울대학교 외국인 학생 지원 방안 연구」. 경향신문(2018.12.3.) 보도") + x[pe:]
    k = x.find("· 오마이뉴스(2020.12.1.)")
    pe = para_end(x, x.rfind("<hp:p ", 0, k))
    x = x[:pe] + REF("· 헤럴드경제(2026.9.8.), \"캠퍼스에 가득 외국인 유학생…30만명 시대 부실 유치 막고 '정착형 인재' 키운다\" "
                     "(biz.heraldcorp.com/article/10866128)") + \
        REF("· 서울대 다양성위원회(2018), 「서울대학교 외국인 학생 지원 방안 연구」 / 경향신문(2018.12.3.), \"서울대 외국인 유학생 "
            "절반 '한국어 수업 이해 못한다'\" (khan.co.kr/article/201812030934001)") + x[pe:]
    return x


def section(x):
    # 1) 2장 머리말 글자 모양
    a = '<hp:run charPrIDRef="21"><hp:t>2. 주요 내용 및 분석 방안</hp:t>'
    assert x.count(a) == 1
    x = x.replace(a, a.replace('"21"', '"22"'))
    # 4) CLIP 각주
    a = "(Radford 외, 2021). openai/clip-vit-base-patch32 사용"
    assert x.count(a) == 1
    x = x.replace(a, "(Radford 외, 2021). ViT-B/32 모델 사용")
    # 5) [표 8] 첫 열 줄바꿈
    k = x.find("[표 8] 탐지 검수 결과")
    t0 = x.find("<hp:tbl ", k)
    t1 = x.find("</hp:tbl>", t0)
    tb = x[t0:t1]
    for a, b in [("<hp:t>오토바이·자전거</hp:t>", "<hp:t>오토바이·<hp:lineBreak/>자전거</hp:t>"),
                 ("<hp:t>베트남 13/13 · 한국 6/8 · 일본 2/6</hp:t>", "<hp:t>베트남 13/13<hp:lineBreak/>한국 6/8<hp:lineBreak/>일본 2/6</hp:t>")]:
        assert tb.count(a) == 1, a
        tb = tb.replace(a, b)
    x = x[:t0] + tb + x[t1:]
    # 6) '측정 한계' 항목 마지막 글자 하나('침')만 다음 쪽으로 넘어가던 것 → 한 줄에 들어가게 줄임
    a = "좌석이 화면 밖에 있으면 놓침"
    assert x.count(a) == 1
    x = x.replace(a, "화면 밖 좌석은 놓침")
    # 7) 발표 3쪽과 같은 통계(유학생 규모, 서울대 조사)를 1-1 항목·각주와 참고 자료에 추가
    x = add_stats(x)
    # 3) 참고 자료 문단 → 새 왼쪽 정렬 문단 모양
    k = x.find("<hp:t>참고 자료</hp:t>")
    head, tail = x[:k], x[k:]
    tail = tail.replace('<hp:p id="0" paraPrIDRef="10" ', '<hp:p id="0" paraPrIDRef="{REF_PP}" ')
    x = head + tail
    # 2) 표 뒤 빈 줄은 넣어 보니 쪽 흐름이 무너져(10쪽→12쪽) 넣지 않는다
    spans = []
    x = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", x, flags=re.S)
    return x, len(spans)


def header(h):
    """문단 모양 10(내어쓰기·양쪽 정렬)을 복제해 왼쪽 정렬 모양을 하나 더 만든다."""
    m = re.search(r'<hh:paraPr id="10".*?</hh:paraPr>', h, re.S)
    ids = [int(v) for v in re.findall(r'<hh:paraPr id="(\d+)"', h)]
    new = max(ids) + 1
    clone = m.group(0).replace('id="10"', 'id="{}"'.format(new), 1).replace('horizontal="JUSTIFY"', 'horizontal="LEFT"', 1)
    end = h.find("</hh:paraProperties>")
    h = h[:end] + clone + h[end:]
    h = re.sub(r'(<hh:paraProperties itemCnt=")(\d+)"', lambda g: '{}{}"'.format(g.group(1), int(g.group(2)) + 1), h, count=1)
    return h, new


def main():
    z = zipfile.ZipFile(SRC)
    h, new_pp = header(z.read("Contents/header.xml").decode("utf-8"))
    x, n_tbl = section(z.read("Contents/section0.xml").decode("utf-8"))
    x = x.replace("{REF_PP}", str(new_pp))
    for s in (x, h):
        xml.dom.minidom.parseString(s.encode("utf-8"))
    tmp = OUT + ".tmp"
    with zipfile.ZipFile(tmp, "w") as out:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename == "Contents/section0.xml":
                data = x.encode("utf-8")
            elif info.filename == "Contents/header.xml":
                data = h.encode("utf-8")
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            out.writestr(zi, data)
    z.close()
    os.replace(tmp, OUT)
    print("[저장]", OUT, "표 뒤 빈 줄 {}곳, 참고 자료 문단 모양 {}".format(n_tbl, new_pp))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
