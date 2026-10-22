# 한눈 — 번역 없이 문화를 비교하는 AI 비전 팀플 도구

2026 HUSS 「AI를 활용한 어울림 공모전」 **최우수상(1등)** 출품작의 코드와 결과물입니다.
프로젝트 설명은 [portfolio/02_hannun.md](https://github.com/Kseongbeen/portfolio/blob/main/projects/02_hannun.md)에 있습니다.

## 구성
```
*.py      01~04 수집·프레임 추출·탐지·지표 계산, 05~16 발표 자료·기획서·대본 생성
data/     영상 목록과 탐지·장면 분류 결과 (CSV)
output/   지표 요약, 그림, 프로토타입(HTML), 시연 영상
```

## 실행
```bash
pip install ultralytics opencv-python pandas matplotlib yt-dlp
python 01_영상수집.py      # 영상 목록의 영상을 data/video 에 받음
python 02_프레임추출.py
python 03_장면분류_탐지.py  # yolo11s.pt 는 처음 실행할 때 자동으로 받음
python 04_지표_시각화.py
```

## 데이터에 대해
- 원본 영상과 추출 프레임은 저작권 때문에 레포에 넣지 않았습니다. `data/영상목록.csv`의 유튜브 링크로 다시 받을 수 있습니다.
- 영상은 분석 목적으로만 사용했고, 출처는 발표 자료에 표시했습니다.
