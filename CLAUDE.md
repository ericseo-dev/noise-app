# 프로젝트 개요
공공데이터csv를 표.그래프.자도로 보여주는 streamlit 웹앱. 기획서는 PLAN.md 참고

## 파일 구조
- noise_app.py : 메인 (UI + 로직)
- ai_helper.py : ask_ai() 함수 정의
- 전국소음진동배출시설표준데이터.csv : 공공데이터 파일
- .env : ANTHROPIC_API_KEY 보관

## 규칙
- 기능을 만들기 전에 PLAN.md를 먼저 확인한다
- 모델은 claude-haiku 사용
- API 호출은 ai_helper.py에서 ask_ai 함수 를 불러 쓴다
- API Key 는 .env에서 읽고 코드에 직접 쓰지 않는다
- 전국소음진동배출시설표준데이터.csv를 UTF-8로 먼저, 안되면 cp949로 읽는다