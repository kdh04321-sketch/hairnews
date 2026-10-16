# 매일 헤어 뉴스 (초안)

매일 오전 7시(한국시간)에 헤어 뉴스를 모아 보여 주는 정적 웹사이트입니다.

## 구성
- `index.html` : 화면 (날짜 선택, 카테고리, 검색)
- `scripts/update_news.py` : 뉴스 수집 (Google 뉴스 RSS, 별도 설치 없음)
- `data/` : 날짜별 결과 (`YYYY-MM-DD.json`, `index.json`), 90일 보관
- `.github/workflows/daily-update.yml` : 매일 07:00 KST 자동 실행

## 공개하는 법 (GitHub Pages, 무료)
1. GitHub에서 새 저장소를 만들고 이 폴더 내용을 올립니다.
2. Settings > Pages > Branch: `main` / root 선택 → 주소가 생깁니다.
3. Actions 탭에서 "헤어 뉴스 일일 갱신"을 한 번 수동 실행해 확인합니다.

## 내 컴퓨터에서 미리보기
```
cd hair-news && python3 -m http.server 8000
```
브라우저에서 http://localhost:8000 을 엽니다.

## 조정하기
- 검색어·카테고리: `scripts/update_news.py` 위쪽 `CATEGORIES`
- 건수: `PER_CAT` (카테고리당 10건 x 4개 = 하루 최대 40건)
