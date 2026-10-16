#!/usr/bin/env python3
"""헤어 뉴스 수집: Google News RSS -> data/YYYY-MM-DD.json, data/index.json (표준 라이브러리만 사용)"""
import json, re, sys, html, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

KST = timezone(timedelta(hours=9))
DATA = Path(__file__).resolve().parent.parent / "data"
PER_CAT = 10         # 카테고리당 최대 건수 (4개 x 10 = 최대 40건)
KEEP_DAYS = 90       # 보관 일수

CATEGORIES = [
    {"id": "kr-news",  "name": "국내 헤어 뉴스",       "lang": "ko", "queries": ["미용실", "헤어", "미용사", "헤어디자이너", "미용실 창업", "미용업 뉴스", "헤어샵", "탈모 헤어"]},
    {"id": "global",   "name": "해외 헤어 뉴스",       "lang": "en", "queries": ["hair salon", "hairstylist", "hair industry", "haircare", "hair loss", "salon business"]},
    {"id": "trend",    "name": "트렌드·스타일",        "lang": "ko", "queries": ["헤어스타일 트렌드", "헤어 컬러", "헤어 펌 유행", "미용실 인기 스타일", "헤어 연예인", "hairstyle trend", "hair color trend"]},
    {"id": "product",  "name": "헤어 제품·브랜드 소식", "lang": "ko", "queries": ["헤어 신제품", "헤어케어 출시", "헤어 브랜드", "헤어 에센스", "헤어 샴푸 출시", "미용실 전용 제품", "hair care launch"]},
]
# 영어 카테고리/쿼리는 영어 설정으로 조회
def feed_url(q, lang):
    if lang == "en" or re.search(r"[A-Za-z]{4,}", q) and not re.search(r"[가-힣]", q):
        hl, gl, ceid = "en-US", "US", "US:en"
    else:
        hl, gl, ceid = "ko", "KR", "KR:ko"
    return ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:1d")
            + f"&hl={hl}&gl={gl}&ceid={ceid}")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 hair-news-bot"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def clean(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", t or ""))).strip()

def parse(xml_bytes):
    out = []
    for it in ET.fromstring(xml_bytes).iter("item"):
        title = clean(it.findtext("title"))
        src_el = it.find("source")
        source = clean(src_el.text) if src_el is not None else ""
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3]
        try:
            dt = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
        except Exception:
            dt = datetime.now(KST)
        out.append({"title": title, "source": source, "url": it.findtext("link"),
                    "published": dt.isoformat(timespec="minutes")})
    return out

HAIR = re.compile(r"미용실|헤어|미용사|hair|salon|stylist|barber", re.I)  # 필수 키워드: 제목에 하나 이상 포함

def norm(t):
    return re.sub(r"[^0-9a-z가-힣]", "", t.lower())[:30]

def main():
    now = datetime.now(KST)
    seen_titles, seen_urls, cats = set(), set(), []
    for c in CATEGORIES:
        items = []
        for q in c["queries"]:
            try:
                items += parse(fetch(feed_url(q, c["lang"])))
            except Exception as e:
                print(f"[경고] '{q}' 수집 실패: {e}", file=sys.stderr)
        items.sort(key=lambda x: x["published"], reverse=True)
        picked = []
        for it in items:
            if not HAIR.search(it["title"]):
                continue
            k = norm(it["title"])
            if k in seen_titles or it["url"] in seen_urls:
                continue
            seen_titles.add(k); seen_urls.add(it["url"]); picked.append(it)
            if len(picked) >= PER_CAT: break
        cats.append({"id": c["id"], "name": c["name"], "items": picked})
    total = sum(len(c["items"]) for c in cats)
    if total == 0:
        print("수집된 기사가 없어 파일을 갱신하지 않습니다.", file=sys.stderr); sys.exit(1)
    DATA.mkdir(exist_ok=True)
    day = now.strftime("%Y-%m-%d")
    (DATA / f"{day}.json").write_text(json.dumps(
        {"date": day, "updated": now.isoformat(timespec="minutes"), "total": total, "categories": cats},
        ensure_ascii=False, indent=1), encoding="utf-8")
    cutoff = (now - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    days = sorted([p.stem for p in DATA.glob("20??-??-??.json")], reverse=True)
    for d in days:
        if d < cutoff: (DATA / f"{d}.json").unlink()
    days = [d for d in days if d >= cutoff]
    (DATA / "index.json").write_text(json.dumps({"dates": days}, ensure_ascii=False), encoding="utf-8")
    # 파일을 직접 열어도 보이도록 전체 데이터를 하나의 JS 파일로도 저장
    bundle = {d: json.loads((DATA / f"{d}.json").read_text(encoding="utf-8")) for d in days}
    (DATA / "bundle.js").write_text("window.HAIR_BUNDLE=" + json.dumps({"dates": days, "days": bundle}, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{day}: {total}건 저장")

if __name__ == "__main__":
    main()
