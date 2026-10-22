# -*- coding: utf-8 -*-
"""
16. 슬라이드 1장 = 대본 1쪽(워드, 가로)으로 만든다 — 총 19쪽

- 대본 내용·시간은 15_발표대본_5분.py의 ROWS를 그대로 쓴다(5분 분량).
- 각 쪽: 위에 쪽 번호·제목·시간, 왼쪽에 해당 슬라이드 그림(최종 발표자료 PDF에서 뽑음), 오른쪽에 큰 글씨 대본과 동작.

산출: output/한눈_발표대본_쪽별.docx
"""

import importlib.util
import os
import sys
import tempfile

import fitz
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
SLIDES = os.path.join(HERE, "output", "한눈_발표자료.pdf")
OUT = os.path.join(HERE, "output", "한눈_발표대본_쪽별.docx")
_spec = importlib.util.spec_from_file_location("m15", os.path.join(HERE, "15_발표대본_5분.py"))
m15 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m15)
ROWS = m15.ROWS


def no_borders(table):
    tbl = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + side)
        e.set(qn("w:val"), "nil")
        b.append(e)
    tbl.append(b)


def run(p, text, size, bold=False, color=None):
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    return r


def main():
    pdf = fitz.open(SLIDES)
    assert len(pdf) == len(ROWS) == 19, (len(pdf), len(ROWS))
    tmp = tempfile.mkdtemp()

    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    sec.left_margin = sec.right_margin = Cm(1.6)
    sec.top_margin = sec.bottom_margin = Cm(1.3)
    st = doc.styles["Normal"]
    st.font.name = "맑은 고딕"
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")

    acc = 0
    for k, (no, title, sec_, text, act) in enumerate(ROWS):
        acc += sec_
        img = os.path.join(tmp, "s%02d.png" % no)
        pdf[no - 1].get_pixmap(dpi=110).save(img)

        # 머리줄: 쪽 번호 · 제목 · 시간
        p = doc.add_paragraph()
        run(p, "{:02d} / 19   ".format(no), 13, True, "3182F6")
        run(p, title, 20, True, "191F28")
        tm = "   {}초 · 누적 {}:{:02d}".format(sec_, acc // 60, acc % 60) if sec_ else "   질문이 나올 때만"
        run(p, tm, 12, False, "8B95A1")
        p.paragraph_format.space_after = Pt(10)

        t = doc.add_table(rows=1, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        no_borders(t)
        left, right = t.rows[0].cells
        left.width, right.width = Cm(11.5), Cm(14.6)
        left.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        left.paragraphs[0].add_run().add_picture(img, width=Cm(11.0))
        q = left.add_paragraph()
        run(q, "동작 · 가리킬 곳", 10, True, "3182F6")
        q = left.add_paragraph()
        run(q, act, 12, False, "4E5968")

        r0 = right.paragraphs[0]
        run(r0, text, 18, False, "191F28")
        r0.paragraph_format.line_spacing = 1.6

        if k < len(ROWS) - 1:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.save(OUT)
    print("[저장]", OUT, len(ROWS), "쪽")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
