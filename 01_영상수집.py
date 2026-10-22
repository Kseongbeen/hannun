# -*- coding: utf-8 -*-
"""
01. 나라별 편의점 매장 둘러보기 영상을 모은다

- 1차 수집(현지어 'vlog' 검색)은 일본 검색 결과에 일본인이 찍은 한국 편의점 영상, 집 먹방이 섞여
  폐기(_보관_1차수집). 2차는 영상 종류를 '매장 둘러보기(투어)'로 통일하고 제목으로 촬영 국가를 확인한다.
- 검색어: 나라별 대표 편의점 브랜드 + 도시 + tour/둘러보기(현지어·영어 병행)
- 제목 필터: 그 나라 지명·브랜드가 하나 이상 있어야 하고, 다른 나라 이름이 있으면 버린다.
- 2~25분 길이, 360p(없으면 480p) mp4. 나라당 N_PER개. 출처는 data/영상목록.csv에 남긴다.

산출: data/video/{KR,JP,VN}/*.mp4, data/영상목록.csv
"""

import csv
import os
import re
import sys

import imageio_ffmpeg
import yt_dlp

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(HERE, "data", "video")
LIST = os.path.join(HERE, "data", "영상목록.csv")

N_PER = 8           # 나라당 받을 영상 수
N_SEARCH = 25       # 검색어마다 살펴볼 결과 수
MIN_S, MAX_S = 120, 1500

QUERIES = {
    "KR": ["편의점 둘러보기", "GS25 Seoul convenience store tour 4K", "CU Korea convenience store tour 4K",
           "7-Eleven Seoul convenience store tour 4K", "korean convenience store tour"],
    "JP": ["Lawson Tokyo convenience store tour 4K", "FamilyMart Japan convenience store tour 4K",
           "7-Eleven Japan convenience store tour 4K", "コンビニ 店内 散策 東京", "konbini tour Osaka"],
    "VN": ["Circle K Vietnam convenience store tour", "GS25 Việt Nam cửa hàng tiện lợi", "Ministop Việt Nam",
           "cửa hàng tiện lợi Sài Gòn", "convenience store Ho Chi Minh city tour", "FamilyMart Việt Nam"],
}

# 제목에 하나 이상 있어야 하는 말(촬영 국가) / 있으면 버리는 말(다른 나라)
MUST = {
    "KR": r"korea|seoul|busan|서울|한국|부산|편의점|🇰🇷",
    "JP": r"japan|tokyo|osaka|kyoto|日本|東京|大阪|konbini|ローソン|ファミマ|セブン|コンビニ|🇯🇵",
    "VN": r"vietnam|việt|viet nam|hanoi|hà nội|saigon|sài gòn|ho chi minh|hồ chí minh|da nang|đà nẵng|tiện lợi|🇻🇳",
}
NOT = {
    "KR": r"japan|tokyo|osaka|일본|도쿄|오사카|vietnam|베트남|taiwan|대만|china|중국|india|hawaii|스위스|필리핀|마닐라|"
          r"미국|태국|유럽|호주|캐나다|홍콩|싱가포르|몽골|swiss|philippines|thailand|usa|🇯🇵|🇻🇳",
    "JP": r"korea|韓国|韓|seoul|ソウル|vietnam|ベトナム|taiwan|台湾|india|インド|hawaii|ハワイ|🇰🇷|🇻🇳",
    "VN": r"korea|hàn quốc|hàn|seoul|japan|nhật|tokyo|mỹ|thái|taiwan|đài loan|trung quốc|🇰🇷|🇯🇵",
}
STORE = r"convenience|편의점|konbini|コンビニ|ローソン|ファミ|セブン|lawson|family ?mart|7[- ]?eleven|seven|gs25|cu |circle ?k|ministop|tiện lợi|b's mart"


def title_ok(cc, t):
    t = (t or "").lower()
    return bool(re.search(MUST[cc], t)) and not re.search(NOT[cc], t) and bool(re.search(STORE, t))


def search(query):
    opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        res = ydl.extract_info("ytsearch{}:{}".format(N_SEARCH, query), download=False)
    return res.get("entries") or []


def main():
    rows = []
    if os.path.exists(LIST):
        with open(LIST, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    have = {r["id"] for r in rows}
    if os.path.exists(os.path.join(HERE, "data", "제외영상.csv")):   # 사람이 확인해 뺀 영상은 다시 받지 않는다
        with open(os.path.join(HERE, "data", "제외영상.csv"), encoding="utf-8-sig") as f:
            have |= {r["id"] for r in csv.DictReader(f)}
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    for cc, queries in QUERIES.items():
        out = os.path.join(VID, cc)
        os.makedirs(out, exist_ok=True)
        got = sum(1 for r in rows if r["country"] == cc)
        seen = set()
        for q in queries:
            for e in search(q):
                if got >= N_PER:
                    break
                vid, dur = e.get("id"), e.get("duration") or 0
                if not vid or vid in seen or vid in have or not (MIN_S <= dur <= MAX_S):
                    continue
                if not title_ok(cc, e.get("title")):
                    continue
                seen.add(vid)
                opts = {
                    "quiet": True, "no_warnings": True, "noprogress": True,
                    "format": "best[height<=360][ext=mp4]/bestvideo[height<=360][ext=mp4]/best[height<=480][ext=mp4]/bestvideo[height<=480][ext=mp4]",
                    "outtmpl": os.path.join(out, "%(id)s.%(ext)s"),
                    "ffmpeg_location": ffmpeg,
                }
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        info = ydl.extract_info("https://www.youtube.com/watch?v=" + vid, download=True)
                except Exception as ex:  # 지역 제한·연령 제한 등은 건너뛴다
                    print("  건너뜀", cc, vid, str(ex)[:80])
                    continue
                rows.append({"country": cc, "id": vid, "query": q, "title": info.get("title", ""),
                             "channel": info.get("channel", ""), "duration": dur,
                             "url": "https://www.youtube.com/watch?v=" + vid})
                have.add(vid)
                got += 1
                print("[{}] {}/{} {}".format(cc, got, N_PER, info.get("title", "")[:50]), flush=True)
                with open(LIST, "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    w.writeheader()
                    w.writerows(rows)
        print("==", cc, "완료", got, flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
