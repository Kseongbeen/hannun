# -*- coding: utf-8 -*-
"""
10. 사용자가 한글에서 손본 기획서(output/한눈_기획서.hwpx)를 그대로 두고, 필요한 곳만 고친다

- 06_기획서_HWPX.py로 다시 만들면 사용자 수정(서식·문장, (5) 해석 카드 절 삭제)이 사라지므로 XML을 직접 고친다.
- 고치는 것
  1) 제출물에 없는 파일·폴더 경로(.py, .csv, output/, data/, _보관_…)를 각주·본문·참고 자료에서 뺀다
  2) (5) 절을 지우며 남은 조각 문단('작성. AI는 이유를 추정하지 않음' + 각주)을 지운다
  3) 절 번호·표 번호·지표 개수 등 앞뒤가 맞지 않는 곳을 맞춘다
- 원본은 output/한눈_기획서_사용자수정_원본백업.hwpx로 보관되어 있다.

산출: output/한눈_기획서.hwpx(덮어씀)
"""

import os
import re
import sys
import zipfile
import xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "output", "한눈_기획서.hwpx")
BACKUP = os.path.join(HERE, "output", "한눈_기획서_사용자수정_원본백업.hwpx")
TMP = SRC + ".tmp"

# (찾을 글, 바꿀 글) — 모두 원문에 정확히 한 번 있어야 한다
REPL = [
    # 1) 파일·폴더 경로 제거
    ("한 파일짜리 웹앱(output/한눈_프로토타입.html). 주소 뒤에 ?demo=1을 붙이면 자막과 함께 자동 시연되며, 이를 녹화한 것이 제출 영상(한눈_시연영상.mp4)",
     "설치 없이 웹 브라우저에서 바로 열리는 웹앱. 자막과 함께 자동으로 진행되는 시연 모드를 녹화한 것이 함께 제출한 시연 영상"),
    ("2026.9.27. 검색·수집. 영상 목록과 주소는 data/영상목록.csv, 제외 사유는 data/제외영상.csv",
     "2026.9.27. 검색·수집. 분석에 쓴 영상 목록은 발표 자료 부록에 수록"),
    ("1차 수집 자료(한국 10편·일본 8편)는 _보관_1차수집 폴더에 보관",
     "1차 수집 규모는 한국 10편·일본 8편"),
    ("판정 기록은 output/검수결과.csv(63건). ",
     "판정 63건(무작위 표본 박스 26개, 좌석 장면 27장, 착석 장면 6장, 오토바이·자전거 장면 4장). "),
    ("(목록·주소는 data/영상목록.csv)", "(한국 6편·일본 8편·베트남 7편, 목록은 발표 자료 부록)"),
    ("목록과 주소는 참고 자료에 명시", "영상 목록은 발표 자료 부록에 수록"),
    # 3) 앞뒤 맞추기
    ("((6) 참고)", "((5) 참고)"),
    ("좌석 오답 6장은 사람 검수대로 고쳐 반영", "좌석 오답 6장은 검수 결과대로 고쳐 반영"),
    ("장면마다 다섯 지표", "장면마다 네 지표"),
    ("다섯 지표의 나라별", "네 지표의 나라별"),
    ("[표 9] 탐지", "[표 8] 탐지"),
    ("[표 10] 성과", "[표 9] 성과"),
    ("[표 11] 활용", "[표 10] 활용"),
    ("[표 12] 추진", "[표 11] 추진"),
    ("기업 홍보 영상(연출 장면)", "기업 홍보 영상(연출 장면))"),
    ("'언어'을", "'언어'를"),
]


def remove_paragraph(x, needle):
    """needle이 든 최상위 문단(<hp:p>…</hp:p>, 안의 각주 문단 포함)을 통째로 지운다."""
    k = x.find(needle)
    assert k > 0, needle
    ps = x.rfind("<hp:p ", 0, k)
    depth, i = 0, ps
    while True:
        a, b = x.find("<hp:p ", i), x.find("</hp:p>", i)
        if a != -1 and a < b:
            depth += 1
            i = a + 5
        else:
            depth -= 1
            i = b + len("</hp:p>")
            if depth == 0:
                return x[:ps] + x[i:]


def remove_footnote(x, needle):
    """needle이 든 각주 컨트롤(<hp:ctrl><hp:footNote>…</hp:footNote></hp:ctrl>)을 지운다."""
    k = x.find(needle)
    assert k > 0, needle
    fs = x.rfind("<hp:ctrl><hp:footNote", 0, k)
    fe = x.find("</hp:footNote></hp:ctrl>", k) + len("</hp:footNote></hp:ctrl>")
    return x[:fs] + x[fe:]


def main():
    z = zipfile.ZipFile(BACKUP)          # 항상 사용자 원본에서 시작(여러 번 돌려도 같은 결과)
    x = z.read("Contents/section0.xml").decode("utf-8")
    n0 = x.count("<hp:footNote ")
    # 2) (5) 절을 지우며 남은 조각 문단
    x = remove_paragraph(x, "작성. AI는 이유를 추정하지 않음")
    # 결과표 각주는 코드·파일 이름뿐이라 통째로 지운다
    x = remove_footnote(x, "산출 파일 output/지표_요약.csv")
    for a, b in REPL:
        assert x.count(a) == 1, (a, x.count(a))
        x = x.replace(a, b)
    # 글 길이가 바뀐 문단은 한글이 저장해 둔 줄 배치(linesegarray)와 어긋나 뒤쪽이 안 그려진다 → 지우고 한글이 다시 계산하게 한다
    x = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", x, flags=re.S)
    for bad in ("output/", "data/", ".csv", ".py", "_보관_", ".html", ".mp4"):
        assert bad not in re.sub(r"<[^>]+>", "", x), bad
    xml.dom.minidom.parseString(x.encode("utf-8"))

    with zipfile.ZipFile(TMP, "w") as out:
        for info in z.infolist():
            data = x.encode("utf-8") if info.filename == "Contents/section0.xml" else z.read(info.filename)
            # 원본 ZipInfo를 그대로 쓰면 한글이 뒤쪽 그림부터 못 읽는다 → 새 ZipInfo에 이름·날짜·압축 방식만 옮긴다
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            out.writestr(zi, data)
    z.close()
    os.replace(TMP, SRC)
    print("[저장]", SRC, "각주 {} → {}".format(n0, x.count("<hp:footNote ")))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
