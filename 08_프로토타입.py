# -*- coding: utf-8 -*-
"""
08. 「한눈」 프로토타입(한 파일짜리 웹앱)을 만든다

- 화면 흐름: ① 조사(나라별 현장 사진) → ② AI 측정(탐지 박스) → ③ 비교(레이더·영상별 점) → ④ 해석 카드 → ⑤ 발표로 보내기
- 사진·탐지 박스·지표는 파일럿 실제 결과(data/탐지결과.csv, output/지표_*.csv)를 그대로 넣는다.
  팀원 이름과 해석 문장은 시연용 예시이다.
- ?demo=1 로 열면 자막과 함께 자동으로 진행된다(시연 영상 녹화용).

산출: output/한눈_프로토타입.html
"""

import base64
import csv
import io
import json
import os
import sys
from collections import defaultdict

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output", "한눈_프로토타입.html")
CC = ["KR", "JP", "VN"]
IND = ["좌석", "착석", "무리", "오토바이·자전거"]
SHOW = {"person": "사람", "chair": "의자", "bench": "벤치", "couch": "소파", "dining table": "테이블",
        "motorcycle": "오토바이", "bicycle": "자전거"}   # 음식·음료는 검수 정밀도 0%라 표시하지 않음
KIND = {"person": "p", "chair": "s", "bench": "s", "couch": "s", "dining table": "s",
        "motorcycle": "r", "bicycle": "r"}


def rows(p):
    with open(os.path.join(HERE, p), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# 사람이 보고 뺀 장면: 자막 말풍선·그래픽 카드·상품 클로즈업
SKIP = {"JP/ujL37T-YCHI_00186.jpg", "JP/ZoBYb-ScMxI_00089.jpg", "JP/ZoBYb-ScMxI_00088.jpg", "VN/32fy4enT1Cs_00015.jpg"}


def pick_frames():
    det = rows("data/탐지결과.csv")
    by = defaultdict(list)
    meta = {}
    for r in det:
        meta[r["file"]] = (r["country"], r["video"], r["scene"], int(r["W"]), int(r["H"]))
        if r["cls"] in SHOW:
            by[r["file"]].append(r)
    out = {}
    for cc in CC:
        cand = []
        for f, (c, v, sc, w, h) in meta.items():
            if c != cc or sc == "out" or f in SKIP:
                continue
            bs = by.get(f, [])
            # 얼굴 클로즈업(사람 박스가 화면의 20% 이상)은 시연 화면에서 뺀다
            if any(b["cls"] == "person" and (float(b["x2"]) - float(b["x1"])) * (float(b["y2"]) - float(b["y1"])) > 0.2 * w * h for b in bs):
                continue
            seats = sum(1 for b in bs if KIND[b["cls"]] == "s")
            ppl = sum(1 for b in bs if b["cls"] == "person")
            cand.append((3 * min(seats, 3) + min(ppl, 3), v, f))
        cand.sort(reverse=True)
        chosen, used = [], defaultdict(int)
        for s, v, f in cand:
            if used[v] >= 2:
                continue
            chosen.append(f)
            used[v] += 1
            if len(chosen) == 6:
                break
        imgs = []
        for f in chosen:
            c, v, sc, w, h = meta[f]
            im = Image.open(os.path.join(HERE, "data", "frames", f)).convert("RGB").resize((480, 270))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=78)
            boxes = [{"k": KIND[b["cls"]], "t": SHOW[b["cls"]],
                      "x": float(b["x1"]) / w, "y": float(b["y1"]) / h,
                      "w": (float(b["x2"]) - float(b["x1"])) / w, "h": (float(b["y2"]) - float(b["y1"])) / h}
                     for b in by.get(f, [])]
            imgs.append({"src": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), "boxes": boxes})
        out[cc] = imgs
    return out


def main():
    summ = {r["country"]: r for r in rows("output/지표_요약.csv")}
    vids = rows("output/지표_영상별.csv")
    key = {"좌석": "seat", "착석": "sit", "무리": "group", "오토바이·자전거": "ride"}
    data = {
        "ind": IND,
        "summ": {c: {k: float(summ[c][k]) for k in IND} for c in CC},
        "n": {c: [int(summ[c]["영상 수"]), int(summ[c]["장면 수"])] for c in CC},
        "vid": {c: {k: [float(v[key[k]]) for v in vids if v["country"] == c] for k in IND} for c in CC},
        "frames": pick_frames(),
    }
    html = TEMPLATE.replace("/*__DATA__*/", "const DATA = " + json.dumps(data, ensure_ascii=False) + ";")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("[저장]", OUT, "{:.2f} MB".format(len(html.encode()) / 1e6))


TEMPLATE = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>한눈 프로토타입</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.min.css">
<style>
/* TDS(토스 디자인 시스템) 느낌: Pretendard · 토스 블루 · 그레이 스케일 · 큰 라운드 카드 · 토스트 */
:root{--ink:#191F28;--g800:#333D4B;--sub:#4E5968;--g600:#6B7684;--mute:#8B95A1;--line:#E5E8EB;--bg:#F2F4F6;--g50:#F9FAFB;--card:#fff;
--acc:#3182F6;--accs:#E8F3FF;--KR:#3182F6;--JP:#F04452;--VN:#03B26C;--KRs:#E8F3FF;--JPs:#FFEEEE;--VNs:#E5F8EF;
--p:#FE9800;--s:#3182F6;--f:#03B26C;--r:#A234C7}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);
font-family:Pretendard,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;-webkit-font-smoothing:antialiased;letter-spacing:-.2px}
header{display:flex;align-items:center;gap:12px;padding:14px 28px;background:#fff}
.logo{font-weight:800;font-size:24px;letter-spacing:-.8px;color:var(--acc)}
.proj{font-size:15px;color:var(--g600);font-weight:500}.team{margin-left:auto;display:flex;gap:6px}
.chip{font-size:13px;padding:6px 12px;border-radius:99px;font-weight:700}
nav{display:flex;gap:4px;padding:0 20px;background:#fff;border-bottom:1px solid var(--line);overflow-x:auto}
nav button{border:0;background:none;color:var(--mute);padding:14px 12px 12px;font:inherit;font-size:16px;font-weight:700;cursor:pointer;
white-space:nowrap;border-bottom:3px solid transparent;transition:.2s}
nav button.on{color:var(--ink);border-bottom-color:var(--ink)}
main{padding:24px 28px 100px;max-width:1280px;margin:0 auto}
.step{display:none}.step.on{display:block;animation:fade .45s cubic-bezier(.2,.8,.2,1)}
@keyframes fade{from{opacity:0;transform:translateY(10px)}to{opacity:1}}
h2{margin:0 0 6px;font-size:26px;font-weight:800;letter-spacing:-.6px}.lead{margin:0 0 20px;color:var(--g600);font-size:16px}
.cols{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.col{background:var(--card);border-radius:20px;padding:16px}
.colh{display:flex;align-items:center;gap:8px;margin-bottom:12px;font-weight:700}
.who{font-size:13px;color:var(--mute);font-weight:500;margin-left:auto}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.ph{position:relative;border-radius:12px;overflow:hidden;background:var(--bg);aspect-ratio:16/9;opacity:0;transform:scale(.97);transition:.4s cubic-bezier(.2,.8,.2,1)}
.ph.in{opacity:1;transform:none}.ph img{width:100%;height:100%;object-fit:cover;display:block}
.bx{position:absolute;border:2px solid;border-radius:4px;opacity:0;transition:opacity .25s}
.bx.in{opacity:1}.bx span{position:absolute;left:-2px;top:-16px;font-size:10px;line-height:14px;padding:0 4px;color:#fff;font-weight:700;white-space:nowrap;border-radius:4px}
.bx.p{border-color:var(--p)}.bx.p span{background:var(--p)}.bx.s{border-color:var(--s)}.bx.s span{background:var(--s)}
.bx.f{border-color:var(--f)}.bx.f span{background:var(--f)}.bx.r{border-color:var(--r)}.bx.r span{background:var(--r)}
.topic{display:flex;gap:10px;align-items:center;background:#fff;border-radius:20px;padding:14px 16px;margin-bottom:16px}
.topic input{flex:1;border:0;background:var(--bg);border-radius:12px;padding:14px 16px;font:inherit;font-size:16px;font-weight:600;color:var(--ink)}
.tag{font-size:13px;font-weight:700;color:var(--acc);background:var(--accs);padding:7px 12px;border-radius:99px;white-space:nowrap}
.bar{height:6px;background:var(--bg);border-radius:99px;overflow:hidden;margin:10px 0 4px}.bar i{display:block;height:100%;width:0;background:var(--acc);transition:width .35s;border-radius:99px}
.stat{font-size:13px;color:var(--mute);font-weight:500}
.legend{display:flex;gap:14px;font-size:13px;color:var(--g600);margin:14px 0 0}.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.two{display:grid;grid-template-columns:1fr 1.25fr;gap:16px}
.panel{background:#fff;border-radius:20px;padding:20px}
.kpis{display:grid;gap:14px}.kpi{display:grid;grid-template-columns:120px 1fr;align-items:center;gap:10px;font-size:15px;padding:6px;border-radius:14px}
.kbars{display:grid;gap:5px}.kb{display:flex;align-items:center;gap:8px}.kb b{height:12px;border-radius:99px;transition:width .6s}.kb em{font-style:normal;font-size:13px;color:var(--g600);font-weight:600}
.warn{margin-top:16px;background:#FFF4E6;border-radius:16px;padding:14px 16px;font-size:15px;color:var(--g800);line-height:1.5}
.hot{box-shadow:0 0 0 3px var(--acc);border-radius:16px}
.card3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
.c{border-radius:20px;padding:20px;min-height:210px;background:#fff}.c h3{margin:0 0 12px;font-size:18px;font-weight:800}
.c textarea{width:100%;height:100px;border:0;border-radius:14px;padding:14px;font:inherit;font-size:15px;resize:none;background:var(--bg);color:var(--ink);line-height:1.5}
.by{font-size:13px;color:var(--mute);margin-top:8px;font-weight:500}
.btn{border:0;background:var(--acc);color:#fff;font:inherit;font-weight:700;padding:14px 20px;border-radius:14px;cursor:pointer}
.slides{display:grid;grid-template-columns:1fr 1.6fr;gap:16px;align-items:start}
.toc{background:#fff;border-radius:20px;padding:16px;font-size:15px;font-weight:600}
.toc div{padding:12px 14px;border-radius:12px;margin-bottom:8px;background:var(--bg);transition:.4s}
.toc .old{text-decoration:line-through;color:var(--mute)}.toc .new{background:var(--accs);color:var(--acc);font-weight:800}
.slide{background:#fff;border-radius:20px;padding:24px;aspect-ratio:16/9;box-shadow:0 8px 24px rgba(0,27,55,.08);display:flex;flex-direction:column}
.slide h4{margin:0 0 6px;font-size:22px;font-weight:800}.slide .sub{color:var(--g600);font-size:14px;margin-bottom:14px}
.srow{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;flex:1}
.scell{border-radius:16px;padding:14px;font-size:14px;font-weight:600;color:var(--sub)}.scell b{display:block;font-size:32px;font-weight:800;margin:4px 0}
.quote{margin-top:12px;background:var(--VNs);padding:12px 16px;font-size:15px;border-radius:14px;font-weight:600;color:var(--g800)}
#cap{position:fixed;left:50%;bottom:28px;transform:translateX(-50%) translateY(10px);max-width:900px;width:calc(100% - 56px);
background:rgba(25,31,40,.94);color:#fff;font-size:20px;font-weight:600;line-height:1.5;padding:16px 24px;border-radius:18px;text-align:center;
opacity:0;transition:.3s;z-index:9;pointer-events:none}
#cap.on{opacity:1;transform:translateX(-50%)}
.note{font-size:13px;color:var(--mute);margin-top:12px}
@media (max-width:760px){.cols,.two,.card3,.slides{grid-template-columns:1fr}.team{display:none}}
</style></head><body>
<header><div class="logo">한눈</div><div class="proj">팀 과제 · 대학가 편의점은 어떤 공간인가?</div>
<div class="team"><span class="chip" style="background:var(--KRs);color:var(--KR)">민수·지은 · 한국</span><span class="chip" style="background:var(--JPs);color:var(--JP)">유카 · 일본</span><span class="chip" style="background:var(--VNs);color:var(--VN)">린 · 베트남</span></div></header>
<nav id="nav"></nav>
<main>
<section class="step" id="s1"><h2>① 조사 — 나라별 팀원이 자기 나라 현장을 모읍니다</h2>
<p class="lead">글을 번역하는 대신, 번역이 필요 없는 사진·영상을 모읍니다. 외국인 팀원은 모국어 검색어와 현지 인맥으로 자료를 찾습니다.</p>
<div class="topic"><span class="tag">비교 질문</span><input id="q" value=""><span class="tag">공통 기준 5개</span></div>
<div class="cols" id="up"></div></section>

<section class="step" id="s2"><h2>② AI 측정 — 같은 AI가 같은 기준으로 셉니다</h2>
<p class="lead">YOLO가 팀원이 올린 사진에서 사람·의자·테이블·오토바이를 찾고, 규칙에 따라 생활 지표로 바꿉니다. 어느 나라 사진이든 기준은 하나입니다.</p>
<div class="cols" id="det"></div>
<div class="legend"><span><i style="background:var(--p)"></i>사람</span><span><i style="background:var(--s)"></i>좌석(의자·테이블)</span><span><i style="background:var(--r)"></i>오토바이·자전거</span></div></section>

<section class="step" id="s3"><h2>③ 비교 — 같은 차트 위에 세 나라</h2>
<p class="lead">해당 요소가 보인 장면의 비율(%). 영상 하나하나를 점으로 함께 봅니다.</p>
<div class="two"><div class="panel"><svg id="radar" viewBox="0 0 360 330" width="100%"></svg></div>
<div class="panel"><div class="kpis" id="kpis"></div><div class="warn" id="warn">💡 <b>베트남의 '앉은 사람'은 7편 중 2편에서 나왔습니다.</b> 나라 차이로 단정하기 전에 현지 팀원에게 물어보세요 → <b>해석 카드 만들기</b></div></div></div></section>

<section class="step" id="s4"><h2>④ 해석 카드 — 측정은 AI, 해석은 현지 팀원</h2>
<p class="lead">AI는 '무엇이 얼마나 보였는가'만 말합니다. '왜'는 그 나라 출신 팀원이 채웁니다.</p>
<div class="card3"><div class="c" style="background:#fff"><h3>📊 AI 측정</h3><div id="m"></div></div>
<div class="c" style="background:var(--VNs)"><h3>🗣 현지인 해석</h3><textarea id="t1" placeholder="왜 그럴까요?"></textarea><div class="by">작성: 린 · 베트남</div></div>
<div class="c" style="background:var(--accs)"><h3>💡 우리 과제의 주장</h3><textarea id="t2" placeholder="우리 과제에 어떻게 쓸까요?"></textarea><div class="by">작성: 팀 전체</div></div></div>
<p class="note">해석 문장은 시연용 예시입니다.</p></section>

<section class="step" id="s5"><h2>⑤ 발표로 보내기 — '해외 사례' 부록이 본론이 됩니다</h2>
<p class="lead">해석 카드가 본론 슬라이드로 들어갑니다. 외국 자료는 더 이상 따로 떨어진 한 장이 아닙니다.</p>
<div class="slides"><div class="toc" id="toc"><div>1. 서론</div><div>2. 한국 편의점 현황</div><div class="o">4. 해외 사례 (베트남)</div><div>5. 개선 전략</div></div>
<div class="slide" id="slide"><h4>본론 2. 누가, 어떻게 머무는가</h4><div class="sub">같은 AI · 같은 기준으로 잰 세 나라 편의점 (앉은 사람이 보인 장면의 비율)</div>
<div class="srow" id="srow"></div><div class="quote" id="sq"></div></div></div></section>
</main>
<div id="cap"></div>
<script>
/*__DATA__*/
const CC=["KR","JP","VN"],NM={KR:"한국",JP:"일본",VN:"베트남"},WHO={KR:"민수·지은",JP:"유카",VN:"린"};
const STEPS=["① 조사","② AI 측정","③ 비교","④ 해석 카드","⑤ 발표로 보내기"];
const $=s=>document.querySelector(s),sleep=ms=>new Promise(r=>setTimeout(r,ms));
let cur=0;
const nav=$("#nav");STEPS.forEach((s,i)=>{const b=document.createElement("button");b.textContent=s;b.onclick=()=>go(i);nav.appendChild(b)});
function go(i){cur=i;document.querySelectorAll(".step").forEach((e,k)=>e.classList.toggle("on",k===i));
 nav.querySelectorAll("button").forEach((e,k)=>e.classList.toggle("on",k===i));
 if(i===0)fill1(false);if(i===1)fill2(false);if(i===2)fill3();if(i===3)fill4(false);if(i===4)fill5(false)}
function colHead(cc,extra){return `<div class="colh"><span class="chip" style="background:var(--${cc}s);color:var(--${cc})">${NM[cc]}</span>${extra||""}<span class="who">${WHO[cc]}</span></div>`}
function photo(f,boxes){const d=document.createElement("div");d.className="ph";d.innerHTML=`<img src="${f.src}">`;
 if(boxes)f.boxes.forEach(b=>{const e=document.createElement("div");e.className="bx "+b.k;e.style.cssText=`left:${b.x*100}%;top:${b.y*100}%;width:${b.w*100}%;height:${b.h*100}%`;e.innerHTML=`<span>${b.t}</span>`;d.appendChild(e)});return d}
async function fill1(anim){$("#q").value="대학가 편의점은 어떤 공간인가? — 한국·일본·베트남 비교";const up=$("#up");up.innerHTML="";
 const g={};CC.forEach(cc=>{const c=document.createElement("div");c.className="col";c.innerHTML=colHead(cc)+`<div class="grid"></div><div class="stat">영상 ${DATA.n[cc][0]}편 · 장면 ${DATA.n[cc][1]}장</div>`;up.appendChild(c);g[cc]=c.querySelector(".grid")});
 for(let k=0;k<6;k++)for(const cc of CC){const f=DATA.frames[cc][k];if(!f)continue;const p=photo(f,false);g[cc].appendChild(p);
  if(anim){await sleep(90)}requestAnimationFrame(()=>p.classList.add("in"))}}
async function fill2(anim){const det=$("#det");det.innerHTML="";const tasks=[];
 CC.forEach(cc=>{const c=document.createElement("div");c.className="col";c.innerHTML=colHead(cc,`<span class="stat" data-c="${cc}">측정 중…</span>`)+`<div class="grid"></div><div class="bar"><i></i></div>`;det.appendChild(c);
  const g=c.querySelector(".grid");DATA.frames[cc].slice(0,4).forEach(f=>{const p=photo(f,true);p.classList.add("in");g.appendChild(p);tasks.push([cc,p,c])})});
 const done={KR:0,JP:0,VN:0};
 for(const [cc,p,c] of tasks){const bs=[...p.querySelectorAll(".bx")];for(const b of bs){if(anim)await sleep(55);b.classList.add("in")}
  done[cc]++;c.querySelector(".bar i").style.width=(done[cc]/4*100)+"%";
  c.querySelector(`[data-c="${cc}"]`).textContent=done[cc]===4?`장면 ${DATA.n[cc][1]}장 측정 완료`:"측정 중…"}}
function fill3(){const R=$("#radar"),N=DATA.ind.length,cx=180,cy=165,rad=120,MAX=10;let s="";
 for(let k=1;k<=4;k++){let pts=[];for(let i=0;i<N;i++){const a=-Math.PI/2+i*2*Math.PI/N;pts.push([cx+rad*k/4*Math.cos(a),cy+rad*k/4*Math.sin(a)])}
  s+=`<polygon points="${pts.map(p=>p.join(",")).join(" ")}" fill="none" stroke="#E5E8EB"/>`;s+=`<text x="${cx+3}" y="${cy-rad*k/4-2}" font-size="9" fill="#8A8F94">${MAX*k/4}%</text>`}
 DATA.ind.forEach((n,i)=>{const a=-Math.PI/2+i*2*Math.PI/N;s+=`<line x1="${cx}" y1="${cy}" x2="${cx+rad*Math.cos(a)}" y2="${cy+rad*Math.sin(a)}" stroke="#E5E8EB"/>`;
  s+=`<text x="${cx+(rad+22)*Math.cos(a)}" y="${cy+(rad+18)*Math.sin(a)+4}" font-size="13" font-weight="700" text-anchor="middle" fill="#191F28">${n}</text>`});
 CC.forEach(cc=>{const col=getComputedStyle(document.body).getPropertyValue("--"+cc);const pts=DATA.ind.map((n,i)=>{const a=-Math.PI/2+i*2*Math.PI/N,v=Math.min(DATA.summ[cc][n],MAX)/MAX*rad;return [cx+v*Math.cos(a),cy+v*Math.sin(a)].join(",")});
  s+=`<polygon points="${pts.join(" ")}" fill="${col}" fill-opacity=".10" stroke="${col}" stroke-width="3" stroke-linejoin="round"/>`});
 CC.forEach((cc,i)=>{s+=`<rect x="${10+i*62}" y="8" width="10" height="10" rx="2" fill="var(--${cc})"/><text x="${24+i*62}" y="17" font-size="12">${NM[cc]}</text>`});R.innerHTML=s;
 const K=$("#kpis");K.innerHTML="";const MX=Math.max(...CC.flatMap(c=>DATA.ind.map(n=>DATA.summ[c][n])));
 DATA.ind.forEach(n=>{const d=document.createElement("div");d.className="kpi";d.dataset.n=n;
  d.innerHTML=`<b>${n}</b><div class="kbars">`+CC.map(cc=>{const v=DATA.summ[cc][n];const dots=DATA.vid[cc][n].map(x=>`<i title="${x}%" style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#fff;border:1.5px solid #6B7684;margin-left:2px"></i>`).join("");
   return `<div class="kb"><b style="width:${Math.max(2,v/MX*200)}px;background:var(--${cc})"></b><em>${NM[cc]} ${v.toFixed(1)}%</em>${dots}</div>`}).join("")+`</div>`;K.appendChild(d)})}
function fill4(anim){const v=DATA.summ;$("#m").innerHTML=`<div style="font-size:14px">앉은 사람이 보인 장면</div>`+CC.map(cc=>`<div style="font-size:22px;font-weight:800;color:var(--${cc})">${NM[cc]} ${v[cc]["착석"].toFixed(1)}%</div>`).join("")+`<div class="by">베트남 7편 중 2편에 집중 · 자동 입력</div>`;
 if(!anim){$("#t1").value="좌석이 있는 매장은 학생들이 공부하고 친구를 만나는 곳이에요. 에어컨이 있어서 더울 때 오래 머물러요.";$("#t2").value="대학가 편의점을 '머무는 공간'으로 — 창가 좌석과 콘센트를 둔 매장 실험"}}
async function typeIn(el,t){el.value="";for(const ch of t){el.value+=ch;await sleep(38)}}
function fill5(anim){const r=$("#srow");r.innerHTML=CC.map(cc=>`<div class="scell" style="background:var(--${cc}s)">${NM[cc]}<b style="color:var(--${cc})">${DATA.summ[cc]["착석"].toFixed(1)}%</b>좌석 ${DATA.summ[cc]["좌석"].toFixed(1)}% · 무리 ${DATA.summ[cc]["무리"].toFixed(1)}%</div>`).join("");
 $("#sq").innerHTML=`🗣 "${$("#t1").value||"좌석이 있는 매장은 학생들이 공부하고 친구를 만나는 곳이에요."}" — 린 · 베트남`;
 const t=$("#toc");if(!anim){t.innerHTML=`<div>1. 서론</div><div class="new">2. 누가, 어떻게 머무는가 (한·일·베)</div><div class="old">4. 해외 사례 (베트남)</div><div>5. 개선 전략</div>`}}
async function cap(t,ms){const c=$("#cap");c.textContent=t;c.classList.add("on");await sleep(ms)}
async function demo(){
 go(0);await cap("유학생이 있는 팀플, 외국인 팀원의 조사는 늘 '해외 사례' 한 장이 됩니다.",3800);
 await cap("「한눈」은 글 대신, 번역이 필요 없는 현장 사진을 모읍니다.",1500);fill1(true);await sleep(2600);
 await cap("한국 팀원은 한국 편의점을, 베트남 팀원 린은 베트남 편의점을 — 각자 자기 나라 현장을 맡습니다.",3600);
 go(1);$("#det").innerHTML="";await cap("같은 AI가 모든 사진에서 사람·의자·테이블을 찾아 셉니다.",800);fill2(true);await sleep(3400);
 await cap("어느 나라 사진이든 기준은 하나. 파일럿에서 영상 21편, 장면 796장을 쟀습니다.",3400);
 go(2);await cap("세 나라가 같은 차트 위에 섭니다. '머무는 장면'은 베트남에서 가장 자주 보였습니다.",4200);
 document.querySelector('[data-n="착석"]').classList.add("hot");await cap("하지만 점을 보면, 베트남 7편 중 2편에서 나온 값입니다.",3600);
 $("#warn").classList.add("hot");await cap("그래서 한눈은 결론 대신 질문을 줍니다 — 이 매장들은 왜 달랐을까?",3800);
 go(3);$("#t1").value="";$("#t2").value="";await cap("AI는 '무엇이 얼마나'만 말합니다. '왜'는 베트남 팀원 린이 답합니다.",1200);
 await typeIn($("#t1"),"좌석이 있는 매장은 학생들이 공부하고 친구를 만나는 곳이에요. 에어컨이 있어서 더울 때 오래 머물러요.");
 await cap("그 해석이 우리 팀의 주장이 됩니다.",600);await typeIn($("#t2"),"대학가 편의점을 '머무는 공간'으로 — 창가 좌석과 콘센트를 둔 매장 실험");await sleep(900);
 go(4);const t=$("#toc");t.innerHTML=`<div>1. 서론</div><div>2. 한국 편의점 현황</div><div class="o">4. 해외 사례 (베트남)</div><div>5. 개선 전략</div>`;
 await cap("원래라면 발표 목차에서 '해외 사례' 한 장으로 떨어져 나갈 자료가,",3000);
 t.innerHTML=`<div>1. 서론</div><div class="new">2. 누가, 어떻게 머무는가 (한·일·베)</div><div class="old">4. 해외 사례 (베트남)</div><div>5. 개선 전략</div>`;
 $("#slide").classList.add("hot");await cap("본론의 근거가 됩니다. 측정은 AI가, 어울림은 사람이 — 한눈.",4800);
 $("#cap").classList.remove("on");document.body.dataset.done="1"}
go(0);if(new URLSearchParams(location.search).get("demo")==="1"){demo()}
const sp=new URLSearchParams(location.search).get("step");if(sp)go(+sp);
</script></body></html>
"""

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
