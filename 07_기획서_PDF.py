# -*- coding: utf-8 -*-
"""
07. 한글(HWP) 자동화로 기획서 hwpx를 PDF로 저장한다

- 한글 자동화는 파일을 열 때 보안 확인창을 띄우므로, 파일 경로 확인 모듈(pyhwpx에 들어 있는
  FilePathCheckerModule.dll, HKCU\\Software\\HNC\\HwpAutomation\\Modules에 등록)을 먼저 불러온다.
- 한글 창은 숨긴 채로 열고, 끝나면 닫는다.

산출: output/한눈_기획서.pdf
"""

import os
import sys

import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "output", "한눈_기획서.hwpx")
DST = os.path.join(HERE, "output", "한눈_기획서.pdf")


def main():
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        hwp.XHwpWindows.Item(0).Visible = False
        hwp.Open(SRC, "HWPX", "forceopen:true")
        if os.path.exists(DST):
            os.remove(DST)
        hwp.SaveAs(DST, "PDF", "")
        pages = hwp.PageCount
    finally:
        hwp.Clear(1)
        hwp.Quit()
    print("[저장]", DST, "{}쪽".format(pages), "{:,} bytes".format(os.path.getsize(DST)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
