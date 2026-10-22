# -*- coding: utf-8 -*-
"""
09. 프로토타입 화면 캡처와 시연 영상(MP4)을 만든다

- 캡처: 5단계 화면을 한 장씩 PNG로 저장(PPT·기획서 삽입용)
- 영상: ?demo=1 자동 진행을 크롬(Playwright)으로 녹화 → ffmpeg로 H.264 MP4 변환

산출: output/프로토_1~5.png, output/한눈_시연영상.mp4
"""

import glob
import os
import shutil
import subprocess
import sys

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
HTML = os.path.join(OUT, "한눈_프로토타입.html")
URL = "file:///" + HTML.replace("\\", "/")
VW, VH = 1280, 720
TMP = os.path.join(OUT, "_video_tmp")


def compose():
    """기획서용: ②~⑤ 화면 캡처를 2×2로 모은 그림."""
    from PIL import Image
    ims = [Image.open(os.path.join(OUT, "프로토_{}.png".format(i))).convert("RGB").resize((1280, 720)) for i in (2, 3, 4, 5)]
    g = 24
    sheet = Image.new("RGB", (1280 * 2 + g, 720 * 2 + g), "white")
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % 2) * (1280 + g), (k // 2) * (720 + g)))
    sheet.save(os.path.join(OUT, "그림_프로토타입.png"))


def main():
    with sync_playwright() as p:
        br = p.chromium.launch(channel="chrome")
        # 화면 캡처
        pg = br.new_page(viewport={"width": VW, "height": VH}, device_scale_factor=2)
        for i in range(5):
            pg.goto(URL + "?step={}".format(i))
            pg.wait_for_timeout(900)
            pg.screenshot(path=os.path.join(OUT, "프로토_{}.png".format(i + 1)))
        pg.close()
        # 시연 녹화
        shutil.rmtree(TMP, ignore_errors=True)
        ctx = br.new_context(viewport={"width": VW, "height": VH}, record_video_dir=TMP,
                             record_video_size={"width": VW, "height": VH})
        pg = ctx.new_page()
        pg.goto(URL + "?demo=1")
        pg.wait_for_function("document.body.dataset.done === '1'", timeout=180000)
        pg.wait_for_timeout(1500)
        ctx.close()
        br.close()
    webm = glob.glob(os.path.join(TMP, "*.webm"))[0]
    mp4 = os.path.join(OUT, "한눈_시연영상.mp4")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-y", "-i", webm, "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-r", "30", "-crf", "20", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(TMP, ignore_errors=True)
    compose()
    print("[저장]", mp4, "{:.1f} MB".format(os.path.getsize(mp4) / 1e6))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
